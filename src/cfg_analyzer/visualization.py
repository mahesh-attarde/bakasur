"""
CFG Visualization

Functions for printing CFG information and exporting to DOT format
for GraphViz visualization.
"""

from typing import Optional
from .models import ControlFlowGraph, BasicBlock


def print_cfg_summary(cfg: ControlFlowGraph):
    """Print a summary of the control flow graph"""
    print(f"Function: {cfg.function_name}")
    print(f"Entry Block: {cfg.entry_block}")
    print(f"Total Blocks: {len(cfg.basic_blocks)}")
    
    # Count different types of blocks
    entry_blocks = sum(1 for block in cfg.basic_blocks.values() if block.is_entry_block)
    exit_blocks = sum(1 for block in cfg.basic_blocks.values() if block.is_exit_block)
    unreachable_blocks = sum(1 for block in cfg.basic_blocks.values() if block.is_unreachable)
    
    print(f"Entry Blocks: {entry_blocks}")
    print(f"Exit Blocks: {exit_blocks}")
    print(f"Unreachable Blocks: {unreachable_blocks}")
    
    # Detect loops and back edges
    loops = cfg.get_loops()
    back_edges = cfg.detect_back_edges()
    print(f"Detected Loops: {len(loops)}")
    print(f"Back Edges (Loop Edges): {len(back_edges)}")
    
    if back_edges:
        print("Loop Edges (colored RED in DOT output):")
        for from_block, to_block in sorted(back_edges):
            print(f"  {from_block} -> {to_block}")
    
    print("\nBasic Blocks:")
    for label, block in cfg.basic_blocks.items():
        terminator = block.terminator
        term_info = ""
        if terminator:
            term_info = f" (terminator: {terminator.opcode})"
            if terminator.jump_targets:
                term_info += f" -> {', '.join(terminator.jump_targets)}"
        
        # Add unreachable marker
        unreachable_marker = " [UNREACHABLE]" if block.is_unreachable else ""
        
        print(f"  {label}: lines {block.start_line}-{block.end_line}, "
              f"{len(block.instructions)} instructions{term_info}{unreachable_marker}")
        print(f"    Predecessors: {list(block.predecessors)}")
        print(f"    Successors: {list(block.successors)}")
        print(f"    Color: {block.background_color}")


def print_cfg_detailed(cfg: ControlFlowGraph):
    """Print detailed CFG information including all instructions"""
    print(f"=== Detailed CFG for Function: {cfg.function_name} ===")
    print(f"Entry Block: {cfg.entry_block}")
    print(f"Total Blocks: {len(cfg.basic_blocks)}")
    
    # Count different types of blocks
    unreachable_blocks = sum(1 for block in cfg.basic_blocks.values() if block.is_unreachable)
    print(f"Unreachable Blocks: {unreachable_blocks}")
    
    # Detect loops
    loops = cfg.get_loops()
    print(f"Detected Loops: {len(loops)}")
    if loops:
        for i, loop in enumerate(loops):
            print(f"  Loop {i+1}: {sorted(loop)}")
    
    print("\n" + "="*60)
    
    # Print each basic block with instructions
    for label, block in cfg.basic_blocks.items():
        unreachable_marker = " [UNREACHABLE]" if block.is_unreachable else ""
        print(f"\nBasic Block: {label}{unreachable_marker}")
        print(f"  Lines: {block.start_line}-{block.end_line}")
        print(f"  Predecessors: {sorted(block.predecessors)}")
        print(f"  Successors: {sorted(block.successors)}")
        print(f"  Background Color: {block.background_color}")
        
        if block.is_entry_block:
            print("  Type: ENTRY BLOCK")
        elif block.is_exit_block:
            print("  Type: EXIT BLOCK")
        if block.is_unreachable:
            print("  Type: UNREACHABLE BLOCK")
        
        print(f"  Instructions ({len(block.instructions)}):")
        if not block.instructions:
            print("    (no instructions)")
        else:
            for i, inst in enumerate(block.instructions):
                marker = " *" if inst.is_terminator else "  "
                inst_text = f"{inst.opcode}"
                if inst.operands:
                    inst_text += f" {inst.operands}"
                
                print(f"   {i+1:2d}{marker} {inst_text}")
                
                if inst.is_terminator and inst.jump_targets:
                    print(f"       -> targets: {', '.join(inst.jump_targets)}")
        
        print("-" * 40)


def export_cfg_to_dot(cfg: ControlFlowGraph, output_file: str, include_instructions: bool = True, max_instructions: int = None):
    """Export CFG to DOT format for visualization"""
    # Detect back edges for loop coloring
    back_edges = cfg.detect_back_edges()
    
    with open(output_file, 'w') as f:
        f.write(f'digraph "{cfg.function_name}" {{\n')
        f.write('  rankdir=TB;\n')
        f.write('  node [shape=box, fontname="Consolas", fontsize=10, margin=0.1, labeljust=l];\n')
        f.write('  edge [fontname="Arial", fontsize=9];\n')
        f.write('  graph [bgcolor=white, splines=true, nodesep=0.3, ranksep=0.5];\n\n')
        
        # Write nodes
        for label, block in cfg.basic_blocks.items():
            if include_instructions:
                node_label = _create_detailed_node_label(label, block, max_instructions)
            else:
                node_label = _create_summary_node_label(label, block)
            
            # Enhanced styling based on block type
            style_attrs = _get_node_style(block)
            f.write(f'  "{label}" [label="{node_label}", {style_attrs}];\n')
        
        f.write('\n')
        
        # Write edges with loop edge coloring
        for label, block in cfg.basic_blocks.items():
            for successor in block.successors:
                # Check if this is a back edge (loop edge)
                if (label, successor) in back_edges:
                    # Color back edges red to indicate loops
                    f.write(f'  "{label}" -> "{successor}" [color=red, penwidth=2.5, style=bold, arrowhead=vee];\n')
                else:
                    # Regular edges
                    f.write(f'  "{label}" -> "{successor}" [color=black, penwidth=1.2, arrowhead=normal];\n')
        
        f.write('}\n')


def _get_node_style(block: BasicBlock) -> str:
    """Get DOT styling attributes for a basic block"""
    attrs = []
    
    # Fill color and style
    if block.is_unreachable:
        attrs.extend([
            'style="filled,dashed"',
            'fillcolor=lightgrey',
            'color=grey',
            'penwidth=1'
        ])
    elif block.is_entry_block:
        attrs.extend([
            'style="filled,bold"',
            'fillcolor=lightgreen',
            'color=darkgreen',
            'penwidth=2'
        ])
    elif block.is_exit_block:
        attrs.extend([
            'style="filled,bold"',
            'fillcolor=lightcoral',
            'color=darkred',
            'penwidth=2'
        ])
    else:
        attrs.extend([
            'style=filled',
            'fillcolor=white',
            'color=black',
            'penwidth=1'
        ])
    
    return ', '.join(attrs)


def _create_detailed_node_label(label: str, block: BasicBlock, max_instructions: int = None) -> str:
    """Create a detailed node label including instructions"""
    lines = []
    
    # Enhanced block header with type indicators
    block_title = f"[{label}]"
    if block.is_unreachable:
        block_title += " UNREACHABLE"
    elif block.is_entry_block:
        block_title += " ENTRY"
    elif block.is_exit_block:
        block_title += " EXIT"
    
    lines.append(block_title)
    lines.append(f"Lines: {block.start_line}-{block.end_line}")
    lines.append("=" * max(20, len(block_title)))  # Separator
    
    if not block.instructions:
        lines.append("(no instructions)")
    else:
        instruction_count = len(block.instructions)
        displayed_count = min(instruction_count, max_instructions) if max_instructions else instruction_count
        
        for i, inst in enumerate(block.instructions[:displayed_count]):
            # Format instruction with better visual indicators
            if inst.is_terminator:
                prefix = ">"  # Arrow for terminators
            else:
                prefix = " "
            
            inst_line = f"{inst.opcode}"
            if inst.operands:
                inst_line += f" {inst.operands}"
            
            # Truncate very long instructions but show more characters
            if len(inst_line) > 45:
                inst_line = inst_line[:42] + "..."
            
            # Add terminator marker
            if inst.is_terminator:
                inst_line += " [TERM]"
            
            lines.append(f"{prefix} {inst_line}")
        
        # Show truncation info if needed
        if max_instructions and instruction_count > max_instructions:
            remaining = instruction_count - max_instructions
            lines.append(f"... ({remaining} more instructions)")
    
    # Add control flow info
    if block.instructions and block.terminator and block.terminator.jump_targets:
        targets = ", ".join(block.terminator.jump_targets)
        lines.append(f"-> {targets}")
    
    # Join lines with left-aligned newline markers for GraphViz
    escaped_lines = []
    for line in lines:
        # Escape quotes and backslashes, then add left-alignment marker
        escaped = line.replace('\\', '\\\\').replace('"', '\\"')
        escaped_lines.append(escaped)
    
    return "\\l".join(escaped_lines) + "\\l"


def _create_summary_node_label(label: str, block: BasicBlock) -> str:
    """Create a summary node label without detailed instructions"""
    lines = []
    
    # Block name with type indicator
    block_title = f"Block: {label}"
    if block.is_unreachable:
        block_title += " [UNREACHABLE]"
    elif block.is_entry_block:
        block_title += " [ENTRY]"
    elif block.is_exit_block:
        block_title += " [EXIT]"
    
    lines.append(block_title)
    lines.append("-" * max(15, len(block_title)))
    lines.append(f"Lines: {block.start_line}-{block.end_line}")
    lines.append(f"Instructions: {len(block.instructions)}")
    
    if block.instructions and block.terminator:
        lines.append(f"Terminator: {block.terminator.opcode}")
    
    # Join lines with left-aligned newline markers for GraphViz
    escaped_lines = []
    for line in lines:
        escaped = line.replace('\\', '\\\\').replace('"', '\\"')
        escaped_lines.append(escaped)
    
    return "\\l".join(escaped_lines) + "\\l"
