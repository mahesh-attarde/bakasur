"""
Intel Assembly Parser

Specialized parser for Intel assembly syntax.
"""

import re
from typing import List
from .base_parser import BaseAssemblyParser


class IntelAssemblyParser(BaseAssemblyParser):
    """Parser for Intel assembly syntax"""
    
    def _init_syntax_specific_patterns(self):
        """Initialize Intel-specific patterns"""
        # Intel syntax terminator instructions
        self.unconditional_jumps = {'jmp', 'br'}
        self.conditional_jumps = {
            'je', 'jne', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle', 
            'ja', 'jae', 'jb', 'jbe', 'js', 'jns', 'jo', 'jno',
            'jc', 'jnc', 'jp', 'jnp', 'jpe', 'jpo', 'jecxz', 'jrcxz'
        }
        self.return_instructions = {'ret', 'retq', 'retf', 'iret', 'iretq'}
        self.call_instructions = {'call', 'callq'}
        
        # Intel syntax jump target pattern
        self.jump_target_pattern = re.compile(r'\.[A-Za-z_][A-Za-z0-9_]*')
    
    def _parse_operands(self, operands: str) -> str:
        """Parse Intel syntax operands - no special transformation needed"""
        return operands
    
    def _extract_jump_targets(self, operands: str) -> List[str]:
        """Extract jump target labels from Intel syntax operands"""
        targets = []
        matches = self.jump_target_pattern.findall(operands)
        for match in matches:
            # Remove the dot prefix if present
            target = match.lstrip('.')
            targets.append(target)
        return targets


# For backward compatibility, keep the original class name as an alias
CFGAssemblyParser = IntelAssemblyParser
