"""
Assembly Parser Factory

Factory for creating the appropriate assembly parser based on syntax.
"""

from enum import Enum
from typing import Union
from .base_parser import BaseAssemblyParser
from .intel_parser import IntelAssemblyParser
from .att_parser import ATTAssemblyParser


class AssemblySyntax(Enum):
    """Supported assembly syntaxes"""
    INTEL = "intel"
    ATT = "att"


class AssemblyParserFactory:
    """Factory for creating assembly parsers"""
    
    @staticmethod
    def create_parser(syntax: Union[AssemblySyntax, str] = AssemblySyntax.INTEL) -> BaseAssemblyParser:
        """
        Create an assembly parser for the specified syntax.
        
        Args:
            syntax: The assembly syntax (Intel or AT&T). Defaults to Intel.
            
        Returns:
            BaseAssemblyParser: The appropriate parser instance
            
        Raises:
            ValueError: If the syntax is not supported
        """
        if isinstance(syntax, str):
            try:
                syntax = AssemblySyntax(syntax.lower())
            except ValueError:
                raise ValueError(f"Unsupported assembly syntax: {syntax}. "
                               f"Supported syntaxes: {[s.value for s in AssemblySyntax]}")
        
        if syntax == AssemblySyntax.INTEL:
            return IntelAssemblyParser()
        elif syntax == AssemblySyntax.ATT:
            return ATTAssemblyParser()
        else:
            raise ValueError(f"Unsupported assembly syntax: {syntax}")
    
    @staticmethod
    def get_supported_syntaxes() -> list[str]:
        """Get list of supported assembly syntaxes"""
        return [syntax.value for syntax in AssemblySyntax]
    
    @staticmethod
    def detect_syntax(file_path: str) -> AssemblySyntax:
        """
        Attempt to auto-detect assembly syntax from file content.
        
        Args:
            file_path: Path to the assembly file
            
        Returns:
            AssemblySyntax: The detected syntax (defaults to Intel if uncertain)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple heuristics for syntax detection
            att_indicators = 0
            intel_indicators = 0
            
            lines = content.split('\n')[:100]  # Check first 100 lines
            
            for line in lines:
                line = line.strip().lower()
                
                # Skip comments and empty lines
                if not line or line.startswith('#') or line.startswith('.'):
                    continue
                
                # AT&T syntax indicators
                if '%' in line and ('movl' in line or 'movq' in line):  # AT&T register syntax
                    att_indicators += 2
                if '$' in line and ('mov' in line or 'cmp' in line):  # AT&T immediate syntax
                    att_indicators += 1
                if line.endswith('q') or line.endswith('l'):  # AT&T suffix
                    att_indicators += 1
                
                # Intel syntax indicators  
                if 'mov ' in line and not '%' in line:  # Intel mov without % registers
                    intel_indicators += 1
                if ('eax' in line or 'rax' in line) and not '%' in line:  # Intel register syntax
                    intel_indicators += 1
            
            # Return detected syntax
            if att_indicators > intel_indicators:
                return AssemblySyntax.ATT
            else:
                return AssemblySyntax.INTEL
                
        except Exception:
            # Default to Intel if detection fails
            return AssemblySyntax.INTEL


# Convenience function for backward compatibility
def create_cfg_parser(syntax: Union[AssemblySyntax, str] = AssemblySyntax.INTEL) -> BaseAssemblyParser:
    """Create a CFG assembly parser. Alias for AssemblyParserFactory.create_parser()"""
    return AssemblyParserFactory.create_parser(syntax)
