#!/usr/bin/env python3
"""
Data Flow Graph (DFG) Analysis Tool

Analyzes data flow dependencies in assembly basic blocks and creates visualizations.
This tool complements the CFG tool by focusing on data dependencies within basic blocks.
Supports multiple architectures through JSON configuration files.

Usage:
  python dfg_tool.py <assembly_file> [options]
  python dfg_tool.py --demo

Options:
  --arch ARCH           Target architecture: x86_64, aarch64 (default: auto-detect)
  --style STYLE         Visualization style: enhanced, classic, comprehensive (default: enhanced)
  --output FILE         Output file for SVG (default: dataflow)
  --svg                 Generate SVG graph
  --demo                Run with demo assembly code
  --list-archs          List available architectures
  --help, -h            Show this help message

Examples:
  python dfg_tool.py example.s --style enhanced
  python dfg_tool.py loop.s --svg --output loop_dataflow
  python dfg_tool.py --demo --style comprehensive
  python dfg_tool.py arm_code.s --arch aarch64
  python dfg_tool.py --list-archs
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dfg_analyzer import (
    DataFlowAnalyzer, 
    DataFlowVisualizer, 
    EnhancedDataFlowVisualizer,
    VisualizationStyle,
    ASCIIDataFlowVisualizer,
    get_available_architectures,
    detect_architecture
)


def read_assembly_file(file_path: str) -> str:
    """Read assembly file and return content"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        sys.exit(1)


def get_demo_assembly(architecture: str = "x86_64") -> str:
    """Return demo assembly code for testing"""
    if architecture == "x86_64":
        return """
.LBB0_72:
    lea esi, [rax + rdx]
    and esi, 4095
    vmovss xmm0, dword ptr [rcx + 4*rsi]
    vmovss dword ptr [r15 + 4*rdx], xmm0
    inc rdx
    cmp r12, rdx
    jne .LBB0_72
"""
    elif architecture == "aarch64":
        return """
loop:
    add x1, x0, x2
    and w1, w1, #4095
    ldr s0, [x3, x1, lsl #2]
    str s0, [x4, x2, lsl #2]
    add x2, x2, #1
    cmp x5, x2
    b.ne loop
"""
    else:
        # Default to x86_64
        return get_demo_assembly("x86_64")


def main():
    parser = argparse.ArgumentParser(
        description="Data Flow Graph (DFG) Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dfg_tool.py example.s --style enhanced
  python dfg_tool.py loop.s --svg --output loop_dataflow
  python dfg_tool.py --demo --style comprehensive
  python dfg_tool.py arm_code.s --arch aarch64
  python dfg_tool.py --list-archs
        """
    )
    
    parser.add_argument('file', nargs='?', help='Assembly file to analyze')
    parser.add_argument('--arch', choices=get_available_architectures() + ['auto'],
                       default='auto', help='Target architecture (default: auto-detect)')
    parser.add_argument('--style', choices=['enhanced', 'classic', 'comprehensive'],
                       default='enhanced', help='Visualization style (default: enhanced)')
    parser.add_argument('--output', default='dataflow', 
                       help='Output file name for SVG (default: dataflow)')
    parser.add_argument('--svg', action='store_true',
                       help='Generate SVG dependency graph')
    parser.add_argument('--demo', action='store_true',
                       help='Run with demo assembly code')
    parser.add_argument('--list-archs', action='store_true',
                       help='List available architectures')
    
    args = parser.parse_args()
    
    # Handle list architectures
    if args.list_archs:
        print("Available Architectures:")
        print("=" * 30)
        for arch in get_available_architectures():
            print(f"  * {arch}")
        print(f"\nTotal: {len(get_available_architectures())} architectures")
        print("\nUse --arch <architecture> to specify, or 'auto' for auto-detection")
        return
    
    # Determine architecture and assembly text
    if args.demo:
        # For demo, use specified architecture or default
        target_arch = args.arch if args.arch != 'auto' else 'x86_64'
        assembly_text = get_demo_assembly(target_arch)
        print(f"DFG Analysis - Demo Mode ({target_arch})")
        print("=" * 50)
    elif args.file:
        assembly_text = read_assembly_file(args.file)
        
        # Determine target architecture
        if args.arch == 'auto':
            target_arch = detect_architecture(assembly_text)
            if target_arch:
                print(f"DFG Analysis - {args.file} (detected: {target_arch})")
            else:
                target_arch = 'x86_64'  # fallback
                print(f"DFG Analysis - {args.file} (fallback: {target_arch})")
        else:
            target_arch = args.arch
            print(f"DFG Analysis - {args.file} (specified: {target_arch})")
        print("=" * 50)
    else:
        print("Error: Please provide an assembly file or use --demo")
        parser.print_help()
        sys.exit(1)
    
    # Create analyzer with specified architecture
    try:
        analyzer = DataFlowAnalyzer(target_arch)
        
        # Show architecture info
        arch_info = analyzer.get_architecture_info()
        print(f"Architecture: {arch_info['architecture']} ({arch_info['description']})")
        print(f"Syntax: {arch_info['syntax']}")
        print(f"Registers: {arch_info['total_registers']} total")
        print()
        
        # Create visualizer based on style
        if args.style == 'enhanced':
            visualizer = DataFlowVisualizer()
            visualizer.analyzer = analyzer  # Use our configured analyzer
            visualizer.analyze_and_print(assembly_text, style="enhanced")
        elif args.style == 'comprehensive':
            visualizer = DataFlowVisualizer() 
            visualizer.analyzer = analyzer  # Use our configured analyzer
            visualizer.analyze_and_print(assembly_text, style="comprehensive")
        else:  # classic
            visualizer = DataFlowVisualizer()
            visualizer.analyzer = analyzer  # Use our configured analyzer
            visualizer.analyze_and_print(assembly_text, style="classic")
        
        # Generate SVG if requested
        if args.svg:
            try:
                visualizer = DataFlowVisualizer()
                visualizer.analyzer = analyzer  # Use our configured analyzer
                output_path = visualizer.create_dependency_graph(
                    assembly_text, 
                    args.output,
                    enhanced=(args.style == 'enhanced')
                )
                print(f"\nSVG dependency graph saved to: {output_path}")
                print("Open the SVG file in a web browser to view the interactive graph.")
            except Exception as e:
                print(f"\nError creating SVG: {e}")
                print("Make sure Graphviz is installed: pip install graphviz")
                
    except ValueError as e:
        print(f"Architecture Error: {e}")
        print(f"Available architectures: {', '.join(get_available_architectures())}")
        sys.exit(1)
    except Exception as e:
        print(f"Analysis Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
