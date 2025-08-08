"""
Base Assembly Parser

Contains common functionality shared between Intel and AT&T assembly parsers.
"""

import re
from typing import List, Dict, Set, Optional, Tuple
from abc import ABC, abstractmethod
from .models import ControlFlowGraph, BasicBlock, Instruction, TerminatorType


class BaseAssemblyParser(ABC):
    """Base class for assembly parsers with common functionality"""
    
    def __init__(self):
        # Common directive patterns
        self.directive_pattern = re.compile(r'^\s*\.')
        self.type_function_pattern = re.compile(r'^\s*\.type\s+([^,\s]+)\s*,\s*@function')
        self.function_end_pattern = re.compile(r'^\s*\.Lfunc_end')
        
        # Common label patterns
        self.basic_block_pattern = re.compile(r'^\s*\.?([A-Za-z_][A-Za-z0-9_]*):')
        self.local_label_pattern = re.compile(r'^\s*\.[A-Za-z_][A-Za-z0-9_]*:')
        
        # Common instruction parsing pattern
        self.instruction_pattern = re.compile(r'^\s*([a-zA-Z][a-zA-Z0-9]*)\s*(.*)')
        
        # Jump target pattern - to be overridden by subclasses if needed
        self.jump_target_pattern = re.compile(r'\.[A-Za-z_][A-Za-z0-9_]*')
        
        # Initialize syntax-specific patterns in subclasses
        self._init_syntax_specific_patterns()
    
    @abstractmethod
    def _init_syntax_specific_patterns(self):
        """Initialize syntax-specific patterns (Intel vs AT&T)"""
        pass
    
    @abstractmethod
    def _parse_operands(self, operands: str) -> str:
        """Parse and normalize operands based on syntax"""
        pass
    
    @abstractmethod
    def _extract_jump_targets(self, operands: str) -> List[str]:
        """Extract jump target labels from operands (syntax-specific)"""
        pass
    
    def parse_file_with_cfg(self, file_path: str) -> Dict[str, ControlFlowGraph]:
        """
        Parse assembly file and build CFGs for all functions
        
        Returns:
            Dictionary mapping function names to their CFGs
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Assembly file '{file_path}' not found")
        except Exception as e:
            raise IOError(f"Error reading file '{file_path}': {e}")
        
        functions = self._parse_functions_with_lines(lines)
        cfgs = {}
        
        for func_name, start_line, end_line in functions:
            func_lines = lines[start_line-1:end_line]
            cfg = self._build_cfg_for_function(func_name, func_lines, start_line)
            cfgs[func_name] = cfg
        
        return cfgs
    
    def _parse_functions_with_lines(self, lines: List[str]) -> List[Tuple[str, int, int]]:
        """Parse functions and return their line ranges"""
        functions = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for .type directive ending with @function
            function_name = self._extract_function_name_from_type(line)
            if function_name:
                # Look for function label on next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if self._is_function_label(next_line, function_name):
                        start_line = i + 1  # 1-indexed, include the label
                        
                        # Find the end of function
                        end_line = self._find_function_end(lines, i + 2)
                        
                        if end_line:
                            functions.append((function_name, start_line, end_line))
                            i = end_line
                        else:
                            # Function without explicit end
                            functions.append((function_name, start_line, len(lines)))
                            i = len(lines)
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        
        return functions
    
    def _build_cfg_for_function(self, func_name: str, func_lines: List[str], base_line_num: int) -> ControlFlowGraph:
        """Build CFG for a single function"""
        cfg = ControlFlowGraph(func_name, "")
        
        # Step 1: Identify basic block boundaries
        block_starts = self._find_basic_block_starts(func_lines)
        
        # Step 2: Create basic blocks
        blocks = self._create_basic_blocks(func_lines, block_starts, base_line_num)
        
        # Step 3: Set entry block (first block with a label or first instruction)
        if blocks:
            first_block = next(iter(blocks.keys()))
            cfg.entry_block = first_block
        
        cfg.basic_blocks = blocks
        
        # Step 4: Build edges between blocks
        self._build_cfg_edges(cfg)
        
        # Step 5: Apply optimization passes
        cfg.optimize()
        
        return cfg
    
    def _find_basic_block_starts(self, lines: List[str]) -> Set[int]:
        """Find all line numbers that start basic blocks"""
        starts = set()
        
        # First line is always a block start
        starts.add(0)
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Labels start new blocks
            if self.local_label_pattern.match(stripped):
                starts.add(i)
            
            # Instructions after terminators start new blocks
            if i > 0:
                prev_line = lines[i-1].strip()
                if self._is_terminator_instruction(prev_line):
                    starts.add(i)
        
        return starts
    
    def _create_basic_blocks(self, lines: List[str], starts: Set[int], base_line_num: int) -> Dict[str, BasicBlock]:
        """Create basic blocks from line ranges"""
        blocks = {}
        start_list = sorted(starts)
        
        for i, start in enumerate(start_list):
            end = start_list[i + 1] - 1 if i + 1 < len(start_list) else len(lines) - 1
            
            # Find block label
            label = self._get_block_label(lines, start)
            if not label:
                label = f"bb_{start}"
            
            # Create basic block
            block = BasicBlock(
                label=label,
                start_line=base_line_num + start,
                end_line=base_line_num + end
            )
            
            # Parse instructions in this block
            for line_idx in range(start, end + 1):
                if line_idx < len(lines):
                    instruction = self._parse_instruction(lines[line_idx], base_line_num + line_idx)
                    if instruction:
                        block.instructions.append(instruction)
            
            blocks[label] = block
        
        return blocks
    
    def _get_block_label(self, lines: List[str], start_idx: int) -> Optional[str]:
        """Extract label from block start"""
        if start_idx < len(lines):
            line = lines[start_idx].strip()
            match = self.basic_block_pattern.match(line)
            if match:
                return match.group(1)
        return None
    
    def _parse_instruction(self, line: str, line_number: int) -> Optional[Instruction]:
        """Parse a single instruction"""
        stripped = line.strip()
        
        # Skip empty lines, comments, and directives
        if not stripped or stripped.startswith('#') or stripped.startswith('.'):
            return None
        
        # Skip labels
        if ':' in stripped and not ' ' in stripped.split(':')[0]:
            return None
        
        # Parse instruction
        match = self.instruction_pattern.match(stripped)
        if not match:
            return None
        
        opcode = match.group(1).lower()
        operands = match.group(2).strip() if match.group(2) else ""
        
        # Normalize operands based on syntax
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
    
    def _is_terminator_instruction(self, line: str) -> bool:
        """Check if line contains a terminator instruction"""
        stripped = line.strip()
        match = self.instruction_pattern.match(stripped)
        if match:
            opcode = match.group(1).lower()
            return self._is_terminator_opcode(opcode)
        return False
    
    def _is_terminator_opcode(self, opcode: str) -> bool:
        """Check if opcode is a terminator"""
        return (opcode in self.unconditional_jumps or 
                opcode in self.conditional_jumps or 
                opcode in self.return_instructions)
    
    def _get_terminator_type(self, opcode: str) -> Optional[TerminatorType]:
        """Get the type of terminator instruction"""
        if opcode in self.unconditional_jumps:
            return TerminatorType.UNCONDITIONAL_JUMP
        elif opcode in self.conditional_jumps:
            return TerminatorType.CONDITIONAL_JUMP
        elif opcode in self.return_instructions:
            return TerminatorType.RETURN
        return None
    
    def _build_cfg_edges(self, cfg: ControlFlowGraph):
        """Build edges between basic blocks in the CFG"""
        block_list = list(cfg.basic_blocks.keys())
        
        for i, block_label in enumerate(block_list):
            block = cfg.basic_blocks[block_label]
            terminator = block.terminator
            
            if terminator:
                # Add edges based on terminator type
                if terminator.terminator_type == TerminatorType.UNCONDITIONAL_JUMP:
                    # Only jump targets
                    for target in terminator.jump_targets:
                        target_block = self._find_target_block(target, cfg)
                        if target_block:
                            cfg.add_edge(block_label, target_block)
                
                elif terminator.terminator_type == TerminatorType.CONDITIONAL_JUMP:
                    # Both jump targets and fallthrough
                    for target in terminator.jump_targets:
                        target_block = self._find_target_block(target, cfg)
                        if target_block:
                            cfg.add_edge(block_label, target_block)
                    
                    # Fallthrough to next block
                    if i + 1 < len(block_list):
                        next_block = block_list[i + 1]
                        cfg.add_edge(block_label, next_block)
                
                elif terminator.terminator_type == TerminatorType.RETURN:
                    # No successors for return
                    pass
            else:
                # No explicit terminator - fallthrough to next block
                if i + 1 < len(block_list):
                    next_block = block_list[i + 1]
                    cfg.add_edge(block_label, next_block)
    
    def _find_target_block(self, target: str, cfg: ControlFlowGraph) -> Optional[str]:
        """Find the basic block that corresponds to a jump target"""
        # Remove leading dot if present
        clean_target = target.lstrip('.')
        
        # Try exact match first
        if clean_target in cfg.basic_blocks:
            return clean_target
        
        # Try with dot prefix
        dot_target = '.' + clean_target if not target.startswith('.') else target
        if dot_target.lstrip('.') in cfg.basic_blocks:
            return dot_target.lstrip('.')
            
        # Search through all block labels for a match
        for block_label in cfg.basic_blocks:
            if block_label == clean_target or block_label == target:
                return block_label
        
        return None
    
    def _extract_function_name_from_type(self, line: str) -> Optional[str]:
        """Extract function name from .type directive"""
        match = self.type_function_pattern.match(line)
        return match.group(1) if match else None
    
    def _is_function_label(self, line: str, expected_name: str) -> bool:
        """Check if line is a function label"""
        escaped_name = re.escape(expected_name)
        pattern = rf'^\s*{escaped_name}\s*:'
        return bool(re.match(pattern, line))
    
    def _find_function_end(self, lines: List[str], start_index: int) -> Optional[int]:
        """Find the end line of a function"""
        for j in range(start_index, len(lines)):
            if self.function_end_pattern.match(lines[j]):
                return j + 1
        return None
