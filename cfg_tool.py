#!/usr/bin/env python3
"""
Control Flow Graph Parser Command-Line Tool

This script parses assembly files and objdump files to build control flow graphs for functions.
It can analyze specific functions or all functions in the file.
Supports both Intel and AT&T assembly syntax.
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
    FileType,
    print_cfg_summary, 
    print_cfg_detailed, 
    export_cfg_to_dot
)

def parse_specific_function(file_path: str, function_name: str, verbose: bool = False, detailed: bool = False, syntax: str = "intel", file_type: str = "assembly"):
    """Parse and analyze a specific function"""
    try:
        parser = AssemblyParserFactory.create_parser(syntax, file_type)
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
        raise

def parse_all_functions(file_path: str, summary_only: bool = True, syntax: str = "intel", file_type: str = "assembly"):
    """Parse and analyze all functions in the file"""
    try:
        parser = AssemblyParserFactory.create_parser(syntax, file_type)
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
        raise

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
        description="Parse assembly files, objdump files, or object files to build control flow graphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse all functions (summary) - Intel syntax (default)
  python cfg_tool.py loops.s
  
  # Parse object file directly (auto-executes objdump)
  python cfg_tool.py loops.o -f function_name
  
  # Parse objdump file with AT&T syntax
  python cfg_tool.py loops.obj.dump -t objdump -s att
  
  # Auto-detect file type and syntax (recommended)
  python cfg_tool.py loops.o --auto-detect -f function_name
  python cfg_tool.py loops.obj.dump --auto-detect -f function_name
  
  # Parse specific function with AT&T syntax from assembly
  python cfg_tool.py loops.s -f MonteCarlo_integrate -s att
  
  # Parse object file with specific function (executes objdump automatically)
  python cfg_tool.py loops.o -f MonteCarlo_integrate -v
  
  # Parse objdump file with specific function
  python cfg_tool.py loops.obj.dump -f MonteCarlo_integrate -t objdump -v
  
  # Auto-detect syntax and parse specific function
  python cfg_tool.py loops.s -f MonteCarlo_integrate --auto-detect -v
  
  # Parse specific function with detailed output
  python cfg_tool.py loops.s -f MonteCarlo_integrate -v
  
  # Export CFG to DOT format with all instructions (object file)
  python cfg_tool.py loops.o -f MonteCarlo_integrate --export-dot
  
  # Export objdump CFG with limited instructions per block
  python cfg_tool.py loops.obj.dump -f function_name --export-dot --max-instructions 5 -t objdump
  
  # Export CFG without instructions (summary only)
  python cfg_tool.py loops.s -f MonteCarlo_integrate --export-dot --no-instructions
  
  # Parse all functions with detailed output (from object file)
  python cfg_tool.py loops.o --detailed
  
  # Export all CFGs to DOT files with instruction limit
  python cfg_tool.py loops.s --export-all-dot --max-instructions 3 -o output_dir

File Types Supported:
  - Assembly source files (.s, .asm)
  - Object files (.o, .obj, .so, .a, .dylib, .dll) - automatically executes objdump
  - Objdump output files (.dump, .objdump) - parses existing objdump output
        """
    )
    
    parser.add_argument('file', help='Assembly file (.s, .asm), object file (.o, .obj, .so, etc.), or objdump output file (.dump)')
    parser.add_argument('-f', '--function', help='Specific function to analyze')
    parser.add_argument('-s', '--syntax', choices=['intel', 'att'], default='intel',
                       help='Assembly syntax (default: intel)')
    parser.add_argument('-t', '--type', choices=['assembly', 'objdump'], default='assembly',
                       help='File type: assembly source or objdump output (default: assembly). Object files are auto-detected.')
    parser.add_argument('--auto-detect', action='store_true',
                       help='Auto-detect assembly syntax and file type from content (recommended)')
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
    
    # Determine file type and assembly syntax
    if args.auto_detect:
        detected_file_type = AssemblyParserFactory.detect_file_type(args.file)
        detected_syntax = AssemblyParserFactory.detect_syntax(args.file)
        file_type = detected_file_type.value
        syntax = detected_syntax.value
        print(f"Auto-detected file type: {file_type.upper()}")
        print(f"Auto-detected assembly syntax: {syntax.upper()}")
    else:
        file_type = args.type
        syntax = args.syntax
        print(f"Using file type: {file_type.upper()}")
        print(f"Using assembly syntax: {syntax.upper()}")
    
    # Create output directory if needed
    if args.export_dot or args.export_all_dot:
        Path(args.output_dir).mkdir(exist_ok=True)
    
    try:
        if args.function:
            # Parse specific function
            cfg = parse_specific_function(args.file, args.function, args.verbose, args.detailed, syntax, file_type)
            
            if cfg and args.export_dot:
                include_instructions = not args.no_instructions
                export_function_cfg(cfg, args.function, args.output_dir, include_instructions, args.max_instructions)
                
        else:
            # Parse all functions
            cfgs = parse_all_functions(args.file, summary_only=not args.detailed, syntax=syntax, file_type=file_type)
            
            if cfgs and args.export_all_dot:
                include_instructions = not args.no_instructions
                export_all_cfgs(cfgs, args.output_dir, include_instructions, args.max_instructions)
    
    except Exception:
        # Error already printed by parse functions
        sys.exit(1)
    
    if args.json:
        # TODO: Add JSON serialization of CFG data
        print("\nJSON export not yet implemented")

if __name__ == "__main__":
    main()
