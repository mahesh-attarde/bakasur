"""
Data flow visualization using Graphviz

Creates visual dependency graphs from assembly analysis.
"""

import graphviz
from typing import List
from .models import Instruction, DataDependency
from .analyzer import DataFlowAnalyzer


class DataFlowVisualizer:
    """Creates visual representations of data flow"""
    
    def __init__(self):
        self.analyzer = DataFlowAnalyzer()
    
    def create_dependency_graph(self, assembly_text: str, output_file: str = "dataflow", 
                              enhanced: bool = True) -> str:
        """
        Create a visual dependency graph from assembly code with enhanced styling
        
        Args:
            assembly_text: Assembly code as string
            output_file: Output file name (without extension)
            enhanced: Use enhanced styling for better comprehension
            
        Returns:
            Path to generated SVG file
        """
        # Parse instructions
        instructions = self.analyzer.parse_basic_block(assembly_text)
        
        if not instructions:
            raise ValueError("No valid instructions found in assembly text")
        
        # Find dependencies
        dependencies = self.analyzer.find_dependencies(instructions)
        
        # Create Graphviz graph
        dot = graphviz.Digraph(comment='Enhanced Data Flow Dependencies')
        
        if enhanced:
            # Enhanced styling for better comprehension
            dot.attr(rankdir='TB', splines='curved', concentrate='true')
            dot.attr('graph', 
                    bgcolor='#f8f9fa',
                    fontname='Arial, sans-serif',
                    fontsize='14',
                    label='Data Flow Dependencies\\n(Enhanced View)',
                    labelloc='t',
                    pad='0.5')
            dot.attr('node', 
                    shape='box', 
                    style='rounded,filled,shadow',
                    fontname='Consolas, monospace',
                    fontsize='12',
                    margin='0.3,0.2')
            dot.attr('edge',
                    fontname='Arial, sans-serif',
                    fontsize='10',
                    arrowhead='vee',
                    arrowsize='0.8')
        else:
            # Original styling
            dot.attr(rankdir='TB', splines='ortho')
            dot.attr('node', shape='box', style='rounded,filled', fontname='Courier')
        
        # Add instruction nodes with enhanced styling
        for i, instruction in enumerate(instructions):
            if enhanced:
                # Create more informative and visually appealing labels
                opcode = instruction.opcode
                operands_str = ', '.join(instruction.operands[:2])
                if len(instruction.operands) > 2:
                    operands_str += f", (+{len(instruction.operands)-2} more)"
                
                label = f"Line {i}\\n{opcode}\\n{operands_str}"
                
                # Enhanced color scheme based on instruction characteristics
                if instruction.opcode in self.analyzer.read_write_instructions:
                    color = '#e3f2fd'  # Light blue for RMW
                    border_color = '#1976d2'
                elif any(op.startswith('[') and op.endswith(']') for op in instruction.operands):
                    color = '#fff3e0'  # Light orange for memory ops
                    border_color = '#f57c00'
                elif instruction.opcode in self.analyzer.jump_instructions:
                    color = '#f3e5f5'  # Light purple for control flow
                    border_color = '#7b1fa2'
                elif instruction.opcode.startswith('v'):  # Vector instructions
                    color = '#e8f5e8'  # Light green for SIMD
                    border_color = '#388e3c'
                else:
                    color = '#fafafa'  # Light gray for others
                    border_color = '#616161'
                
                dot.node(str(i), label, 
                        fillcolor=color,
                        color=border_color,
                        penwidth='2')
            else:
                # Original node styling
                label = f"Line {i}\\n{instruction.opcode}"
                if instruction.operands:
                    label += f" {', '.join(instruction.operands[:2])}"
                    if len(instruction.operands) > 2:
                        label += ", ..."
                
                if instruction.opcode in self.analyzer.read_write_instructions:
                    color = 'lightblue'
                elif instruction.opcode in self.analyzer.read_only_instructions:
                    color = 'lightgreen'
                elif instruction.opcode in self.analyzer.jump_instructions:
                    color = 'lightyellow'
                else:
                    color = 'lightgray'
                
                dot.node(str(i), label, fillcolor=color)
        
        # Add dependency edges with enhanced styling
        if enhanced:
            edge_styles = {
                'RAW': {'color': '#d32f2f', 'style': 'solid', 'penwidth': '3', 'weight': '3'},
                'WAR': {'color': '#1976d2', 'style': 'dashed', 'penwidth': '2', 'weight': '2'},
                'WAW': {'color': '#388e3c', 'style': 'dotted', 'penwidth': '2', 'weight': '1'}
            }
            
            # Group dependencies to avoid clutter
            dependency_groups = {}
            for dep in dependencies:
                key = (dep.source_line, dep.target_line, dep.operand_type)
                if key not in dependency_groups:
                    dependency_groups[key] = []
                dependency_groups[key].append(dep)
            
            for (source, target, op_type), deps in dependency_groups.items():
                if len(deps) == 1:
                    dep = deps[0]
                    style = edge_styles[dep.dependency_type]
                    
                    # Enhanced labels with resource type icons
                    resource_icon = "REG" if dep.operand_type == 'register' else "MEM"
                    label = f"{resource_icon} {dep.resource}\\n{dep.dependency_type}"
                    
                    dot.edge(str(source), str(target),
                            label=label,
                            color=style['color'],
                            fontcolor=style['color'],
                            style=style['style'],
                            penwidth=style['penwidth'],
                            weight=style['weight'])
                else:
                    # Multiple dependencies between same instructions
                    dep_types = [d.dependency_type for d in deps]
                    resources = [d.resource for d in deps]
                    
                    # Use the most critical dependency type for styling
                    priority = {'RAW': 3, 'WAW': 2, 'WAR': 1}
                    main_dep_type = max(dep_types, key=lambda x: priority[x])
                    style = edge_styles[main_dep_type]
                    
                    resource_icon = "REG" if deps[0].operand_type == 'register' else "MEM"
                    label = f"{resource_icon} {len(deps)} deps\\n{', '.join(set(dep_types))}"
                    
                    dot.edge(str(source), str(target),
                            label=label,
                            color=style['color'],
                            fontcolor=style['color'],
                            style=style['style'],
                            penwidth=style['penwidth'],
                            weight=style['weight'])
        else:
            # Original edge styling
            edge_colors = {
                'RAW': 'red',
                'WAR': 'blue',
                'WAW': 'green'
            }
            
            for dep in dependencies:
                color = edge_colors.get(dep.dependency_type, 'black')
                label = f"{dep.resource}\\n({dep.dependency_type}-{dep.operand_type})"
                style = 'solid' if dep.operand_type == 'register' else 'dashed'
                
                dot.edge(str(dep.source_line), str(dep.target_line),
                        label=label,
                        color=color,
                        fontcolor=color,
                        fontsize='10',
                        style=style)
        
        # Add enhanced legend
        with dot.subgraph(name='cluster_legend') as legend:
            if enhanced:
                legend.attr(label='Legend', 
                           style='filled,rounded', 
                           color='#e0e0e0',
                           fontname='Arial, sans-serif',
                           fontsize='12')
                
                legend.node('legend_raw', 'RAW\\n(True Dependency)', 
                           color='#d32f2f', fontcolor='#d32f2f', style='filled',
                           fillcolor='#ffebee')
                legend.node('legend_war', 'WAR\\n(Anti Dependency)', 
                           color='#1976d2', fontcolor='#1976d2', style='filled',
                           fillcolor='#e3f2fd')
                legend.node('legend_waw', 'WAW\\n(Output Dependency)', 
                           color='#388e3c', fontcolor='#388e3c', style='filled',
                           fillcolor='#e8f5e8')
                legend.node('legend_reg', 'Register\\n(solid line)', 
                           style='filled', fillcolor='#f5f5f5')
                legend.node('legend_mem', 'Memory\\n(dashed line)', 
                           style='filled,dashed', fillcolor='#f5f5f5')
                
                # Add instruction type legend
                legend.node('legend_rmw', 'RMW Instructions', 
                           fillcolor='#e3f2fd', color='#1976d2', style='filled')
                legend.node('legend_mem_ops', 'Memory Operations', 
                           fillcolor='#fff3e0', color='#f57c00', style='filled')
                legend.node('legend_simd', 'SIMD Instructions', 
                           fillcolor='#e8f5e8', color='#388e3c', style='filled')
            else:
                # Original legend
                legend.attr(label='Legend', style='filled', color='lightgray')
                legend.node('legend_raw', 'RAW\\n(True Dep)', color='red', style='')
                legend.node('legend_war', 'WAR\\n(Anti Dep)', color='blue', style='')
                legend.node('legend_waw', 'WAW\\n(Output Dep)', color='green', style='')
                legend.node('legend_reg', 'Register\\n(solid line)', style='')
                legend.node('legend_mem', 'Memory\\n(dashed line)', style='dashed')
        
        # Render to file
        output_path = dot.render(output_file, format='svg', cleanup=True)
        
        return output_path
    
    def analyze_and_print(self, assembly_text: str, style: str = "enhanced") -> None:
        """Analyze and print dependency information with enhanced visualization options"""
        instructions = self.analyzer.parse_basic_block(assembly_text)
        dependencies = self.analyzer.find_dependencies(instructions)
        
        if style == "enhanced":
            # Use the new enhanced visualization
            from .enhanced_visualizer import EnhancedDataFlowVisualizer, VisualizationStyle
            enhanced_viz = EnhancedDataFlowVisualizer()
            print(enhanced_viz.visualize(instructions, dependencies, VisualizationStyle.FLOW_DIAGRAM))
            return
        elif style == "comprehensive":
            from .enhanced_visualizer import EnhancedDataFlowVisualizer
            enhanced_viz = EnhancedDataFlowVisualizer()
            print(enhanced_viz.create_comprehensive_report(instructions, dependencies))
            return
        
        # Original classic style
        print("=== INSTRUCTIONS ===")
        for i, instruction in enumerate(instructions):
            reads, writes, memory_ops = self.analyzer.analyze_instruction_operands(instruction)
            print(f"Line {i}: {instruction}")
            if reads:
                # Separate register and memory reads
                reg_reads = [r for r in reads if not (r.startswith('[') and r.endswith(']'))]
                mem_reads = [r for r in reads if r.startswith('[') and r.endswith(']')]
                if reg_reads:
                    print(f"  Reads (reg): {', '.join(sorted(reg_reads))}")
                if mem_reads:
                    print(f"  Reads (mem): {', '.join(sorted(mem_reads))}")
            if writes:
                # Separate register and memory writes
                reg_writes = [w for w in writes if not (w.startswith('[') and w.endswith(']'))]
                mem_writes = [w for w in writes if w.startswith('[') and w.endswith(']')]
                if reg_writes:
                    print(f"  Writes (reg): {', '.join(sorted(reg_writes))}")
                if mem_writes:
                    print(f"  Writes (mem): {', '.join(sorted(mem_writes))}")
            if memory_ops:
                print(f"  Memory ops: {', '.join(sorted(memory_ops))}")
            print()
        
        print("=== DEPENDENCIES ===")
        if dependencies:
            for dep in dependencies:
                print(f"{dep}")
        else:
            print("No dependencies found")
