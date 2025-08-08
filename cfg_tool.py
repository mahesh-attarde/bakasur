#!/usr/bin/env python3
"""
Control Flow Graph Parser Command-Line Tool

This script parses assembly files and builds control flow graphs for functions.
It can analyze specific functions or all functions in the file.
"""

import sys
import argparse
import json
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cfg_analyzer import (
    CFGAssemblyParser,  # For backward compatibility
    AssemblyParserFactory, 
    AssemblySyntax,
    print_cfg_summary, 
    print_cfg_detailed, 
    export_cfg_to_dot
)

def parse_specific_function(file_path: str, function_name: str, verbose: bool = False, detailed: bool = False, syntax: str = "intel"):
    """Parse and analyze a specific function"""
    try:
        parser = AssemblyParserFactory.create_parser(syntax)
    except ValueError as e:
        print(f"Error: {e}")
        return None
    
    try:
        cfgs = parser.parse_file_with_cfg(file_path)
        
        if function_name not in cfgs:
            print(f"Function '{function_name}' not found in {file_path}")
            available_functions = list(cfgs.keys())
            if available_functions:
                print(f"Available functions: {', '.join(available_functions)}")
            return None
        
        cfg = cfgs[function_name]
        
        if detailed:
            print_cfg_detailed(cfg)
        else:
            print(f"Control Flow Graph for function: {function_name}")
            print("=" * 60)
            print_cfg_summary(cfg)
        
        if verbose and not detailed:
            print("\nDetailed Block Information:")
            print("-" * 40)
            for label, block in cfg.basic_blocks.items():
                print(f"\nBlock: {label}")
                print(f"  Lines: {block.start_line}-{block.end_line}")
                print(f"  Instructions:")
                for inst in block.instructions:
                    marker = " *" if inst.is_terminator else "  "
                    print(f"   {marker} {inst.line_number}: {inst.opcode} {inst.operands}")
                    if inst.is_terminator:
                        print(f"      -> Terminator: {inst.terminator_type.value}")
                        if inst.jump_targets:
                            print(f"      -> Targets: {', '.join(inst.jump_targets)}")
        
        return cfg
        
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None

def parse_all_functions(file_path: str, summary_only: bool = True, syntax: str = "intel"):
    """Parse and analyze all functions in the file"""
    try:
        parser = AssemblyParserFactory.create_parser(syntax)
    except ValueError as e:
        print(f"Error: {e}")
        return {}
    
    try:
        cfgs = parser.parse_file_with_cfg(file_path)
        
        if not cfgs:
            print(f"No functions found in {file_path}")
            return {}
        
        print(f"Found {len(cfgs)} function(s) in {file_path}")
        print("=" * 60)
        
        for func_name, cfg in cfgs.items():
            if summary_only:
                print(f"\n{func_name}:")
                print(f"  Blocks: {len(cfg.basic_blocks)}")
                print(f"  Entry: {cfg.entry_block}")
                
                # Count edges
                total_edges = sum(len(block.successors) for block in cfg.basic_blocks.values())
                print(f"  Edges: {total_edges}")
                
                # Detect loops
                loops = cfg.get_loops()
                print(f"  Loops: {len(loops)}")
                
                # Exit blocks
                exit_blocks = [label for label, block in cfg.basic_blocks.items() if block.is_exit_block]
                print(f"  Exit blocks: {len(exit_blocks)}")
            else:
                print(f"\n{'='*20} {func_name} {'='*20}")
                print_cfg_summary(cfg)
        
        return cfgs
        
    except Exception as e:
        print(f"Error parsing file: {e}")
        return {}

def export_function_cfg(cfg, function_name: str, output_dir: str = ".", include_instructions: bool = True, max_instructions: int = None):
    """Export a function's CFG to DOT format"""
    output_path = Path(output_dir) / f"{function_name}_cfg.dot"
    export_cfg_to_dot(cfg, str(output_path), include_instructions=include_instructions, max_instructions=max_instructions)
    print(f"CFG exported to: {output_path}")
    print(f"To visualize: dot -Tpng {output_path} -o {function_name}_cfg.png")

def export_all_cfgs(cfgs: dict, output_dir: str = ".", include_instructions: bool = True, max_instructions: int = None):
    """Export all CFGs to DOT format"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for func_name, cfg in cfgs.items():
        dot_file = output_path / f"{func_name}_cfg.dot"
        export_cfg_to_dot(cfg, str(dot_file), include_instructions=include_instructions, max_instructions=max_instructions)
        print(f"Exported {func_name} CFG to: {dot_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Parse assembly files and build control flow graphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse all functions (summary) - Intel syntax (default)
  python cfg_tool.py loops.s
  
  # Parse specific function with AT&T syntax
  python cfg_tool.py loops.s -f MonteCarlo_integrate -s att
  
  # Auto-detect syntax and parse specific function
  python cfg_tool.py loops.s -f MonteCarlo_integrate --auto-detect -v
  
  # Parse specific function with detailed output
  python cfg_tool.py loops.s -f MonteCarlo_integrate -v
  
  # Export CFG to DOT format with all instructions
  python cfg_tool.py loops.s -f MonteCarlo_integrate --export-dot
  
  # Export CFG with limited instructions per block (AT&T syntax)
  python cfg_tool.py loops.s -f MonteCarlo_integrate --export-dot --max-instructions 5 -s att
  
  # Export CFG without instructions (summary only)
  python cfg_tool.py loops.s -f MonteCarlo_integrate --export-dot --no-instructions
  
  # Parse all functions with detailed output
  python cfg_tool.py loops.s --detailed
  
  # Export all CFGs to DOT files with instruction limit
  python cfg_tool.py loops.s --export-all-dot --max-instructions 3 -o output_dir
        """
    )
    
    parser.add_argument('file', help='Assembly file to parse')
    parser.add_argument('-f', '--function', help='Specific function to analyze')
    parser.add_argument('-s', '--syntax', choices=['intel', 'att'], default='intel',
                       help='Assembly syntax (default: intel)')
    parser.add_argument('--auto-detect', action='store_true',
                       help='Auto-detect assembly syntax from file content')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Show detailed instruction information')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed information for all functions')
    parser.add_argument('--export-dot', action='store_true',
                       help='Export CFG to DOT format (requires -f)')
    parser.add_argument('--export-all-dot', action='store_true',
                       help='Export all CFGs to DOT format')
    parser.add_argument('--no-instructions', action='store_true',
                       help='Exclude instructions from DOT output (summary only)')
    parser.add_argument('--max-instructions', type=int, metavar='N',
                       help='Limit number of instructions shown per block in DOT output (default: no limit)')
    parser.add_argument('-o', '--output-dir', default='.',
                       help='Output directory for exported files')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    # Determine assembly syntax
    if args.auto_detect:
        detected_syntax = AssemblyParserFactory.detect_syntax(args.file)
        syntax = detected_syntax.value
        print(f"Auto-detected assembly syntax: {syntax.upper()}")
    else:
        syntax = args.syntax
        print(f"Using assembly syntax: {syntax.upper()}")
    
    # Create output directory if needed
    if args.export_dot or args.export_all_dot:
        Path(args.output_dir).mkdir(exist_ok=True)
    
    if args.function:
        # Parse specific function
        cfg = parse_specific_function(args.file, args.function, args.verbose, args.detailed, syntax)
        
        if cfg and args.export_dot:
            include_instructions = not args.no_instructions
            export_function_cfg(cfg, args.function, args.output_dir, include_instructions, args.max_instructions)
            
    else:
        # Parse all functions
        cfgs = parse_all_functions(args.file, summary_only=not args.detailed, syntax=syntax)
        
        if cfgs and args.export_all_dot:
            include_instructions = not args.no_instructions
            export_all_cfgs(cfgs, args.output_dir, include_instructions, args.max_instructions)
    
    if args.json:
        # TODO: Add JSON serialization of CFG data
        print("\nJSON export not yet implemented")

if __name__ == "__main__":
    main()
