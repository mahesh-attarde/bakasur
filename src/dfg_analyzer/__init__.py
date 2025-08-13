"""
Data Flow Graph (DFG) Analyzer Package

A configurable data flow analysis tool that supports multiple architectures
through JSON configuration files.
"""

from .models import Instruction, DataDependency
from .analyzer import DataFlowAnalyzer
from .generic_parser import GenericAssemblyParser, IntelAssemblyParser, ARM64AssemblyParser
from .arch_config import (
    ArchitectureConfig, ArchitectureLoader, 
    load_architecture, get_available_architectures, detect_architecture
)
from .visualization import DataFlowVisualizer
from .enhanced_visualizer import EnhancedDataFlowVisualizer, VisualizationStyle
from .ascii_visualizer import ASCIIDataFlowVisualizer

__all__ = [
    'Instruction',
    'DataDependency',
    'DataFlowAnalyzer',
    'GenericAssemblyParser',
    'IntelAssemblyParser',
    'ARM64AssemblyParser',
    'ArchitectureConfig',
    'ArchitectureLoader',
    'load_architecture',
    'get_available_architectures', 
    'detect_architecture',
    'DataFlowVisualizer',
    'EnhancedDataFlowVisualizer',
    'VisualizationStyle',
    'ASCIIDataFlowVisualizer'
]
