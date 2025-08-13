"""
Data flow analysis for assembly instructions

Analyzes data dependencies between instructions in assembly basic blocks.
"""

import re
from typing import List, Set, Tuple, Optional
from .models import Instruction, DataDependency
from .generic_parser import GenericAssemblyParser
from .arch_config import ArchitectureConfig


class DataFlowAnalyzer:
    """Analyzes data flow dependencies in assembly basic blocks"""
    
    def __init__(self, architecture: str = None):
        """
        Initialize analyzer for specific architecture
        
        Args:
            architecture: Architecture name (e.g., 'x86_64', 'aarch64')
                         If None, will auto-detect from first parsed instruction
        """
        self.parser = GenericAssemblyParser(architecture)
        self.config: Optional[ArchitectureConfig] = None
        
    def _ensure_config(self, assembly_text: str = ""):
        """Ensure architecture configuration is loaded"""
        self.parser._ensure_config(assembly_text)
        self.config = self.parser.config
    
    def analyze_instruction_operands(self, instruction: Instruction) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Analyze instruction operands to determine reads and writes
        
        Returns:
            reads: Set of registers/memory read
            writes: Set of registers/memory written
            memory_ops: Set of memory operations
        """
        self._ensure_config()
        
        reads = set()
        writes = set()
        memory_ops = set()
        
        if not instruction.operands:
            return reads, writes, memory_ops
        
        opcode = instruction.opcode.lower()
        
        # Special case for LEA-like instructions (address calculation only)
        special_addr_calc_instructions = set()
        for name, info in self.config.special_instructions.items():
            if info.get("behavior") == "address_calculation_only":
                special_addr_calc_instructions.add(name)
        
        if opcode in special_addr_calc_instructions:
            # These instructions don't access memory, only calculate addresses
            if len(instruction.operands) >= 2:
                dest_reads, _, _ = self.parser.parse_operand(instruction.operands[0])
                writes.update(dest_reads)
                
                # Extract only the registers from the memory expression
                src_operand = instruction.operands[1]
                if '[' in src_operand and ']' in src_operand:
                    # Extract register names from memory expression without treating as memory access
                    memory_expr = re.search(r'\[([^\]]+)\]', src_operand)
                    if memory_expr:
                        expr_content = memory_expr.group(1)
                        # Find register names in the expression
                        reg_pattern = self.config.memory_patterns["register"]
                        reg_matches = re.findall(reg_pattern, expr_content, re.IGNORECASE)
                        for reg in reg_matches:
                            reads.add(self.parser.normalize_register(reg))
                else:
                    # Handle non-memory source operands
                    src_reads, _, _ = self.parser.parse_operand(src_operand)
                    reads.update(src_reads)
        
        # Handle different instruction types using configuration
        elif opcode in self.config.read_write_instructions:
            # Special handling for mask instructions
            is_mask_instruction = any(opcode.startswith(pattern) for pattern in self.config.mask_instructions)
            
            if is_mask_instruction:
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
                        if "mask_register" in self.config.memory_patterns:
                            mask_pattern = self.config.memory_patterns["mask_register"]
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
                        if "mask_register" in self.config.memory_patterns:
                            mask_pattern = self.config.memory_patterns["mask_register"]
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
                    if opcode in self.config.read_modify_write_instructions:
                        # Destination is also read in these instructions
                        if dest_mem:
                            reads.add(dest_mem)  # Memory location is read before being written
                        else:
                            reads.update(dest_reads)  # Register is read before being written
        
        elif opcode in self.config.read_only_instructions:
            # All operands are read
            for operand in instruction.operands:
                op_reads, op_writes, op_mem = self.parser.parse_operand(operand)
                reads.update(op_reads)
                if op_mem:
                    memory_ops.add(op_mem)
                    reads.add(op_mem)
        
        elif opcode in self.config.jump_instructions:
            # Jump instructions typically read their operands
            for operand in instruction.operands:
                op_reads, op_writes, op_mem = self.parser.parse_operand(operand)
                reads.update(op_reads)
        
        return reads, writes, memory_ops
    
    def find_dependencies(self, instructions: List[Instruction]) -> List[DataDependency]:
        """Find data dependencies between instructions"""
        self._ensure_config()
        
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
        self._ensure_config(assembly_text)
        
        instructions = []
        lines = assembly_text.strip().split('\n')
        
        for i, line in enumerate(lines):
            instruction = self.parser.parse_instruction(line, i)
            if instruction and instruction.opcode:  # Skip empty lines and label-only lines
                instructions.append(instruction)
        
        return instructions
    
    def get_architecture_info(self) -> dict:
        """Get information about the current architecture configuration"""
        self._ensure_config()
        return self.parser.get_architecture_info()
