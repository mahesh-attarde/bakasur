#!/usr/bin/env python3
"""
Data Flow Visualizer for Assembly Basic Blocks

Creates visual representations of data flow dependencies within assembly basic blocks.
Shows register and memory dependencies between instructions.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import graphviz
from pathlib import Path


@dataclass
class Instruction:
    """Represents a single assembly instruction with its operands"""
    line_num: int
    label: Optional[str]
    opcode: str
    operands: List[str]
    raw_line: str
    
    def __str__(self):
        prefix = f"{self.label}:\n" if self.label else ""
        return f"{prefix}{self.opcode} {', '.join(self.operands)}"


@dataclass
class DataDependency:
    """Represents a data dependency between instructions"""
    source_line: int
    target_line: int
    resource: str  # register name or memory location
    dependency_type: str  # 'RAW', 'WAR', 'WAW'
    operand_type: str  # 'register' or 'memory'
    
    def __str__(self):
        return f"Line {self.source_line} -> Line {self.target_line} ({self.resource}, {self.dependency_type}, {self.operand_type})"


class IntelAssemblyParser:
    """Parser for Intel syntax assembly instructions"""
    
    def __init__(self):
        # Intel x86-64 registers
        self.registers = {
            # 64-bit registers
            'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp',
            'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15',
            # 32-bit registers
            'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp',
            'r8d', 'r9d', 'r10d', 'r11d', 'r12d', 'r13d', 'r14d', 'r15d',
            # 16-bit registers
            'ax', 'bx', 'cx', 'dx', 'si', 'di', 'bp', 'sp',
            'r8w', 'r9w', 'r10w', 'r11w', 'r12w', 'r13w', 'r14w', 'r15w',
            # 8-bit registers
            'al', 'bl', 'cl', 'dl', 'sil', 'dil', 'bpl', 'spl',
            'ah', 'bh', 'ch', 'dh',
            'r8b', 'r9b', 'r10b', 'r11b', 'r12b', 'r13b', 'r14b', 'r15b',
            # SIMD registers (XMM, YMM, ZMM)
            'xmm0', 'xmm1', 'xmm2', 'xmm3', 'xmm4', 'xmm5', 'xmm6', 'xmm7',
            'xmm8', 'xmm9', 'xmm10', 'xmm11', 'xmm12', 'xmm13', 'xmm14', 'xmm15',
            'xmm16', 'xmm17', 'xmm18', 'xmm19', 'xmm20', 'xmm21', 'xmm22', 'xmm23',
            'xmm24', 'xmm25', 'xmm26', 'xmm27', 'xmm28', 'xmm29', 'xmm30', 'xmm31',
            'ymm0', 'ymm1', 'ymm2', 'ymm3', 'ymm4', 'ymm5', 'ymm6', 'ymm7',
            'ymm8', 'ymm9', 'ymm10', 'ymm11', 'ymm12', 'ymm13', 'ymm14', 'ymm15',
            'ymm16', 'ymm17', 'ymm18', 'ymm19', 'ymm20', 'ymm21', 'ymm22', 'ymm23',
            'ymm24', 'ymm25', 'ymm26', 'ymm27', 'ymm28', 'ymm29', 'ymm30', 'ymm31',
            'zmm0', 'zmm1', 'zmm2', 'zmm3', 'zmm4', 'zmm5', 'zmm6', 'zmm7',
            'zmm8', 'zmm9', 'zmm10', 'zmm11', 'zmm12', 'zmm13', 'zmm14', 'zmm15',
            'zmm16', 'zmm17', 'zmm18', 'zmm19', 'zmm20', 'zmm21', 'zmm22', 'zmm23',
            'zmm24', 'zmm25', 'zmm26', 'zmm27', 'zmm28', 'zmm29', 'zmm30', 'zmm31',
            # AVX-512 mask registers
            'k0', 'k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'k7'
        }
        
        # Register aliases (same physical register)
        self.register_aliases = {
            # General purpose registers
            'rax': {'rax', 'eax', 'ax', 'al', 'ah'},
            'rbx': {'rbx', 'ebx', 'bx', 'bl', 'bh'},
            'rcx': {'rcx', 'ecx', 'cx', 'cl', 'ch'},
            'rdx': {'rdx', 'edx', 'dx', 'dl', 'dh'},
            'rsi': {'rsi', 'esi', 'si', 'sil'},
            'rdi': {'rdi', 'edi', 'di', 'dil'},
            'rbp': {'rbp', 'ebp', 'bp', 'bpl'},
            'rsp': {'rsp', 'esp', 'sp', 'spl'},
            'r8': {'r8', 'r8d', 'r8w', 'r8b'},
            'r9': {'r9', 'r9d', 'r9w', 'r9b'},
            'r10': {'r10', 'r10d', 'r10w', 'r10b'},
            'r11': {'r11', 'r11d', 'r11w', 'r11b'},
            'r12': {'r12', 'r12d', 'r12w', 'r12b'},
            'r13': {'r13', 'r13d', 'r13w', 'r13b'},
            'r14': {'r14', 'r14d', 'r14w', 'r14b'},
            'r15': {'r15', 'r15d', 'r15w', 'r15b'},
        }
        
        # SIMD register aliases (XMM/YMM/ZMM share the same physical register)
        for i in range(32):
            base_name = f'zmm{i}'
            self.register_aliases[base_name] = {f'zmm{i}', f'ymm{i}', f'xmm{i}'}
        
        # Mask register aliases (k0-k7 are independent registers)
        for i in range(8):
            mask_name = f'k{i}'
            self.register_aliases[mask_name] = {mask_name}
    
    def normalize_register(self, reg: str) -> str:
        """Normalize register name to its base form"""
        reg = reg.lower()
        
        # For general purpose registers, normalize to 64-bit form
        for base_reg, aliases in self.register_aliases.items():
            if reg in aliases and base_reg.startswith('r'):
                return base_reg
        
        # For SIMD registers, normalize to ZMM form (largest)
        for base_reg, aliases in self.register_aliases.items():
            if reg in aliases and base_reg.startswith('zmm'):
                return base_reg
        
        # For mask registers, return as-is (k0-k7)
        for base_reg, aliases in self.register_aliases.items():
            if reg in aliases and base_reg.startswith('k'):
                return base_reg
                
        # If not found in aliases, return as-is
        return reg
    
    def parse_operand(self, operand: str) -> Tuple[Set[str], Set[str], Optional[str]]:
        """
        Parse an operand and return (reads, writes, memory_location)
        
        Returns:
            reads: Set of registers read
            writes: Set of registers written
            memory_location: Memory location if applicable
        """
        operand = operand.strip()
        reads = set()
        writes = set()
        memory_location = None
        
        # Handle memory operands: [base + index*scale + displacement]
        memory_pattern = r'\[([^\]]+)\]'
        memory_match = re.search(memory_pattern, operand)
        
        if memory_match:
            memory_expr = memory_match.group(1)
            memory_location = f"[{memory_expr}]"
            
            # Extract registers from memory expression
            # Pattern for register names in memory expressions
            reg_pattern = r'\b(' + '|'.join(self.registers) + r')\b'
            reg_matches = re.findall(reg_pattern, memory_expr, re.IGNORECASE)
            
            for reg in reg_matches:
                reads.add(self.normalize_register(reg))
            
            # Handle AVX-512 mask operands that might appear after memory operands
            # e.g., "zmmword ptr [rax]{k1}" 
            mask_pattern = r'\{(k[0-7])\}'
            mask_matches = re.findall(mask_pattern, operand, re.IGNORECASE)
            for mask in mask_matches:
                reads.add(self.normalize_register(mask))
        
        # Handle direct register operands
        else:
            # Handle AVX-512 mask operands like {k1}, {k1}{z}
            mask_pattern = r'\{(k[0-7])\}'
            mask_matches = re.findall(mask_pattern, operand, re.IGNORECASE)
            for mask in mask_matches:
                reads.add(self.normalize_register(mask))
            
            # Handle regular register operands
            reg_pattern = r'\b(' + '|'.join(self.registers) + r')\b'
            reg_matches = re.findall(reg_pattern, operand, re.IGNORECASE)
            
            for reg in reg_matches:
                reads.add(self.normalize_register(reg))
        
        return reads, writes, memory_location
    
    def parse_instruction(self, line: str, line_num: int) -> Optional[Instruction]:
        """Parse a single assembly instruction line"""
        line = line.strip()
        if not line or line.startswith('#') or line.startswith(';'):
            return None
        
        # Check for label
        label = None
        if ':' in line and not line.startswith('\t') and not line.startswith(' '):
            parts = line.split(':', 1)
            if len(parts) == 2:
                label = parts[0].strip()
                line = parts[1].strip()
                if not line:  # Label-only line
                    return Instruction(line_num, label, '', [], line)
        
        # Parse instruction
        parts = line.split(None, 1)
        if not parts:
            return None
        
        opcode = parts[0].lower()
        operands = []
        
        if len(parts) > 1:
            # Split operands by comma, but handle nested brackets
            operand_str = parts[1]
            operands = self._split_operands(operand_str)
        
        return Instruction(line_num, label, opcode, operands, line)
    
    def _split_operands(self, operand_str: str) -> List[str]:
        """Split operands by comma, handling nested brackets"""
        operands = []
        current = ""
        bracket_depth = 0
        
        for char in operand_str:
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ',' and bracket_depth == 0:
                operands.append(current.strip())
                current = ""
                continue
            
            current += char
        
        if current.strip():
            operands.append(current.strip())
        
        return operands


class DataFlowAnalyzer:
    """Analyzes data flow dependencies in assembly basic blocks"""
    
    def __init__(self):
        self.parser = IntelAssemblyParser()
        
        # Instruction classifications
        self.read_write_instructions = {
            'mov', 'movss', 'movsd', 'movd', 'movq', 'movups', 'movaps',
            'add', 'sub', 'mul', 'div', 'imul', 'idiv',
            'and', 'or', 'xor', 'not', 'shl', 'shr', 'sar',
            'inc', 'dec', 'neg', 'shld', 'shrd',
            # AVX/AVX2/AVX-512 instructions
            'vmovss', 'vmovsd', 'vmovd', 'vmovq', 'vmovups', 'vmovaps', 'vmovapd',
            'vmovdqu', 'vmovdqa', 'vmovhps', 'vmovlps', 'vmovhpd', 'vmovlpd',
            'vaddss', 'vsubss', 'vmulss', 'vdivss',
            'vaddps', 'vsubps', 'vmulps', 'vdivps',
            'vaddpd', 'vsubpd', 'vmulpd', 'vdivpd',
            'vextractf128', 'vinsertf128', 'vextractf32x4', 'vinsertf32x4',
            'vextractf64x2', 'vinsertf64x2', 'vextractf32x8', 'vinsertf32x8',
            'vextractf64x4', 'vinsertf64x4',
            # FMA instructions (three-operand)
            'vfmadd132ss', 'vfmadd213ss', 'vfmadd231ss',
            'vfmadd132ps', 'vfmadd213ps', 'vfmadd231ps',
            'vfmadd132pd', 'vfmadd213pd', 'vfmadd231pd',
            'vfmsub132ss', 'vfmsub213ss', 'vfmsub231ss',
            'vfnmadd132ss', 'vfnmadd213ss', 'vfnmadd231ss',
            'vfnmsub132ss', 'vfnmsub213ss', 'vfnmsub231ss',
            # Blend and permutation instructions
            'vblendps', 'vblendpd', 'vblendvps', 'vblendvpd',
            'vpermilps', 'vpermilpd', 'vperm2f128',
            # Conditional moves (three-operand in some cases)
            'cmovne', 'cmove', 'cmovl', 'cmovle', 'cmovg', 'cmovge',
            'cmova', 'cmovae', 'cmovb', 'cmovbe', 'cmovo', 'cmovno',
            'cmovs', 'cmovns', 'cmovp', 'cmovnp',
            # Packed multiply-add
            'vpmadd52luq', 'vpmadd52huq',
            # AVX-512 mask operations
            'vpcmpeqb', 'vpcmpeqw', 'vpcmpeqd', 'vpcmpeqq',
            'vpcmpgtb', 'vpcmpgtw', 'vpcmpgtd', 'vpcmpgtq',
            'vpcmpltb', 'vpcmpltw', 'vpcmpltd', 'vpcmpltq',
            'vpcmpneb', 'vpcmpnew', 'vpcmpned', 'vpcmpneq',
            'kandw', 'kandb', 'kandq', 'kandnw', 'kandnb', 'kandnq',
            'korw', 'korb', 'korq', 'kxorw', 'kxorb', 'kxorq',
            'knotw', 'knotb', 'knotq', 'ktestw', 'ktestb', 'ktestq',
            'kshiftlw', 'kshiftlb', 'kshiftlq', 'kshiftrw', 'kshiftrb', 'kshiftrq',
            # Gather/scatter instructions 
            'vpgatherdd', 'vpgatherqd', 'vpgatherdq', 'vpgatherqq',
            'vpscatterdd', 'vpscatterqd', 'vpscatterdq', 'vpscatterqq',
            'vgatherdps', 'vgatherqps', 'vgatherdpd', 'vgatherqpd',
            'vscatterdps', 'vscatterqps', 'vscatterdpd', 'vscatterqpd',
            # Other common SIMD instructions
            'movdqu', 'movdqa', 'movhps', 'movlps', 'movhpd', 'movlpd',
            'addss', 'subss', 'mulss', 'divss',
            'addps', 'subps', 'mulps', 'divps',
            'addpd', 'subpd', 'mulpd', 'divpd'
        }
        
        self.read_only_instructions = {
            'cmp', 'test', 'bt', 'bts', 'btr', 'btc'
        }
        
        self.jump_instructions = {
            'jmp', 'je', 'jne', 'jz', 'jnz', 'jl', 'jle', 'jg', 'jge',
            'ja', 'jae', 'jb', 'jbe', 'js', 'jns', 'jo', 'jno',
            'jc', 'jnc', 'jp', 'jnp'
        }
    
    def analyze_instruction_operands(self, instruction: Instruction) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Analyze instruction operands to determine reads and writes
        
        Returns:
            reads: Set of registers/memory read
            writes: Set of registers/memory written
            memory_ops: Set of memory operations
        """
        reads = set()
        writes = set()
        memory_ops = set()
        
        if not instruction.operands:
            return reads, writes, memory_ops
        
        opcode = instruction.opcode.lower()
        
        # Special case for LEA - doesn't access memory, only calculates address
        if opcode == 'lea':
            # LEA only reads the address calculation registers, writes to destination
            # It does NOT access memory, only calculates the effective address
            if len(instruction.operands) >= 2:
                dest_reads, _, _ = self.parser.parse_operand(instruction.operands[0])
                writes.update(dest_reads)
                
                # For LEA, extract only the registers from the memory expression
                # Don't treat it as a memory access
                src_operand = instruction.operands[1]
                if '[' in src_operand and ']' in src_operand:
                    # Extract register names from memory expression without treating as memory access
                    memory_expr = re.search(r'\[([^\]]+)\]', src_operand)
                    if memory_expr:
                        expr_content = memory_expr.group(1)
                        # Find register names in the expression
                        reg_pattern = r'\b(' + '|'.join(self.parser.registers) + r')\b'
                        reg_matches = re.findall(reg_pattern, expr_content, re.IGNORECASE)
                        for reg in reg_matches:
                            reads.add(self.parser.normalize_register(reg))
                else:
                    # Handle non-memory source operands
                    src_reads, _, _ = self.parser.parse_operand(src_operand)
                    reads.update(src_reads)
        
        # Handle different instruction types
        elif opcode in self.read_write_instructions:
            # Special handling for mask comparison instructions - they write to destination without reading it first
            if opcode.startswith(('vpcmp', 'kand', 'kor', 'kxor', 'knot')):
                # Mask-generating/manipulating instructions: first operand is destination (write-only), rest are sources
                if instruction.operands:
                    # Destination operand (write-only)
                    dest_reads, dest_writes, dest_mem = self.parser.parse_operand(instruction.operands[0])
                    
                    if dest_mem:
                        memory_ops.add(dest_mem)
                        reads.update(dest_reads)  # Memory address calculation
                        writes.add(dest_mem)      # Memory write
                    else:
                        # For destination operands, separate main register writes from mask register reads
                        dest_operand = instruction.operands[0]
                        
                        # Extract mask registers (these are reads even in destination operands)
                        mask_pattern = r'\{(k[0-7])\}'
                        mask_matches = re.findall(mask_pattern, dest_operand, re.IGNORECASE)
                        for mask in mask_matches:
                            reads.add(self.parser.normalize_register(mask))
                        
                        # Extract main registers (these are writes for destination)
                        # Remove mask syntax to get the main register
                        clean_operand = re.sub(r'\{[^}]+\}', '', dest_operand)
                        main_reads, main_writes, main_mem = self.parser.parse_operand(clean_operand)
                        writes.update(main_reads)  # Main register is written to
                    
                    # Source operands (read-only)
                    for operand in instruction.operands[1:]:
                        src_reads, src_writes, src_mem = self.parser.parse_operand(operand)
                        reads.update(src_reads)
                        if src_mem:
                            memory_ops.add(src_mem)
                            reads.add(src_mem)
            else:
                # Regular read-write instructions
                # First operand is usually destination (write), rest are source (read)
                if instruction.operands:
                    # Destination operand
                    dest_reads, dest_writes, dest_mem = self.parser.parse_operand(instruction.operands[0])
                    
                    if dest_mem:
                        memory_ops.add(dest_mem)
                        reads.update(dest_reads)  # Memory address calculation
                        writes.add(dest_mem)      # Memory write
                    else:
                        # For destination operands, separate main register writes from mask register reads
                        dest_operand = instruction.operands[0]
                        
                        # Extract mask registers (these are reads even in destination operands)
                        mask_pattern = r'\{(k[0-7])\}'
                        mask_matches = re.findall(mask_pattern, dest_operand, re.IGNORECASE)
                        for mask in mask_matches:
                            reads.add(self.parser.normalize_register(mask))
                        
                        # Extract main registers (these are writes for destination)
                        # Remove mask syntax to get the main register
                        clean_operand = re.sub(r'\{[^}]+\}', '', dest_operand)
                        main_reads, main_writes, main_mem = self.parser.parse_operand(clean_operand)
                        writes.update(main_reads)  # Main register is written to
                    
                    # Source operands
                    for operand in instruction.operands[1:]:
                        src_reads, src_writes, src_mem = self.parser.parse_operand(operand)
                        reads.update(src_reads)
                        if src_mem:
                            memory_ops.add(src_mem)
                            reads.add(src_mem)
                    
                    # Handle read-modify-write instructions (destination is also read)
                    if opcode in {'add', 'sub', 'and', 'or', 'xor', 'shld', 'shrd', 
                                 'vfmadd132ss', 'vfmadd213ss', 'vfmadd231ss',
                                 'vfmadd132ps', 'vfmadd213ps', 'vfmadd231ps',
                                 'vfmadd132pd', 'vfmadd213pd', 'vfmadd231pd',
                                 'vfmsub132ss', 'vfmsub213ss', 'vfmsub231ss',
                                 'vfnmadd132ss', 'vfnmadd213ss', 'vfnmadd231ss',
                                 'vfnmsub132ss', 'vfnmsub213ss', 'vfnmsub231ss',
                                 'vpmadd52luq', 'vpmadd52huq'}:
                        # Destination is also read in these instructions
                        if dest_mem:
                            reads.add(dest_mem)  # Memory location is read before being written
                        else:
                            reads.update(dest_reads)  # Register is read before being written
                        # Destination is also read in these instructions
                        if dest_mem:
                            reads.add(dest_mem)  # Memory location is read before being written
                        else:
                            reads.update(dest_reads)  # Register is read before being written
        
        elif opcode in self.read_only_instructions:
            # All operands are read
            for operand in instruction.operands:
                op_reads, op_writes, op_mem = self.parser.parse_operand(operand)
                reads.update(op_reads)
                if op_mem:
                    memory_ops.add(op_mem)
                    reads.add(op_mem)
        
        elif opcode in self.jump_instructions:
            # Jump instructions typically read their operands
            for operand in instruction.operands:
                op_reads, op_writes, op_mem = self.parser.parse_operand(operand)
                reads.update(op_reads)
        
        return reads, writes, memory_ops
    
    def find_dependencies(self, instructions: List[Instruction]) -> List[DataDependency]:
        """Find data dependencies between instructions"""
        dependencies = []
        
        # Track last writer for each resource
        last_writer = {}  # resource -> instruction_index
        
        def classify_operand_type(resource: str) -> str:
            """Classify if a resource is a register or memory operand"""
            # Check if resource contains memory bracket notation
            if '[' in resource and ']' in resource:
                return 'memory'
            else:
                return 'register'
        
        for i, instruction in enumerate(instructions):
            reads, writes, memory_ops = self.analyze_instruction_operands(instruction)
            
            # Check for Read-After-Write (RAW) dependencies
            for resource in reads:
                if resource in last_writer:
                    dep = DataDependency(
                        source_line=last_writer[resource],
                        target_line=i,
                        resource=resource,
                        dependency_type='RAW',
                        operand_type=classify_operand_type(resource)
                    )
                    dependencies.append(dep)
            
            # Check for Write-After-Read (WAR) and Write-After-Write (WAW)
            for resource in writes:
                # Find all previous instructions that read this resource (WAR)
                for j in range(i):
                    prev_reads, prev_writes, prev_memory = self.analyze_instruction_operands(instructions[j])
                    if resource in prev_reads and j > last_writer.get(resource, -1):
                        dep = DataDependency(
                            source_line=j,
                            target_line=i,
                            resource=resource,
                            dependency_type='WAR',
                            operand_type=classify_operand_type(resource)
                        )
                        dependencies.append(dep)
                
                # Check for WAW
                if resource in last_writer:
                    dep = DataDependency(
                        source_line=last_writer[resource],
                        target_line=i,
                        resource=resource,
                        dependency_type='WAW',
                        operand_type=classify_operand_type(resource)
                    )
                    dependencies.append(dep)
                
                # Update last writer
                last_writer[resource] = i
        
        return dependencies
    
    def parse_basic_block(self, assembly_text: str) -> List[Instruction]:
        """Parse assembly text into instructions"""
        instructions = []
        lines = assembly_text.strip().split('\n')
        
        for i, line in enumerate(lines):
            instruction = self.parser.parse_instruction(line, i)
            if instruction and instruction.opcode:  # Skip empty lines and label-only lines
                instructions.append(instruction)
        
        return instructions


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
                    resource_icon = "📋" if dep.operand_type == 'register' else "💾"
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
                    
                    resource_icon = "📋" if deps[0].operand_type == 'register' else "💾"
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
                legend.attr(label='🔍 Legend', 
                           style='filled,rounded', 
                           color='#e0e0e0',
                           fontname='Arial, sans-serif',
                           fontsize='12')
                
                legend.node('legend_raw', '🔴 RAW\\n(True Dependency)', 
                           color='#d32f2f', fontcolor='#d32f2f', style='filled',
                           fillcolor='#ffebee')
                legend.node('legend_war', '🔵 WAR\\n(Anti Dependency)', 
                           color='#1976d2', fontcolor='#1976d2', style='filled',
                           fillcolor='#e3f2fd')
                legend.node('legend_waw', '🟢 WAW\\n(Output Dependency)', 
                           color='#388e3c', fontcolor='#388e3c', style='filled',
                           fillcolor='#e8f5e8')
                legend.node('legend_reg', '📋 Register\\n(solid line)', 
                           style='filled', fillcolor='#f5f5f5')
                legend.node('legend_mem', '💾 Memory\\n(dashed line)', 
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
            from enhanced_dataflow_visualizer import EnhancedDataFlowVisualizer, VisualizationStyle
            enhanced_viz = EnhancedDataFlowVisualizer()
            print(enhanced_viz.visualize(instructions, dependencies, VisualizationStyle.FLOW_DIAGRAM))
            return
        elif style == "timeline":
            from enhanced_dataflow_visualizer import EnhancedDataFlowVisualizer, VisualizationStyle  
            enhanced_viz = EnhancedDataFlowVisualizer()
            print(enhanced_viz.visualize(instructions, dependencies, VisualizationStyle.TIMELINE))
            return
        elif style == "lanes":
            from enhanced_dataflow_visualizer import EnhancedDataFlowVisualizer, VisualizationStyle
            enhanced_viz = EnhancedDataFlowVisualizer()
            print(enhanced_viz.visualize(instructions, dependencies, VisualizationStyle.PARALLEL_LANES))
            return
        elif style == "matrix":
            from enhanced_dataflow_visualizer import EnhancedDataFlowVisualizer, VisualizationStyle
            enhanced_viz = EnhancedDataFlowVisualizer()
            print(enhanced_viz.visualize(instructions, dependencies, VisualizationStyle.DEPENDENCY_MATRIX))
            return
        elif style == "pipeline":
            from enhanced_dataflow_visualizer import EnhancedDataFlowVisualizer, VisualizationStyle
            enhanced_viz = EnhancedDataFlowVisualizer()
            print(enhanced_viz.visualize(instructions, dependencies, VisualizationStyle.INSTRUCTION_PIPELINE))
            return
        elif style == "comprehensive":
            from enhanced_dataflow_visualizer import EnhancedDataFlowVisualizer
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
        dependencies = []
        seen_mem_raw = set()
        def normalize_mem(mem):
            # Normalize memory expressions: [rax], [rax+0], [rax + 0], etc.
            import re
            m = re.match(r'\[([a-z0-9]+)([ \+0]*)\]', mem)
            if m:
                return f'[{m.group(1)}]'
            return mem

        for i, instr1 in enumerate(instructions):
            for j, instr2 in enumerate(instructions[i+1:], i+1):
                # Register dependencies
                for reg in instr1.writes:
                    if reg in instr2.reads:
                        dependencies.append(Dependency(i, j, reg, "RAW", "register"))
                for reg in instr1.writes:
                    if reg in instr2.writes:
                        dependencies.append(Dependency(i, j, reg, "WAW", "register"))
                for reg in instr1.reads:
                    if reg in instr2.writes:
                        dependencies.append(Dependency(i, j, reg, "WAR", "register"))
                # Memory dependencies
                # Only one RAW per normalized memory location per instruction pair
                norm_writes = set(normalize_mem(mem) for mem in instr1.writes)
                norm_reads = set(normalize_mem(mem) for mem in instr2.reads)
                norm_instr2_writes = set(normalize_mem(mem) for mem in instr2.writes)
                norm_instr1_reads = set(normalize_mem(mem) for mem in instr1.reads)
                for mem in norm_writes:
                    if mem in norm_reads:
                        key = (mem, i, j)
                        if key not in seen_mem_raw:
                            dependencies.append(Dependency(i, j, mem, "RAW", "memory"))
                            seen_mem_raw.add(key)
                for mem in norm_writes:
                    if mem in norm_instr2_writes:
                        dependencies.append(Dependency(i, j, mem, "WAW", "memory"))
                for mem in norm_instr1_reads:
                    if mem in norm_instr2_writes:
                        dependencies.append(Dependency(i, j, mem, "WAR", "memory"))
            # Print memory dependencies
            print("\nMemory Dependencies:")
            has_mem_deps = any(mem_deps[dt] for dt in ['RAW', 'WAR', 'WAW'])
            if has_mem_deps:
                for dep_type in ['RAW', 'WAR', 'WAW']:
                    if mem_deps[dep_type]:
                        type_names = {
                            'RAW': 'Read-After-Write (True)',
                            'WAR': 'Write-After-Read (Anti)', 
                            'WAW': 'Write-After-Write (Output)'
                        }
                        print(f"  {type_names[dep_type]}:")
                        for dep in mem_deps[dep_type]:
                            print(f"    Line {dep.source_line} -> Line {dep.target_line} ({dep.resource})")
            else:
                print("  No memory dependencies found")
                
        else:
            print("No dependencies found")


def main():
    """Example usage with the provided basic block"""
    
    # The basic block from the user's file
    assembly_code = """
.LBB0_72:
    lea esi, [rax + rdx]
    and esi, 4095
    vmovss xmm0, dword ptr [rcx + 4*rsi]
    vmovss dword ptr [r15 + 4*rdx], xmm0
    inc rdx
    cmp r12, rdx
    jne .LBB0_72
"""
    
    print("Data Flow Analysis for Basic Block")
    print("=" * 50)
    
    # Create visualizer
    visualizer = DataFlowVisualizer()
    
    # Analyze and print dependencies
    visualizer.analyze_and_print(assembly_code)
    
    # Create visual representation
    try:
        output_file = visualizer.create_dependency_graph(assembly_code, "basic_block_dataflow")
        print(f"\nVisual representation saved to: {output_file}")
        print("Open the SVG file in a web browser to view the dependency graph.")
    except Exception as e:
        print(f"Error creating visual representation: {e}")
        print("Make sure Graphviz is installed: pip install graphviz")


if __name__ == "__main__":
    main()
