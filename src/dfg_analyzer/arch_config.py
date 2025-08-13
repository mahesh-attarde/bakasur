"""
Architecture Configuration Loader

Loads architecture-specific data from JSON configuration files.
This allows the dataflow tool to support multiple architectures.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass


@dataclass
class ArchitectureConfig:
    """Architecture configuration data structure"""
    
    architecture: str
    description: str
    syntax: str
    
    # Register data
    all_registers: Set[str]
    register_categories: Dict[str, List[str]]
    register_aliases: Dict[str, Set[str]]
    
    # Instruction categories  
    read_write_instructions: Set[str]
    read_only_instructions: Set[str]
    jump_instructions: Set[str]
    read_modify_write_instructions: Set[str]
    mask_instructions: Set[str]
    
    # Special instructions
    special_instructions: Dict[str, Dict[str, str]]
    
    # Memory syntax patterns
    memory_patterns: Dict[str, str]


class ArchitectureLoader:
    """Loads and manages architecture configurations"""
    
    def __init__(self):
        self.configs_dir = Path(__file__).parent / "architectures"
        self._loaded_configs: Dict[str, ArchitectureConfig] = {}
    
    def get_available_architectures(self) -> List[str]:
        """Get list of available architecture configurations"""
        if not self.configs_dir.exists():
            return []
        
        architectures = []
        for file_path in self.configs_dir.glob("*.json"):
            arch_name = file_path.stem
            architectures.append(arch_name)
        
        return sorted(architectures)
    
    def load_architecture(self, architecture: str) -> ArchitectureConfig:
        """Load architecture configuration from JSON file"""
        
        # Return cached config if already loaded
        if architecture in self._loaded_configs:
            return self._loaded_configs[architecture]
        
        config_file = self.configs_dir / f"{architecture}.json"
        
        if not config_file.exists():
            available = self.get_available_architectures()
            raise ValueError(f"Architecture '{architecture}' not found. Available: {available}")
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            config = self._parse_config(data)
            self._loaded_configs[architecture] = config
            
            return config
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid configuration file for {architecture}: {e}")
    
    def _parse_config(self, data: Dict[str, Any]) -> ArchitectureConfig:
        """Parse JSON data into ArchitectureConfig object"""
        
        # Extract basic info
        architecture = data["architecture"]
        description = data["description"]
        syntax = data["syntax"]
        
        # Process registers
        register_categories = data["registers"]
        all_registers = set()
        for category, regs in register_categories.items():
            all_registers.update(regs)
        
        # Process register aliases
        register_aliases = {}
        for base_reg, aliases in data["register_aliases"].items():
            register_aliases[base_reg] = set(aliases)
        
        # Process instruction categories
        inst_categories = data["instruction_categories"]
        read_write_instructions = set(inst_categories.get("read_write", []))
        read_only_instructions = set(inst_categories.get("read_only", []))
        jump_instructions = set(inst_categories.get("jump", []))
        read_modify_write_instructions = set(inst_categories.get("read_modify_write", []))
        mask_instructions = set(inst_categories.get("mask_instructions", []))
        
        # Process special instructions
        special_instructions = data.get("special_instructions", {})
        
        # Process memory syntax patterns
        memory_patterns = data["memory_syntax"]["patterns"]
        
        # Create register pattern for this architecture
        register_names = "|".join(sorted(all_registers, key=len, reverse=True))
        memory_patterns["register"] = memory_patterns["register"].format(
            register_names=register_names
        )
        
        return ArchitectureConfig(
            architecture=architecture,
            description=description,
            syntax=syntax,
            all_registers=all_registers,
            register_categories=register_categories,
            register_aliases=register_aliases,
            read_write_instructions=read_write_instructions,
            read_only_instructions=read_only_instructions,
            jump_instructions=jump_instructions,
            read_modify_write_instructions=read_modify_write_instructions,
            mask_instructions=mask_instructions,
            special_instructions=special_instructions,
            memory_patterns=memory_patterns
        )
    
    def detect_architecture(self, assembly_text: str) -> Optional[str]:
        """
        Attempt to detect architecture from assembly code
        
        Returns:
            Architecture name if detected, None otherwise
        """
        assembly_lower = assembly_text.lower()
        
        # Simple heuristics for architecture detection
        x86_indicators = [
            'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi',
            'eax', 'ebx', 'ecx', 'edx',
            'xmm', 'ymm', 'zmm',
            'mov ', 'jmp', 'call'
        ]
        
        arm_indicators = [
            'x0', 'x1', 'x2', 'x3', 'w0', 'w1', 'w2', 'w3',
            'v0', 'v1', 'v2', 'v3',
            'ldr', 'str', 'ldp', 'stp',
            'b.', 'bl ', 'cbz', 'cbnz'
        ]
        
        riscv_indicators = [
            'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
            't0', 't1', 't2', 't3', 't4', 't5', 't6',
            's0', 's1', 's2', 's3', 'sp', 'ra', 'gp', 'tp',
            'li ', 'addi', 'ble', 'bge', 'beq', 'bne',
            'jal', 'jalr', 'ret'
        ]
        
        x86_score = sum(1 for indicator in x86_indicators if indicator in assembly_lower)
        arm_score = sum(1 for indicator in arm_indicators if indicator in assembly_lower)
        riscv_score = sum(1 for indicator in riscv_indicators if indicator in assembly_lower)
        
        # Return the architecture with highest score
        scores = [
            (x86_score, "x86_64"),
            (arm_score, "aarch64"),
            (riscv_score, "riscv64")
        ]
        
        max_score, best_arch = max(scores)
        
        if max_score > 0:
            return best_arch
        
        # Default to x86_64 if nothing detected
        return "x86_64"


# Global instance for easy access
_arch_loader = ArchitectureLoader()

def get_architecture_loader() -> ArchitectureLoader:
    """Get the global architecture loader instance"""
    return _arch_loader

def load_architecture(architecture: str) -> ArchitectureConfig:
    """Convenience function to load an architecture configuration"""
    return _arch_loader.load_architecture(architecture)

def get_available_architectures() -> List[str]:
    """Convenience function to get available architectures"""
    return _arch_loader.get_available_architectures()

def detect_architecture(assembly_text: str) -> Optional[str]:
    """Convenience function to detect architecture from assembly code"""
    return _arch_loader.detect_architecture(assembly_text)
