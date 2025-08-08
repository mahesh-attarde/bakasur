"""
CFG Analyzer Package

A comprehensive Control Flow Graph analysis toolkit for assembly code.
Provides loop detection, visualization, and static analysis capabilities.
Supports both Intel and AT&T assembly syntax, and both assembly source and objdump files.
"""

# New syntax-aware imports
from .base_parser import BaseAssemblyParser
from .intel_parser import IntelAssemblyParser, CFGAssemblyParser  # CFGAssemblyParser for backward compatibility
from .att_parser import ATTAssemblyParser
from .objdump_parser import ObjdumpParser
from .parser_factory import AssemblyParserFactory, AssemblySyntax, FileType, create_cfg_parser

# Original imports
from .models import Instruction, BasicBlock, ControlFlowGraph, TerminatorType
from .visualization import export_cfg_to_dot, print_cfg_summary, print_cfg_detailed

__version__ = "1.2.0"
__author__ = "CFG Analysis Session"

__all__ = [
    # Backward compatibility
    'CFGAssemblyParser',
    
    # New syntax-aware classes
    'BaseAssemblyParser',
    'IntelAssemblyParser', 
    'ATTAssemblyParser',
    'ObjdumpParser',
    'AssemblyParserFactory',
    'AssemblySyntax',
    'FileType',
    'create_cfg_parser',
    
    # Data models
    'Instruction',
    'BasicBlock', 
    'ControlFlowGraph',
    'TerminatorType',
    
    # Visualization
    'export_cfg_to_dot',
    'print_cfg_summary',
    'print_cfg_detailed'
]
