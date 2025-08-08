"""
Object Dump Parser

Parser for objdump output files that reuses the existing CFG analysis architecture.
Supports both Intel and AT&T syntax objdump output.
Can automatically execute objdump on object files or parse existing dump files.
"""

import re
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from .base_parser import BaseAssemblyParser
from .intel_parser import IntelAssemblyParser
from .att_parser import ATTAssemblyParser
from .models import ControlFlowGraph, BasicBlock, Instruction, TerminatorType


class ObjdumpParser(BaseAssemblyParser):
    """Parser for objdump output files"""
    
    def __init__(self, syntax_parser=None):
        """
        Initialize objdump parser with a syntax-specific parser.
        
        Args:
            syntax_parser: Intel or AT&T parser for instruction-specific logic.
                          If None, will auto-detect from first few instructions.
        """
        super().__init__()
        self.syntax_parser = syntax_parser
        self.address_to_label = {}  # Map addresses to labels
        self.label_to_address = {}  # Map labels to addresses
        
        # Objdump-specific patterns
        self.file_header_pattern = re.compile(r'^[^:]+:\s+file format')
        self.section_header_pattern = re.compile(r'^Disassembly of section')
        self.function_header_pattern = re.compile(r'^([0-9a-fA-F]+)\s+<([^>\.]+)>:')  # Functions don't start with dot
        self.label_header_pattern = re.compile(r'^([0-9a-fA-F]+)\s+<\.([^>]+)>:')      # Labels start with dot
        self.instruction_pattern = re.compile(r'^\s*([0-9a-fA-F]+):\s+([a-zA-Z][a-zA-Z0-9]*)\s*(.*)')
        
        # Initialize with default syntax patterns (will be overridden if syntax_parser provided)
        self._init_syntax_specific_patterns()
    
    def _init_syntax_specific_patterns(self):
        """Initialize default syntax patterns (Intel-like)"""
        self.unconditional_jumps = {'jmp', 'jmpq', 'jmpl'}
        self.conditional_jumps = {
            'je', 'jne', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle', 
            'ja', 'jae', 'jb', 'jbe', 'js', 'jns', 'jo', 'jno',
            'jc', 'jnc', 'jp', 'jnp', 'jpe', 'jpo', 'jecxz', 'jrcxz'
        }
        self.return_instructions = {'ret', 'retq', 'retl', 'retf', 'iret', 'iretq'}
        self.call_instructions = {'call', 'callq', 'calll'}
    
    def _auto_detect_syntax(self, lines: List[str]) -> str:
        """Auto-detect assembly syntax from objdump output"""
        # Look at the first few instructions to detect syntax
        att_indicators = 0
        intel_indicators = 0
        
        for line in lines[:20]:
            inst_match = self.instruction_pattern.match(line)
            if inst_match:
                operands = inst_match.group(3).strip()
                
                # AT&T syntax indicators
                if '%' in operands:  # Register syntax
                    att_indicators += 2
                if '$' in operands:  # Immediate syntax
                    att_indicators += 1
                
                # Intel syntax indicators (less definitive in objdump)
                if operands and not ('%' in operands or '$' in operands):
                    intel_indicators += 1
        
        return "att" if att_indicators > intel_indicators else "intel"
    
    def _setup_syntax_parser(self, lines: List[str]):
        """Setup the appropriate syntax parser"""
        if self.syntax_parser is None:
            detected_syntax = self._auto_detect_syntax(lines)
            if detected_syntax == "att":
                self.syntax_parser = ATTAssemblyParser()
            else:
                self.syntax_parser = IntelAssemblyParser()
            
            # Copy syntax-specific patterns
            self.unconditional_jumps = self.syntax_parser.unconditional_jumps
            self.conditional_jumps = self.syntax_parser.conditional_jumps
            self.return_instructions = self.syntax_parser.return_instructions
            self.call_instructions = self.syntax_parser.call_instructions
    
    def _parse_operands(self, operands: str) -> str:
        """Delegate operand parsing to syntax parser"""
        if self.syntax_parser:
            return self.syntax_parser._parse_operands(operands)
        return operands
    
    def _extract_jump_targets(self, operands: str) -> List[str]:
        """Extract jump targets from objdump operands"""
        targets = []
        
        # Objdump shows targets as addresses with optional symbols
        # Format: "address <symbol>" - be more specific to avoid matching hex in instruction names
        target_pattern = re.compile(r'\b([0-9a-fA-F]+)\s*<([^>]+)>')
        matches = target_pattern.findall(operands)
        
        for address, symbol in matches:
            # Try to resolve to a known label first
            resolved_label = self._resolve_address_to_label(address)
            if resolved_label:
                targets.append(resolved_label)
            else:
                # For objdump format like "170 <MonteCarlo_integrate+0x170>"
                # we use the address to create our block label
                targets.append(f"addr_{address}")
        
        # Also check for plain addresses without symbols
        if not matches:
            plain_address_pattern = re.compile(r'\b([0-9a-fA-F]+)\b')
            plain_matches = plain_address_pattern.findall(operands)
            for address in plain_matches:
                # Skip very short addresses that might be register offsets
                if len(address) >= 2:
                    resolved_label = self._resolve_address_to_label(address)
                    if resolved_label:
                        targets.append(resolved_label)
                    else:
                        targets.append(f"addr_{address}")
        
        return targets
    
    def _resolve_address_to_label(self, short_address: str) -> Optional[str]:
        """Resolve a short address to a known label"""
        # Try direct lookup first
        if short_address in self.address_to_label:
            return self.address_to_label[short_address]
        
        # Try with zero-padding (objdump uses short form, but we store long form)
        for stored_addr, label in self.address_to_label.items():
            if stored_addr.lstrip('0') == short_address.lstrip('0'):
                return label
        
        return None
    
    @staticmethod
    def is_object_file(file_path: str) -> bool:
        """Check if the file is an object file that needs objdump processing"""
        path = Path(file_path)
        object_extensions = {'.o', '.obj', '.so', '.a', '.dylib', '.dll'}
        
        # Check the final extension only (not compound extensions like .obj.dump)
        final_extension = path.suffix.lower()
        return final_extension in object_extensions
    
    @staticmethod
    def execute_objdump(file_path: str, function_name: Optional[str] = None) -> str:
        """
        Execute objdump on object file and return the output
        
        Args:
            file_path: Path to the object file
            function_name: Optional function name to disassemble (uses --disassemble=function)
            
        Returns:
            String containing objdump output
            
        Raises:
            FileNotFoundError: If objdump is not available
            subprocess.CalledProcessError: If objdump execution fails
            OSError: If the object file cannot be read
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Object file '{file_path}' not found")
        
        # Build objdump command
        cmd = ['objdump', '-d', '--no-show-raw-insn']
        
        # Add function-specific disassembly if requested
        if function_name:
            cmd.extend(['--disassemble=' + function_name])
        
        cmd.append(file_path)
        
        try:
            # Execute objdump and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 30 second timeout
            )
            return result.stdout
            
        except FileNotFoundError:
            raise FileNotFoundError(
                "objdump command not found. Please install binutils package or ensure objdump is in PATH."
            )
        except subprocess.TimeoutExpired:
            raise OSError(f"objdump execution timed out for file: {file_path}")
        except subprocess.CalledProcessError as e:
            raise OSError(f"objdump failed with exit code {e.returncode}: {e.stderr}")

    def parse_file_with_cfg(self, file_path: str) -> Dict[str, ControlFlowGraph]:
        """
        Parse objdump file or object file and build CFGs for all functions
        
        Args:
            file_path: Path to objdump output file or object file
            
        Returns:
            Dictionary mapping function names to their CFGs
        """
        lines = []
        
        try:
            # Check if this is an object file that needs objdump processing
            if self.is_object_file(file_path):
                print(f"Executing objdump on object file: {file_path}")
                objdump_output = self.execute_objdump(file_path)
                lines = objdump_output.splitlines()
            else:
                # Read existing objdump output file
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                lines = [line.rstrip() for line in lines]
                
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File '{file_path}' not found: {e}")
        except OSError as e:
            raise OSError(f"Error processing file '{file_path}': {e}")
        except Exception as e:
            raise IOError(f"Error reading file '{file_path}': {e}")
        
        # Setup syntax parser
        self._setup_syntax_parser(lines)
        
        # First pass: build address/label mappings
        self._build_address_mappings(lines)
        
        # Second pass: extract functions
        functions = self._parse_functions_with_lines(lines)
        cfgs = {}
        
        for func_name, start_line, end_line in functions:
            func_lines = lines[start_line:end_line+1]
            cfg = self._build_cfg_for_function(func_name, func_lines, start_line + 1)
            cfgs[func_name] = cfg
        
        return cfgs
    
    def parse_specific_function(self, file_path: str, function_name: str) -> Optional[ControlFlowGraph]:
        """
        Parse a specific function from objdump file or object file
        
        Args:
            file_path: Path to objdump output file or object file
            function_name: Name of the function to parse
            
        Returns:
            ControlFlowGraph for the specified function, or None if not found
        """
        lines = []
        
        try:
            # Check if this is an object file that needs objdump processing
            if self.is_object_file(file_path):
                print(f"Executing objdump on object file: {file_path} for function: {function_name}")
                # Use function-specific objdump for better performance
                objdump_output = self.execute_objdump(file_path, function_name)
                lines = objdump_output.splitlines()
            else:
                # Read existing objdump output file
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                lines = [line.rstrip() for line in lines]
                
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File '{file_path}' not found: {e}")
        except OSError as e:
            raise OSError(f"Error processing file '{file_path}': {e}")
        except Exception as e:
            raise IOError(f"Error reading file '{file_path}': {e}")
        
        # Setup syntax parser
        self._setup_syntax_parser(lines)
        
        # First pass: build address/label mappings
        self._build_address_mappings(lines)
        
        # Second pass: find the specific function
        functions = self._parse_functions_with_lines(lines)
        
        for func_name, start_line, end_line in functions:
            if func_name == function_name:
                func_lines = lines[start_line:end_line+1]
                return self._build_cfg_for_function(func_name, func_lines, start_line + 1)
        
        return None
    
    def _build_address_mappings(self, lines: List[str]):
        """Build mappings between addresses and labels"""
        for line in lines:
            # Function headers
            func_match = self.function_header_pattern.match(line)
            if func_match:
                address = func_match.group(1)
                name = func_match.group(2)
                self.address_to_label[address] = name
                self.label_to_address[name] = address
                continue
            
            # Label headers
            label_match = self.label_header_pattern.match(line)
            if label_match:
                address = label_match.group(1)
                label = label_match.group(2)
                self.address_to_label[address] = label
                self.label_to_address[label] = address
    
    def _parse_functions_with_lines(self, lines: List[str]) -> List[Tuple[str, int, int]]:
        """Parse functions and return their line ranges"""
        functions = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Look for function headers
            func_match = self.function_header_pattern.match(line)
            if func_match:
                func_name = func_match.group(2)
                start_line = i
                
                # Find end of function (next function or end of file)
                end_line = len(lines) - 1
                for j in range(i + 1, len(lines)):
                    # End at next function
                    if self.function_header_pattern.match(lines[j]):
                        end_line = j - 1
                        break
                    # End at empty line followed by non-instruction
                    if (not lines[j].strip() and 
                        j + 1 < len(lines) and 
                        not self.instruction_pattern.match(lines[j + 1]) and
                        not self.label_header_pattern.match(lines[j + 1])):
                        end_line = j - 1
                        break
                
                functions.append((func_name, start_line, end_line))
                i = end_line + 1
            else:
                i += 1
        
        return functions
    
    def _find_basic_block_starts(self, lines: List[str]) -> Set[int]:
        """Find all line numbers that start basic blocks in objdump format"""
        starts = set()
        
        for i, line in enumerate(lines):
            # Function headers start blocks
            if self.function_header_pattern.match(line):
                starts.add(i)
                continue
            
            # Label headers start blocks  
            if self.label_header_pattern.match(line):
                starts.add(i)
                continue
            
            # Instructions after terminators start new blocks
            if i > 0:
                prev_line = lines[i-1]
                if self._is_terminator_instruction_objdump(prev_line):
                    starts.add(i)
        
        return starts
    
    def _is_terminator_instruction_objdump(self, line: str) -> bool:
        """Check if objdump line contains a terminator instruction"""
        inst_match = self.instruction_pattern.match(line)
        if inst_match:
            opcode = inst_match.group(2).lower()
            return self._is_terminator_opcode(opcode)
        return False
    
    def _get_block_label(self, lines: List[str], start_idx: int) -> Optional[str]:
        """Extract label from objdump block start"""
        if start_idx < len(lines):
            line = lines[start_idx]
            
            # Function header
            func_match = self.function_header_pattern.match(line)
            if func_match:
                return func_match.group(2)
            
            # Label header
            label_match = self.label_header_pattern.match(line)
            if label_match:
                return label_match.group(2)
            
            # Instruction line - create synthetic label
            inst_match = self.instruction_pattern.match(line)
            if inst_match:
                address = inst_match.group(1)
                return f"addr_{address}"
        
        return None
    
    def _parse_instruction(self, line: str, line_number: int) -> Optional[Instruction]:
        """Parse a single objdump instruction"""
        # Skip headers and empty lines
        if (self.function_header_pattern.match(line) or 
            self.label_header_pattern.match(line) or
            not line.strip()):
            return None
        
        # Parse instruction
        inst_match = self.instruction_pattern.match(line)
        if not inst_match:
            return None
        
        address = inst_match.group(1)
        opcode = inst_match.group(2).lower()
        operands = inst_match.group(3).strip() if inst_match.group(3) else ""
        
        # Normalize operands using syntax parser
        normalized_operands = self._parse_operands(operands)
        
        # Determine if this is a terminator
        is_terminator = self._is_terminator_opcode(opcode)
        terminator_type = self._get_terminator_type(opcode)
        jump_targets = self._extract_jump_targets(operands) if is_terminator else []
        
        return Instruction(
            line_number=line_number,
            opcode=opcode,
            operands=normalized_operands,
            raw_line=line,
            is_terminator=is_terminator,
            terminator_type=terminator_type,
            jump_targets=jump_targets
        )
