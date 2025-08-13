#!/usr/bin/env python3
"""
Enhanced Data Flow Visualization

Creative and intuitive visualizations for data flow dependencies including:
1. ASCII Art Flow Diagrams
2. Interactive SVG with enhanced layouts

Thinking outside the box for maximum comprehension.
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import textwrap


class VisualizationStyle(Enum):
    """Different visualization styles available"""
    CLASSIC_ASCII = "classic"
    FLOW_DIAGRAM = "flow"


@dataclass
class EnhancedDependency:
    """Enhanced dependency with visual metadata"""
    source_line: int
    target_line: int
    resource: str
    dependency_type: str  # 'RAW', 'WAR', 'WAW'
    operand_type: str    # 'register', 'memory'
    strength: float = 1.0  # Dependency strength (0.0-1.0)
    critical_path: bool = False  # Is this on the critical path?
    
    def get_symbol(self) -> str:
        """Get visual symbol for this dependency type"""
        symbols = {
            'RAW': 'R',  # R for true dependencies (RAW)
            'WAR': 'A',  # A for anti-dependencies (WAR)
            'WAW': 'O'   # O for output dependencies (WAW)
        }
        return symbols.get(self.dependency_type, 'D')
    
    def get_ascii_symbol(self) -> str:
        """Get ASCII symbol for this dependency type"""
        symbols = {
            'RAW': '>>',  # True dependency (data flows forward)
            'WAR': '<>',  # Anti dependency (conflict)
            'WAW': '>>',  # Output dependency (overwrites)
        }
        return symbols.get(self.dependency_type, '->')


class EnhancedDataFlowVisualizer:
    """Enhanced data flow visualizer with multiple creative representation styles"""
    
    def __init__(self):
        # ASCII characters for better visual representation
        self.symbols = {
            'box_top_left': '+',
            'box_top_right': '+', 
            'box_bottom_left': '+',
            'box_bottom_right': '+',
            'box_horizontal': '-',
            'box_vertical': '|',
            'arrow_right': '->',
            'arrow_down': 'v',
            'arrow_up': '^',
            'arrow_diagonal_se': '\\',
            'arrow_diagonal_sw': '/',
            'dependency_raw': 'R',
            'dependency_war': 'A', 
            'dependency_waw': 'O',
            'register': 'REG',
            'memory': 'MEM',
            'instruction': 'INST',
            'cpu': 'CPU',
            'pipeline_stage': 'PIPE'
        }
        
        # Color schemes for different elements
        self.colors = {
            'instruction': '\033[94m',      # Blue
            'register': '\033[92m',         # Green
            'memory': '\033[93m',           # Yellow
            'dependency_raw': '\033[91m',   # Red
            'dependency_war': '\033[94m',   # Blue
            'dependency_waw': '\033[95m',   # Magenta
            'reset': '\033[0m',             # Reset
            'bold': '\033[1m',              # Bold
            'underline': '\033[4m'          # Underline
        }
    
    def colorize(self, text: str, color_key: str) -> str:
        """Add color to text"""
        return f"{self.colors.get(color_key, '')}{text}{self.colors['reset']}"
    
    def create_ascii_flow_diagram(self, instructions: List, dependencies: List[EnhancedDependency]) -> str:
        """Create an ASCII flow diagram showing instruction flow and dependencies"""
        
        lines = []
        lines.append(self.colorize("DATA FLOW ANALYSIS", 'bold'))
        lines.append("=" * 60)
        lines.append("")
        
        # Create instruction boxes with visual enhancements
        max_width = max(len(str(instr)) for instr in instructions) + 10
        box_width = min(max_width, 50)
        
        for i, instruction in enumerate(instructions):
            # Instruction box with Unicode border
            instr_text = f"L{i}: {instruction.opcode} {', '.join(instruction.operands[:3])}"
            if len(instruction.operands) > 3:
                instr_text += "..."
            
            # Wrap long instructions
            wrapped = textwrap.fill(instr_text, box_width - 4)
            instr_lines = wrapped.split('\n')
            
            # Create box
            lines.append(f"+{'-' * (box_width - 2)}+")
            for line in instr_lines:
                padded = line.ljust(box_width - 4)
                lines.append(f"| {self.colorize(padded, 'instruction')} |")
            lines.append(f"+{'-' * (box_width - 2)}+")
            
            # Show dependencies from this instruction
            outgoing_deps = [dep for dep in dependencies if dep.source_line == i]
            if outgoing_deps:
                for dep in outgoing_deps:
                    arrow = "v"
                    dep_symbol = dep.get_ascii_symbol()
                    resource_icon = "REG" if dep.operand_type == 'register' else "MEM"
                    
                    dep_text = f"  {arrow} {dep_symbol} {resource_icon} {dep.resource} -> L{dep.target_line}"
                    color_key = f"dependency_{dep.dependency_type.lower()}"
                    lines.append(self.colorize(dep_text, color_key))
                lines.append("")
            else:
                lines.append("")
        
        return '\n'.join(lines)
    
    def create_classic_ascii_visualization(self, instructions: List, dependencies: List[EnhancedDependency]) -> str:
        """Create classic ASCII text visualization"""
        lines = []
        lines.append("=== INSTRUCTIONS ===")
        
        for i, instruction in enumerate(instructions):
            lines.append(f"Line {i}: {instruction}")
        
        lines.append("")
        lines.append("=== DEPENDENCIES ===")
        
        if dependencies:
            for dep in dependencies:
                dep_icon = "REG" if dep.operand_type == 'register' else "MEM"
                lines.append(f"{dep_icon} L{dep.source_line} -> L{dep.target_line}: {dep.resource} ({dep.dependency_type})")
        else:
            lines.append("No dependencies found")
        
        return '\n'.join(lines)
    
    def visualize(self, instructions: List, dependencies: List, 
                 style: VisualizationStyle = VisualizationStyle.FLOW_DIAGRAM) -> str:
        """Main visualization method supporting ASCII styles only"""
        
        # Convert to enhanced dependencies
        enhanced_deps = []
        for dep in dependencies:
            enhanced_dep = EnhancedDependency(
                source_line=dep.source_line,
                target_line=dep.target_line,
                resource=dep.resource,
                dependency_type=dep.dependency_type,
                operand_type=dep.operand_type
            )
            enhanced_deps.append(enhanced_dep)
        
        # Route to appropriate visualization method (ASCII only)
        if style == VisualizationStyle.CLASSIC_ASCII:
            return self.create_classic_ascii_visualization(instructions, enhanced_deps)
        else:  # FLOW_DIAGRAM or any other value defaults to flow diagram
            return self.create_ascii_flow_diagram(instructions, enhanced_deps)
    
    def create_comprehensive_report(self, instructions: List, dependencies: List) -> str:
        """Create a comprehensive ASCII-only analysis report"""
        
        report_lines = []
        report_lines.append(self.colorize("COMPREHENSIVE DATA FLOW ANALYSIS REPORT", 'bold'))
        report_lines.append("=" * 70)
        report_lines.append("")
        
        # Basic statistics
        report_lines.append(self.colorize("STATISTICS", 'bold'))
        report_lines.append(f"Total Instructions: {len(instructions)}")
        report_lines.append(f"Total Dependencies: {len(dependencies)}")
        
        dep_counts = {'RAW': 0, 'WAR': 0, 'WAW': 0}
        operand_counts = {'register': 0, 'memory': 0}
        
        for dep in dependencies:
            dep_counts[dep.dependency_type] += 1
            operand_counts[dep.operand_type] += 1
        
        report_lines.append(f"RAW Dependencies: {dep_counts['RAW']}")
        report_lines.append(f"WAR Dependencies: {dep_counts['WAR']}")  
        report_lines.append(f"WAW Dependencies: {dep_counts['WAW']}")
        report_lines.append(f"Register Dependencies: {operand_counts['register']}")
        report_lines.append(f"Memory Dependencies: {operand_counts['memory']}")
        report_lines.append("")
        
        # Include ASCII visualization styles only
        styles = [
            (VisualizationStyle.FLOW_DIAGRAM, "FLOW DIAGRAM"),
            (VisualizationStyle.CLASSIC_ASCII, "CLASSIC ASCII")
        ]
        
        for style, title in styles:
            report_lines.append("")
            report_lines.append("=" * 70)
            visualization = self.visualize(instructions, dependencies, style)
            report_lines.append(visualization)
        
        return '\n'.join(report_lines)


def demo_enhanced_visualization():
    """Demo function showing enhanced visualization capabilities"""
    
    # Create sample instructions and dependencies for demo
    from dataclasses import dataclass
    from typing import Optional
    
    @dataclass
    class Instruction:
        line_num: int
        label: Optional[str]
        opcode: str
        operands: list
        raw_line: str = ""
    
    @dataclass 
    class DataDependency:
        source_line: int
        target_line: int
        resource: str
        dependency_type: str
        operand_type: str
    
    # Sample assembly with various dependency types
    instructions = [
        Instruction(0, None, "mov", ["eax", "ebx"]),
        Instruction(1, None, "mov", ["dword ptr [rcx]", "eax"]),
        Instruction(2, None, "mov", ["edx", "dword ptr [rcx]"]), 
        Instruction(3, None, "add", ["eax", "edx"]),
        Instruction(4, None, "mov", ["dword ptr [rsi]", "eax"])
    ]
    
    dependencies = [
        DataDependency(0, 1, "rax", "RAW", "register"),
        DataDependency(1, 2, "[rcx]", "RAW", "memory"),
        DataDependency(0, 3, "rax", "WAW", "register"),
        DataDependency(2, 3, "rdx", "RAW", "register"),
        DataDependency(3, 4, "rax", "RAW", "register")
    ]
    
    visualizer = EnhancedDataFlowVisualizer()
    
    print("ENHANCED DATA FLOW VISUALIZATION DEMO")
    print("=" * 50)
    print()
    
    # Show different visualization styles
    styles_to_demo = [
        (VisualizationStyle.FLOW_DIAGRAM, "ASCII Flow Diagram"),
        (VisualizationStyle.CLASSIC_ASCII, "Classic ASCII"),
    ]
    
    for style, name in styles_to_demo:
        print(f"\n{name.upper()}")
        print("-" * 40)
        result = visualizer.visualize(instructions, dependencies, style)
        print(result)
        print()


if __name__ == "__main__":
    demo_enhanced_visualization()
