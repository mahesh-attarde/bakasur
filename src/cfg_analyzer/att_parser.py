"""
AT&T Assembly Parser

Specialized parser for AT&T assembly syntax.
"""

import re
from typing import List
from .base_parser import BaseAssemblyParser


class ATTAssemblyParser(BaseAssemblyParser):
    """Parser for AT&T assembly syntax"""
    
    def _init_syntax_specific_patterns(self):
        """Initialize AT&T-specific patterns"""
        # AT&T syntax terminator instructions (same opcodes, different suffixes)
        self.unconditional_jumps = {'jmp', 'jmpq', 'jmpl', 'br'}
        self.conditional_jumps = {
            'je', 'jne', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle', 
            'ja', 'jae', 'jb', 'jbe', 'js', 'jns', 'jo', 'jno',
            'jc', 'jnc', 'jp', 'jnp', 'jpe', 'jpo', 'jecxz', 'jrcxz',
            # AT&T suffix variants
            'jeq', 'jneq', 'jzq', 'jnzq', 'jgq', 'jgeq', 'jlq', 'jleq',
            'jaq', 'jaeq', 'jbq', 'jbeq', 'jsq', 'jnsq', 'joq', 'jnoq',
            'jcq', 'jncq', 'jpq', 'jnpq', 'jpeq', 'jpoq'
        }
        self.return_instructions = {'ret', 'retq', 'retl', 'retf', 'iret', 'iretq'}
        self.call_instructions = {'call', 'callq', 'calll'}
        
        # AT&T syntax jump target pattern - targets can be with or without $ prefix
        self.jump_target_pattern = re.compile(r'[\$]?\.[A-Za-z_][A-Za-z0-9_]*|[\$]?[A-Za-z_][A-Za-z0-9_]*')
    
    def _parse_operands(self, operands: str) -> str:
        """Parse AT&T syntax operands and normalize them"""
        # AT&T syntax transformations:
        # - Registers have % prefix: %eax, %rax
        # - Immediate values have $ prefix: $10
        # - Memory operands: offset(%base,%index,scale)
        # - For CFG analysis, we mainly care about jump targets, so minimal transformation needed
        
        return operands
    
    def _extract_jump_targets(self, operands: str) -> List[str]:
        """Extract jump target labels from AT&T syntax operands"""
        targets = []
        
        # In AT&T syntax, jump targets can appear as:
        # - .label
        # - label
        # - $label (immediate addressing)
        
        # Remove common AT&T prefixes and suffixes for jump target detection
        cleaned_operands = operands.strip()
        
        # Handle different AT&T jump target formats
        att_target_patterns = [
            re.compile(r'\$?\.[A-Za-z_][A-Za-z0-9_]*'),  # $.label or .label
            re.compile(r'\$?[A-Za-z_][A-Za-z0-9_]*(?=\s*$|,)'),  # $label or label (at end or before comma)
        ]
        
        for pattern in att_target_patterns:
            matches = pattern.findall(cleaned_operands)
            for match in matches:
                # Clean up the target
                target = match.lstrip('$').lstrip('.')
                if target and target not in targets:  # Avoid duplicates
                    targets.append(target)
        
        return targets
