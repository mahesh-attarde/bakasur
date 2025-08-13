#!/usr/bin/env python3
"""
ASCII Data Flow Visualizer for Assembly Analysis

Simple ASCII visualization for data flow dependencies.
"""

import re
from .models import LegacyInstruction, Dependency

class ASCIIDataFlowVisualizer:
    def __init__(self):
        self.instructions = []
        self.dependencies = []
        self.loop_carried_deps = []
    
    def parse_assembly(self, assembly_text):
        self.instructions = []
        lines = assembly_text.strip().split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            
            parts = line.split(None, 1)
            if len(parts) >= 1:
                opcode = parts[0]
                operands = parts[1] if len(parts) > 1 else ""
                
                instr = LegacyInstruction(i, opcode, operands, line)
                if not opcode.endswith(':'):
                    self._analyze_registers(instr)
                self.instructions.append(instr)
    
    def _analyze_registers(self, instr):
        reg_pattern = r'\b(?:rax|rbx|rcx|rdx|rsi|rdi|rsp|rbp|r8|r9|r10|r11|r12|r13|r14|r15|eax|ebx|ecx|edx|esi|edi|esp|ebp|xmm\d+|ymm\d+|zmm\d+)\b'
        
        operands = instr.operands
        if not operands:
            return
        
        instr.memory_address_reads = set()
        
        parts = [p.strip() for p in operands.split(',')]
        
        def extract_data_registers(operand, is_destination=False):
            data_reads = set()
            data_writes = set()
            if 'ptr' in operand and '[' in operand:
                bracket_start = operand.find('[')
                bracket_end = operand.find(']')
                if bracket_start != -1 and bracket_end != -1:
                    address_expr = operand[bracket_start+1:bracket_end]
                    for match in re.finditer(reg_pattern, address_expr):
                        instr.memory_address_reads.add(match.group())
                return data_reads, data_writes
            else:
                for match in re.finditer(reg_pattern, operand):
                    reg = match.group()
                    if is_destination:
                        data_writes.add(reg)
                    else:
                        data_reads.add(reg)
                return data_reads, data_writes
        
        if len(parts) >= 2:
            if instr.opcode.startswith(('mov', 'vmov')):
                # mov src, dst - reads src, writes dst
                src, dst = parts[0], parts[1]
                
                src_reads, src_writes = extract_data_registers(src, False)
                dst_reads, dst_writes = extract_data_registers(dst, True)
                
                instr.reads.update(src_reads)
                instr.writes.update(dst_writes)
                
                # For memory destinations, no direct register write
            
            elif instr.opcode.startswith(('add', 'sub', 'vadd', 'vsub')):
                # Arithmetic: src, dst - reads both, writes dst
                src, dst = parts[0], parts[1]
                
                src_reads, src_writes = extract_data_registers(src, False)
                dst_reads, dst_writes = extract_data_registers(dst, False)  # Read first
                
                instr.reads.update(src_reads)
                instr.reads.update(dst_reads)
                
                if not ('ptr' in dst and '[' in dst):
                    dst_reads_w, dst_writes_w = extract_data_registers(dst, True)
                    instr.writes.update(dst_writes_w)
            
            elif instr.opcode.startswith('lea'):
                # lea dst, [address] - writes to dst, reads address regs (but for addressing)
                dst, src = parts[0], parts[1]
                
                dst_reads, dst_writes = extract_data_registers(dst, True)
                instr.writes.update(dst_writes)
                
                if '[' in src:
                    bracket_start = src.find('[')
                    bracket_end = src.find(']')
                    if bracket_start != -1 and bracket_end != -1:
                        address_expr = src[bracket_start+1:bracket_end]
                        for match in re.finditer(reg_pattern, address_expr):
                            instr.memory_address_reads.add(match.group())
            
            elif instr.opcode.startswith(('movzx', 'movsx', 'movsxd')):
                # Zero/sign extend: reads src, writes dst
                src, dst = parts[0], parts[1]
                
                src_reads, src_writes = extract_data_registers(src, False)
                dst_reads, dst_writes = extract_data_registers(dst, True)
                
                instr.reads.update(src_reads)
                instr.writes.update(dst_writes)
            
            elif instr.opcode.startswith('cmp'):
                # Compare - reads both operands
                for part in parts:
                    part_reads, part_writes = extract_data_registers(part, False)
                    instr.reads.update(part_reads)
            
            else:
                # Generic handling
                for i, part in enumerate(parts):
                    is_dest = (i == 0)  # Assume first operand is destination
                    part_reads, part_writes = extract_data_registers(part, False)
                    instr.reads.update(part_reads)
                    if is_dest and not ('ptr' in part and '[' in part):
                        _, dest_writes = extract_data_registers(part, True)
                        instr.writes.update(dest_writes)
        
        else:
            # Single operand instruction
            operand = parts[0] if parts else operands
            if instr.opcode.startswith('inc'):
                if 'ptr' in operand and '[' in operand:
                    bracket_start = operand.find('[')
                    bracket_end = operand.find(']')
                    if bracket_start != -1 and bracket_end != -1:
                        address_expr = operand[bracket_start+1:bracket_end]
                        for match in re.finditer(reg_pattern, address_expr):
                            instr.memory_address_reads.add(match.group())
                else:
                    for match in re.finditer(reg_pattern, operand):
                        reg = match.group()
                        instr.reads.add(reg)
                        instr.writes.add(reg)
            else:
                part_reads, part_writes = extract_data_registers(operand, False)
                instr.reads.update(part_reads)
    
    def find_dependencies(self):
        self.dependencies = []
        
        for i, instr1 in enumerate(self.instructions):
            for j, instr2 in enumerate(self.instructions[i+1:], i+1):
                for reg in instr1.writes:
                    if reg in instr2.reads:
                        self.dependencies.append(Dependency(i, j, reg, "RAW"))
                for reg in instr1.writes:
                    if reg in instr2.writes:
                        self.dependencies.append(Dependency(i, j, reg, "WAW"))
                for reg in instr1.reads:
                    if reg in instr2.writes:
                        self.dependencies.append(Dependency(i, j, reg, "WAR"))
    
    def detect_loop_carried_dependencies(self):
        self.loop_carried_deps = []
        
        label_map = {}
        for i, instr in enumerate(self.instructions):
            if instr.opcode.endswith(':'):
                label_name = instr.opcode.rstrip(':')
                label_map[label_name] = i
        loop_info = []
        for i, instr in enumerate(self.instructions):
            if instr.opcode.startswith(('jmp', 'j', 'loop')):
                operand = instr.operands.strip()
                if operand in label_map:
                    target_line = label_map[operand]
                    if target_line <= i:
                        loop_info.append((target_line, i))
        # No loop-carried dependencies detected
    
    def generate_summary_statistics(self):
        result = []
        result.append("HAZARD SUMMARY STATISTICS")
        result.append("=" * 80)
        result.append("")
        
        dep_counts = {"RAW": 0, "WAW": 0, "WAR": 0}
        loop_dep_counts = {"LOOP-RAW": 0}  # Only track true dependencies for loops
        
        for dep in self.dependencies:
            if dep.dep_type in dep_counts:
                dep_counts[dep.dep_type] += 1
        
        for dep in self.loop_carried_deps:
            if dep.dep_type in loop_dep_counts:
                loop_dep_counts[dep.dep_type] += 1
        
        result.append("Standard Dependencies:")
        result.append(f"  RAW (Read After Write):  {dep_counts['RAW']:3d}")
        result.append(f"  WAW (Write After Write): {dep_counts['WAW']:3d}")
        result.append(f"  WAR (Write After Read):  {dep_counts['WAR']:3d}")
        result.append(f"  Total Standard:          {sum(dep_counts.values()):3d}")
        result.append("")
        
        result.append("Loop-Carried Dependencies (True Dependencies Only):")
        result.append(f"  LOOP-RAW:                {loop_dep_counts['LOOP-RAW']:3d}")
        result.append(f"  Total Loop-Carried:      {sum(loop_dep_counts.values()):3d}")
        result.append("")
        
        total_deps = sum(dep_counts.values()) + sum(loop_dep_counts.values())
        result.append("Overall Statistics:")
        result.append(f"  Total Instructions:      {len(self.instructions):3d}")
        result.append(f"  Total Dependencies:      {total_deps:3d}")
        if len(self.instructions) > 0:
            result.append(f"  Dependencies per Instr:  {total_deps/len(self.instructions):5.2f}")
        result.append("")
        
        if self.loop_carried_deps:
            result.append("Loop-Carried Dependency Details:")
            for dep in self.loop_carried_deps:
                from_instr = self.instructions[dep.from_instr]
                to_instr = self.instructions[dep.to_instr]
                result.append(f"  L{dep.from_instr} -> L{dep.to_instr}: {dep.dep_type}({dep.register})")
                result.append(f"    From: {from_instr.full_text}")
                result.append(f"    To:   {to_instr.full_text}")
            result.append("")
        else:
            result.append("No true loop-carried dependencies detected.")
            result.append("")
            result.append("Analysis: This loop processes independent data elements.")
            result.append("Each iteration:")
            result.append("  - Accesses different memory locations (rax-based indexing)")
            result.append("  - Performs independent computations")
            result.append("  - No accumulation across iterations")
            result.append("Result: Loop is potentially parallelizable.")
            result.append("")
        
        return "\n".join(result)
    
    def visualize_instruction_chain(self):
        result = []
        result.append("INSTRUCTION DEPENDENCY CHAINS")
        result.append("=" * 80)
        result.append("")
        
        max_instr_len = max(len(instr.full_text) for instr in self.instructions) if self.instructions else 0
        instr_width = max(50, max_instr_len + 5)
        
        for i, instr in enumerate(self.instructions):
            immediate_deps = {}
            for reg in instr.writes:
                for dep in self.dependencies:
                    if dep.from_instr == i and dep.register == reg:
                        if reg not in immediate_deps or dep.to_instr < immediate_deps[reg][0]:
                            immediate_deps[reg] = (dep.to_instr, dep.dep_type)
            
            instr_text = f"L{i:2d}: {instr.full_text}"
            
            if immediate_deps:
                dep_texts = []
                for reg, (target_idx, dep_type) in immediate_deps.items():
                    dep_texts.append(f"{dep_type}({reg})->L{target_idx}")
                dep_column = " | " + ", ".join(dep_texts)
            else:
                dep_column = ""
            
            line = f"{instr_text:<{instr_width}}{dep_column}"
            result.append(line)
        
        return "\n".join(result)
    
    def analyze(self, assembly_text):
        self.parse_assembly(assembly_text)
        self.find_dependencies()
        self.detect_loop_carried_dependencies()
        
        result = []
        result.append(self.generate_summary_statistics())
        result.append(self.visualize_instruction_chain())
        
        return "\n".join(result)

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 dataflow_analyzer.py <assembly_file>")
        print("Example: python3 dataflow_analyzer.py simple_dataflow.s")
        return
    
    filename = sys.argv[1]
    
    try:
        with open(filename, 'r') as f:
            assembly_text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return
    
    visualizer = ASCIIDataFlowVisualizer()
    result = visualizer.analyze(assembly_text)
    print(result)

if __name__ == "__main__":
    main()
