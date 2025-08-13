"""
Generic Assembly Parser

A configurable parser that can work with different architectures
by using architecture-specific configuration files.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from .models import Instruction
from .arch_config import ArchitectureConfig, load_architecture, detect_architecture


class GenericAssemblyParser:
    """Generic parser that works with multiple architectures via configuration"""
    
    def __init__(self, architecture: str = None):
        """
        Initialize parser for specific architecture
        
        Args:
            architecture: Architecture name (e.g., 'x86_64', 'aarch64')
                         If None, will auto-detect from first parsed instruction
        """
        self.architecture_name = architecture
        self.config: Optional[ArchitectureConfig] = None
        self._auto_detect = architecture is None
        
        if architecture:
            self.config = load_architecture(architecture)
    
    def _ensure_config(self, assembly_text: str = ""):
        """Ensure configuration is loaded, auto-detecting if necessary"""
        if self.config is None:
            if self._auto_detect:
                detected_arch = detect_architecture(assembly_text)
                if detected_arch:
                    self.architecture_name = detected_arch
                    self.config = load_architecture(detected_arch)
                else:
                    # Default fallback
                    self.architecture_name = "x86_64"
                    self.config = load_architecture("x86_64")
            else:
                raise ValueError("No architecture configuration loaded")
    
    def normalize_register(self, reg: str) -> str:
        """Normalize register name to its base form"""
        self._ensure_config()
        
        reg = reg.lower()
        
        # Find the base register for this alias
        for base_reg, aliases in self.config.register_aliases.items():
            if reg in aliases:
                return base_reg
        
        # If not found in aliases, return as-is
        return reg
    
    def parse_operand(self, operand: str) -> Tuple[Set[str], Set[str], Optional[str]]:
        """
        Parse an operand and return (reads, writes, memory_location)
        
        Returns:
            reads: Set of registers read
            writes: Set of registers written
            memory_location: Memory location if applicable
        """
        self._ensure_config()
        
        operand = operand.strip()
        reads = set()
        writes = set()
        memory_location = None
        
        # Handle memory operands using architecture-specific pattern
        memory_pattern = self.config.memory_patterns["memory_operand"]
        memory_match = re.search(memory_pattern, operand)
        
        if memory_match:
            memory_expr = memory_match.group(1)
            memory_location = f"[{memory_expr}]"
            
            # Extract registers from memory expression
            reg_pattern = self.config.memory_patterns["register"]
            reg_matches = re.findall(reg_pattern, memory_expr, re.IGNORECASE)
            
            for reg in reg_matches:
                reads.add(self.normalize_register(reg))
            
            # Handle architecture-specific mask operands (x86_64 AVX-512)
            if "mask_register" in self.config.memory_patterns:
                mask_pattern = self.config.memory_patterns["mask_register"]
                mask_matches = re.findall(mask_pattern, operand, re.IGNORECASE)
                for mask in mask_matches:
                    reads.add(self.normalize_register(mask))
        
        # Handle direct register operands
        else:
            # Handle architecture-specific mask operands (x86_64 AVX-512)
            if "mask_register" in self.config.memory_patterns:
                mask_pattern = self.config.memory_patterns["mask_register"]
                mask_matches = re.findall(mask_pattern, operand, re.IGNORECASE)
                for mask in mask_matches:
                    reads.add(self.normalize_register(mask))
            
            # Handle regular register operands
            reg_pattern = self.config.memory_patterns["register"]
            reg_matches = re.findall(reg_pattern, operand, re.IGNORECASE)
            
            for reg in reg_matches:
                reads.add(self.normalize_register(reg))
        
        return reads, writes, memory_location
    
    def parse_instruction(self, line: str, line_num: int) -> Optional[Instruction]:
        """Parse a single assembly instruction line"""
        self._ensure_config(line)
        
        line = line.strip()
        if not line or line.startswith('#') or line.startswith(';'):
            return None
        
        # Check for label
        label = None
        if ':' in line and not line.startswith('\t') and not line.startswith(' '):
            parts = line.split(':', 1)
            if len(parts) == 2:
                label = parts[0].strip()
                line = parts[1].strip()
                if not line:  # Label-only line
                    return Instruction(line_num, label, '', [], line)
        
        # Parse instruction
        parts = line.split(None, 1)
        if not parts:
            return None
        
        opcode = parts[0].lower()
        operands = []
        
        if len(parts) > 1:
            # Split operands by comma, but handle nested brackets
            operand_str = parts[1]
            operands = self._split_operands(operand_str)
        
        return Instruction(line_num, label, opcode, operands, line)
    
    def _split_operands(self, operand_str: str) -> List[str]:
        """Split operands by comma, handling nested brackets"""
        operands = []
        current = ""
        bracket_depth = 0
        
        for char in operand_str:
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ',' and bracket_depth == 0:
                operands.append(current.strip())
                current = ""
                continue
            
            current += char
        
        if current.strip():
            operands.append(current.strip())
        
        return operands
    
    def get_architecture_info(self) -> Dict[str, str]:
        """Get information about the current architecture configuration"""
        self._ensure_config()
        
        return {
            "architecture": self.config.architecture,
            "description": self.config.description,
            "syntax": self.config.syntax,
            "total_registers": str(len(self.config.all_registers)),
            "instruction_categories": str(len(self.config.read_write_instructions) + 
                                         len(self.config.read_only_instructions) + 
                                         len(self.config.jump_instructions))
        }


# For backward compatibility with existing code
class IntelAssemblyParser(GenericAssemblyParser):
    """Intel x86_64 assembly parser (backward compatibility)"""
    
    def __init__(self):
        super().__init__("x86_64")


# Additional convenience parsers for specific architectures
class ARM64AssemblyParser(GenericAssemblyParser):
    """ARM64/AArch64 assembly parser"""
    
    def __init__(self):
        super().__init__("aarch64")
