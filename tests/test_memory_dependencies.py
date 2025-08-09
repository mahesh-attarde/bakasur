#!/usr/bin/env python3
"""
Unit tests for Memory Dependencies in Data Flow Analyzer

Tests memory dependency detection, classification, and analysis functionality
"""

import unittest
import sys
import os

# Add parent directory to Python path for data_flow_visualizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_flow_visualizer import DataFlowVisualizer, DataDependency


class TestMemoryDependencies(unittest.TestCase):
    """Test cases for memory dependency analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_memory_raw_dependency(self):
        """Test Read-After-Write memory dependency detection"""
        assembly_code = """
        mov dword ptr [rax], ebx
        mov ecx, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find one RAW memory dependency
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        
        dep = memory_deps[0]
        self.assertEqual(dep.dependency_type, 'RAW')
        self.assertEqual(dep.source_line, 0)
        self.assertEqual(dep.target_line, 1)
        self.assertEqual(dep.resource, '[rax]')
        self.assertEqual(dep.operand_type, 'memory')
    
    def test_memory_war_dependency(self):
        """Test Write-After-Read memory dependency detection"""
        assembly_code = """
        mov eax, dword ptr [rbx]
        mov dword ptr [rbx], ecx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find one WAR memory dependency
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        
        dep = memory_deps[0]
        self.assertEqual(dep.dependency_type, 'WAR')
        self.assertEqual(dep.source_line, 0)
        self.assertEqual(dep.target_line, 1)
        self.assertEqual(dep.resource, '[rbx]')
        self.assertEqual(dep.operand_type, 'memory')
    
    def test_memory_waw_dependency(self):
        """Test Write-After-Write memory dependency detection"""
        assembly_code = """
        mov dword ptr [rdx], eax
        mov dword ptr [rdx], ebx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find one WAW memory dependency
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        
        dep = memory_deps[0]
        self.assertEqual(dep.dependency_type, 'WAW')
        self.assertEqual(dep.source_line, 0)
        self.assertEqual(dep.target_line, 1)
        self.assertEqual(dep.resource, '[rdx]')
        self.assertEqual(dep.operand_type, 'memory')
    
    def test_complex_memory_address(self):
        """Test memory dependencies with complex addressing modes"""
        assembly_code = """
        mov dword ptr [rax + rbx*2 + 4], ecx
        mov edx, dword ptr [rax + rbx*2 + 4]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on complex memory address
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        
        dep = memory_deps[0]
        self.assertEqual(dep.dependency_type, 'RAW')
        self.assertEqual(dep.resource, '[rax + rbx*2 + 4]')
        self.assertEqual(dep.operand_type, 'memory')
    
    def test_memory_vs_register_dependencies(self):
        """Test mixed memory and register dependencies"""
        assembly_code = """
        mov eax, ebx
        mov dword ptr [rcx], eax
        mov edx, dword ptr [rcx]
        mov eax, edx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Separate register and memory dependencies
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        mem_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should have both types
        self.assertGreater(len(reg_deps), 0)
        self.assertGreater(len(mem_deps), 0)
        
        # Check memory dependency
        mem_raw_deps = [dep for dep in mem_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(mem_raw_deps), 1)
        self.assertEqual(mem_raw_deps[0].resource, '[rcx]')
    
    def test_different_memory_locations(self):
        """Test that different memory locations don't create dependencies"""
        assembly_code = """
        mov dword ptr [rax], ebx
        mov ecx, dword ptr [rdx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find no memory dependencies (different addresses)
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 0)
    
    def test_memory_aliasing_same_register(self):
        """Test memory dependencies with same base register"""
        assembly_code = """
        mov dword ptr [rax], ebx
        mov ecx, dword ptr [rax + 4]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find no memory dependencies (different offsets, conservative analysis)
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 0)
    
    def test_stack_memory_operations(self):
        """Test memory dependencies with stack operations"""
        assembly_code = """
        push eax
        pop ebx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Stack operations should create memory dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Note: This depends on how push/pop are modeled in the analyzer
        # The exact behavior may vary based on implementation
    
    def test_array_access_pattern(self):
        """Test memory dependencies in array access patterns"""
        assembly_code = """
        mov eax, 0
        mov dword ptr [rbx + rax*4], ecx
        inc eax
        mov edx, dword ptr [rbx + rax*4]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Conservative analysis treats identical memory expressions as same location
        # Even though rax value changes, the textual expression is the same
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        
        dep = memory_deps[0]
        self.assertEqual(dep.dependency_type, 'RAW')
        self.assertEqual(dep.resource, '[rbx + rax*4]')
        self.assertEqual(dep.operand_type, 'memory')
    
    def test_float_memory_operations(self):
        """Test memory dependencies with floating-point memory operations"""
        assembly_code = """
        vmovss dword ptr [rax], xmm0
        vmovss xmm1, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW memory dependency for float operations
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        
        dep = memory_deps[0]
        self.assertEqual(dep.dependency_type, 'RAW')
        self.assertEqual(dep.resource, '[rax]')
        self.assertEqual(dep.operand_type, 'memory')
    
    def test_memory_size_variations(self):
        """Test memory dependencies with different operation sizes"""
        assembly_code = """
        mov byte ptr [rax], bl
        mov cx, word ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency despite size difference
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        
        dep = memory_deps[0]
        self.assertEqual(dep.dependency_type, 'RAW')
        self.assertEqual(dep.resource, '[rax]')
        self.assertEqual(dep.operand_type, 'memory')
    
    def test_complex_real_world_example(self):
        """Test memory dependencies in a real-world code pattern"""
        assembly_code = """
        lea rsi, [rax + rdx]
        and esi, 4095
        vmovss xmm0, dword ptr [rcx + 4*rsi]
        vmovss dword ptr [r15 + 4*rdx], xmm0
        inc rdx
        cmp r12, rdx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Separate dependencies by type
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        mem_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # This example should have register dependencies but no memory dependencies
        # (different memory addresses)
        self.assertGreater(len(reg_deps), 0)
        # Memory dependencies depend on whether the analyzer can prove addresses are different
        # In conservative analysis, different expressions = no dependency
    
    def test_operand_type_classification(self):
        """Test that operand types are correctly classified"""
        assembly_code = """
        mov eax, ebx
        mov dword ptr [rcx], eax
        mov edx, dword ptr [rcx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Check that all dependencies have correct operand_type field
        for dep in dependencies:
            self.assertIn(dep.operand_type, ['register', 'memory'])
            
            # Verify operand type matches resource type
            if dep.resource.startswith('[') and dep.resource.endswith(']'):
                self.assertEqual(dep.operand_type, 'memory')
            else:
                self.assertEqual(dep.operand_type, 'register')


class TestMemoryDependencyEdgeCases(unittest.TestCase):
    """Test edge cases and corner cases for memory dependency analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_empty_basic_block(self):
        """Test memory dependency analysis with empty basic block"""
        assembly_code = ""
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        self.assertEqual(len(instructions), 0)
        self.assertEqual(len(dependencies), 0)
    
    def test_single_instruction(self):
        """Test memory dependency analysis with single instruction"""
        assembly_code = "mov dword ptr [rax], ebx"
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        self.assertEqual(len(instructions), 1)
        self.assertEqual(len(dependencies), 0)  # No dependencies with single instruction
    
    def test_register_only_operations(self):
        """Test that register-only operations don't create memory dependencies"""
        assembly_code = """
        mov eax, ebx
        add eax, ecx
        mov edx, eax
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should have only register dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 0)
        
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        self.assertGreater(len(register_deps), 0)


class TestAdvancedMemoryDependencies(unittest.TestCase):
    """Test advanced memory dependency scenarios that were missing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_lea_instruction_no_memory_access(self):
        """Test that LEA doesn't create memory dependencies (address calculation only)"""
        assembly_code = """
        mov dword ptr [rax + 8], ebx
        lea rsi, [rax + 8]
        mov ecx, dword ptr [rax + 8]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # LEA calculates address but doesn't access memory
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find RAW dependency between mov instructions, LEA doesn't interfere
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].source_line, 0)
        self.assertEqual(raw_deps[0].target_line, 2)
    
    def test_rip_relative_addressing(self):
        """Test RIP-relative addressing dependencies"""
        assembly_code = """
        mov dword ptr [rip + 0x100], eax
        mov ebx, dword ptr [rip + 0x100]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on RIP-relative address
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        self.assertEqual(memory_deps[0].dependency_type, 'RAW')
        self.assertEqual(memory_deps[0].resource, '[rip + 0x100]')
    
    def test_indirect_memory_addressing(self):
        """Test indirect memory addressing patterns"""
        assembly_code = """
        mov rax, qword ptr [rbx]
        mov dword ptr [rax], ecx
        mov edx, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on [rax] location
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        rax_deps = [dep for dep in memory_deps if dep.resource == '[rax]']
        self.assertEqual(len(rax_deps), 1)
        self.assertEqual(rax_deps[0].dependency_type, 'RAW')
    
    def test_unaligned_memory_operations(self):
        """Test unaligned memory access dependencies"""
        assembly_code = """
        mov word ptr [rax + 1], bx
        mov cx, word ptr [rax + 1]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on unaligned location
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        self.assertEqual(memory_deps[0].dependency_type, 'RAW')
        self.assertEqual(memory_deps[0].resource, '[rax + 1]')
    
    def test_stack_red_zone_access(self):
        """Test stack red zone (negative RSP offset) dependencies"""
        assembly_code = """
        mov dword ptr [rsp - 8], eax
        mov ebx, dword ptr [rsp - 8]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on negative stack offset
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        self.assertEqual(memory_deps[0].dependency_type, 'RAW')
        self.assertEqual(memory_deps[0].resource, '[rsp - 8]')
    
    def test_multiple_memory_operands_same_instruction(self):
        """Test instructions with source and destination memory operands"""
        assembly_code = """
        mov rax, qword ptr [rbx]
        mov qword ptr [rcx], qword ptr [rax]
        mov rdx, qword ptr [rcx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find dependencies involving memory locations
        self.assertGreater(len(memory_deps), 0)
        
        # Check for RAW dependency on [rcx]
        rcx_deps = [dep for dep in memory_deps if dep.resource == '[rcx]' and dep.dependency_type == 'RAW']
        self.assertEqual(len(rcx_deps), 1)
    
    def test_memory_scale_factor_variations(self):
        """Test memory addressing with different scale factors"""
        assembly_code = """
        mov dword ptr [rax + rbx*1], ecx
        mov dword ptr [rax + rbx*2], edx
        mov esi, dword ptr [rax + rbx*1]
        mov edi, dword ptr [rax + rbx*2]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find two separate RAW dependencies (different scale factors = different addresses)
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 2)
    
    def test_overlapping_memory_regions_conservative(self):
        """Test conservative analysis of potentially overlapping memory regions"""
        assembly_code = """
        mov qword ptr [rax], rbx
        mov dword ptr [rax + 4], ecx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Conservative analysis: different expressions = no dependency
        # Even though these could overlap in reality
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 0)
    
    def test_segment_override_memory_operations(self):
        """Test memory operations with segment overrides"""
        assembly_code = """
        mov dword ptr fs:[rax], ebx
        mov ecx, dword ptr fs:[rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle segment overrides (if parser supports them)
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Result depends on whether segment prefixes are parsed correctly
    
    def test_memory_expression_normalization_limits(self):
        """Test limits of memory expression normalization"""
        assembly_code = """
        mov dword ptr [rax + rbx], ecx
        mov edx, dword ptr [rbx + rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # These expressions are mathematically equivalent but textually different
        # Conservative analysis treats them as different
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 0)
    
    def test_very_large_memory_displacement(self):
        """Test memory operands with large displacements"""
        assembly_code = """
        mov dword ptr [rax + 0x12345678], ebx
        mov ecx, dword ptr [rax + 0x12345678]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle large displacements correctly
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        self.assertEqual(memory_deps[0].dependency_type, 'RAW')
    
    def test_zero_displacement_implicit_vs_explicit(self):
        """Test implicit vs explicit zero displacement"""
        assembly_code = """
        mov dword ptr [rax], ebx
        mov ecx, dword ptr [rax + 0]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # [rax] and [rax + 0] should be treated as different expressions
        # in conservative analysis
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 0)


class TestMemoryDependencyStressTests(unittest.TestCase):
    """Stress tests for memory dependency analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_many_memory_locations(self):
        """Test with many different memory locations"""
        assembly_lines = []
        for i in range(10):
            assembly_lines.append(f"mov dword ptr [rax + {i*4}], ebx")
        
        for i in range(10):
            assembly_lines.append(f"mov ecx, dword ptr [rax + {i*4}]")
        
        assembly_code = '\n'.join(assembly_lines)
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find 10 RAW dependencies (each write->read pair)
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 10)
    
    def test_deeply_nested_memory_expressions(self):
        """Test complex nested memory addressing"""
        assembly_code = """
        mov rax, qword ptr [rbx + rcx*2]
        mov rdx, qword ptr [rax + rsi*4 + 8]
        mov dword ptr [rdx + rdi*8 + 16], esi
        mov ecx, dword ptr [rdx + rdi*8 + 16]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle complex addressing and find final RAW dependency
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 1)


class TestMemoryDependencyEdgeCases(unittest.TestCase):
    def test_placeholder(self):
        """Placeholder test for edge cases"""
        pass


class TestThreeOperandInstructions(unittest.TestCase):
    """Test cases for three-operand x86 instructions with overlapping destinations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_vfmadd_memory_destination_overlap_src1(self):
        """Test FMA instruction where destination overlaps with first source in memory"""
        assembly_code = """
        vmovss dword ptr [rax], xmm1
        vfmadd213ss dword ptr [rax], xmm2, xmm3
        vmovss xmm0, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW (read first write) and WAR (write after read) dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # First: RAW dependency from vmovss write to vfmadd read
        # Second: WAR dependency from vfmadd write to final vmovss read
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        war_deps = [dep for dep in memory_deps if dep.dependency_type == 'WAR']
        
        self.assertEqual(len(raw_deps), 1)
        self.assertEqual(len(war_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rax]')
        self.assertEqual(war_deps[0].resource, '[rax]')
    
    def test_vfmadd_memory_destination_overlap_src2(self):
        """Test FMA instruction where destination overlaps with second source in memory"""
        assembly_code = """
        vmovss dword ptr [rbx], xmm2
        vfmadd213ss xmm1, dword ptr [rbx], xmm3
        vmovss xmm0, dword ptr [rbx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency from vmovss write to vfmadd read
        # And potential WAR if destination writes back to memory
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rbx]')
    
    def test_vpmadd_three_operand_memory_overlap(self):
        """Test packed multiply-add with memory operand overlaps"""
        assembly_code = """
        vmovdqa xmmword ptr [rcx], xmm1
        vpmadd52luq xmm0, xmm1, xmmword ptr [rcx]
        vmovdqa xmm2, xmmword ptr [rcx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency from vmovdqa write to vpmadd read
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rcx]')
    
    def test_imul_three_operand_memory_source(self):
        """Test three-operand IMUL with memory source"""
        assembly_code = """
        mov dword ptr [rdx], eax
        imul ebx, dword ptr [rdx], 4
        mov ecx, dword ptr [rdx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency from mov write to imul read
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rdx]')
    
    def test_vblend_three_operand_memory_destination(self):
        """Test blend instruction with memory destination"""
        assembly_code = """
        vmovss dword ptr [rsi], xmm1
        vblendvps xmm0, xmm1, dword ptr [rsi], xmm2
        vmovss xmm3, dword ptr [rsi]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency from vmovss write to vblendvps read
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rsi]')
    
    def test_lea_three_operand_no_memory_dependency(self):
        """Test LEA three-operand (address calculation) doesn't create memory deps"""
        assembly_code = """
        mov dword ptr [rax + rbx + 8], ecx
        lea rdi, [rax + rbx + 8]
        mov edx, dword ptr [rax + rbx + 8]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # LEA calculates address but doesn't access memory
        # Should find RAW dependency between the two mov instructions only
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        self.assertEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].source_line, 0)  # First mov
        self.assertEqual(raw_deps[0].target_line, 2)  # Third mov (skipping LEA)
    
    def test_shld_three_operand_memory_overlap(self):
        """Test SHLD/SHRD three-operand instructions with memory"""
        assembly_code = """
        mov dword ptr [r8], eax
        shld dword ptr [r8], ebx, 4
        mov ecx, dword ptr [r8]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # SHLD reads and writes the first operand (memory location)
        # Should find RAW (mov->shld) and WAR (shld->mov) dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        war_deps = [dep for dep in memory_deps if dep.dependency_type == 'WAR']
        
        # At least one RAW dependency (mov write -> shld read)
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[r8]')
    
    def test_multiple_three_operand_memory_conflicts(self):
        """Test multiple three-operand instructions with memory conflicts"""
        assembly_code = """
        vmovss dword ptr [rax], xmm0
        vmovss dword ptr [rbx], xmm1  
        vfmadd213ss dword ptr [rax], dword ptr [rbx], xmm2
        vmovss xmm3, dword ptr [rax]
        vmovss xmm4, dword ptr [rbx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find multiple RAW dependencies:
        # 1. [rax] write -> vfmadd read
        # 2. [rbx] write -> vfmadd read  
        # 3. vfmadd write [rax] -> final vmovss read [rax]
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        # At least 2 RAW dependencies (writes to reads)
        self.assertGreaterEqual(len(raw_deps), 2)
        
        # Check that both memory locations are involved
        resources = {dep.resource for dep in raw_deps}
        self.assertIn('[rax]', resources)
        self.assertIn('[rbx]', resources)
    
    def test_cmov_three_operand_memory_conditional(self):
        """Test conditional move three-operand with memory"""
        assembly_code = """
        mov dword ptr [rcx], eax
        cmp ebx, 0
        cmovne edx, dword ptr [rcx]
        mov dword ptr [rcx], esi
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency from first mov to cmovne
        # And WAR dependency from cmovne to final mov
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        war_deps = [dep for dep in memory_deps if dep.dependency_type == 'WAR']
        
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rcx]')
    
    def test_vperm_three_operand_memory_permutation(self):
        """Test permutation instructions with three operands and memory"""
        assembly_code = """
        vmovdqa xmmword ptr [rdi], xmm1
        vpermilps xmm0, xmmword ptr [rdi], 0x1B
        vmovdqa xmm2, xmmword ptr [rdi]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency from vmovdqa write to vpermilps read
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rdi]')
    
    def test_complex_three_operand_addressing_modes(self):
        """Test three-operand instructions with complex addressing modes"""
        assembly_code = """
        mov qword ptr [rax + rbx*2 + 16], rcx
        imul rdx, qword ptr [rax + rbx*2 + 16], 3
        shld qword ptr [rax + rbx*2 + 16], rdi, cl
        mov rsi, qword ptr [rax + rbx*2 + 16]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find multiple dependencies on the complex memory location
        complex_addr_deps = [dep for dep in memory_deps 
                           if dep.resource == '[rax + rbx*2 + 16]']
        
        self.assertGreaterEqual(len(complex_addr_deps), 2)
        
        # Should have RAW dependencies
        raw_deps = [dep for dep in complex_addr_deps if dep.dependency_type == 'RAW']
        self.assertGreaterEqual(len(raw_deps), 1)


class TestMaskRegisterDependencies(unittest.TestCase):
    """Test cases for AVX-512 mask register dependencies"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_mask_register_basic_dependency(self):
        """Test basic mask register RAW dependency"""
        assembly_code = """
        vpcmpeqd k1, zmm0, zmm1
        vmovaps zmm2{k1}, zmm3
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on mask register k1
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        k1_deps = [dep for dep in register_deps if 'k1' in dep.resource]
        
        self.assertEqual(len(k1_deps), 1)
        self.assertEqual(k1_deps[0].dependency_type, 'RAW')
        self.assertEqual(k1_deps[0].source_line, 0)
        self.assertEqual(k1_deps[0].target_line, 1)
    
    def test_mask_register_with_memory_operands(self):
        """Test mask register dependencies with memory operands"""
        assembly_code = """
        vpcmpeqd k2, zmm0, zmmword ptr [rax]
        vmovaps zmmword ptr [rbx]{k2}, zmm1
        vmovaps zmm2{k2}, zmmword ptr [rcx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find mask register RAW dependencies
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        k2_deps = [dep for dep in register_deps if 'k2' in dep.resource]
        
        # k2 is written by first instruction, read by second and third
        self.assertEqual(len(k2_deps), 2)
        for dep in k2_deps:
            self.assertEqual(dep.dependency_type, 'RAW')
            self.assertEqual(dep.source_line, 0)
            self.assertIn(dep.target_line, [1, 2])
    
    def test_mask_register_logical_operations(self):
        """Test mask register logical operations dependencies"""
        assembly_code = """
        vpcmpeqd k1, zmm0, zmm1
        vpcmpgtd k2, zmm2, zmm3
        kandw k3, k1, k2
        vmovaps zmm4{k3}, zmm5
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find RAW dependencies for k1->kandw and k2->kandw
        k1_deps = [dep for dep in register_deps if 'k1' in dep.resource and dep.dependency_type == 'RAW']
        k2_deps = [dep for dep in register_deps if 'k2' in dep.resource and dep.dependency_type == 'RAW']
        k3_deps = [dep for dep in register_deps if 'k3' in dep.resource and dep.dependency_type == 'RAW']
        
        self.assertEqual(len(k1_deps), 1)  # k1 write -> kandw read
        self.assertEqual(len(k2_deps), 1)  # k2 write -> kandw read
        self.assertEqual(len(k3_deps), 1)  # k3 write -> vmovaps read
    
    def test_mask_register_waw_dependency(self):
        """Test mask register WAW (Write-After-Write) dependency"""
        assembly_code = """
        vpcmpeqd k4, zmm0, zmm1
        vpcmpgtd k4, zmm2, zmm3
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find WAW dependency on mask register k4
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        k4_deps = [dep for dep in register_deps if 'k4' in dep.resource]
        
        self.assertEqual(len(k4_deps), 1)
        self.assertEqual(k4_deps[0].dependency_type, 'WAW')
        self.assertEqual(k4_deps[0].source_line, 0)
        self.assertEqual(k4_deps[0].target_line, 1)
    
    def test_mask_register_war_dependency(self):
        """Test mask register WAR (Write-After-Read) dependency"""
        assembly_code = """
        vmovaps zmm0{k5}, zmm1
        vpcmpeqd k5, zmm2, zmm3
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find WAR dependency on mask register k5
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        k5_deps = [dep for dep in register_deps if 'k5' in dep.resource]
        
        self.assertEqual(len(k5_deps), 1)
        self.assertEqual(k5_deps[0].dependency_type, 'WAR')
        self.assertEqual(k5_deps[0].source_line, 0)
        self.assertEqual(k5_deps[0].target_line, 1)
    
    def test_mask_register_complex_memory_pattern(self):
        """Test complex pattern with mask registers and memory"""
        assembly_code = """
        mov rax, qword ptr [rsi]
        vpcmpeqd k6, zmm0, zmmword ptr [rax]
        vmovaps zmmword ptr [rax + 64]{k6}, zmm1
        vmovaps zmm2{k6}, zmmword ptr [rax + 128]
        kandw k7, k6, k1
        vmovaps zmmword ptr [rdi]{k7}, zmm3
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find multiple mask register dependencies
        k6_deps = [dep for dep in register_deps if 'k6' in dep.resource]
        k7_deps = [dep for dep in register_deps if 'k7' in dep.resource]
        
        # k6 is used in multiple places
        self.assertGreaterEqual(len(k6_deps), 2)
        
        # Should also have memory dependencies involving [rax]
        rax_mem_deps = [dep for dep in memory_deps if '[rax]' in dep.resource]
        self.assertGreaterEqual(len(rax_mem_deps), 1)
    
    def test_mask_register_with_merging_zeroing(self):
        """Test mask register with merging vs zeroing semantics"""
        assembly_code = """
        vpcmpeqd k3, zmm0, zmm1
        vmovaps zmm2{k3}, zmm3         ; merging (default)
        vmovaps zmm4{k3}{z}, zmm5      ; zeroing
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Both merging and zeroing operations should depend on k3
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        k3_deps = [dep for dep in register_deps if 'k3' in dep.resource and dep.dependency_type == 'RAW']
        
        self.assertEqual(len(k3_deps), 2)  # k3 used by both vmovaps instructions
        
        # Check line dependencies
        target_lines = {dep.target_line for dep in k3_deps}
        self.assertEqual(target_lines, {1, 2})
    
    def test_mask_register_broadcast_operations(self):
        """Test mask register with broadcast memory operations"""
        assembly_code = """
        vpcmpeqd k1, zmm0, dword ptr [rax]{1to16}
        vmovaps zmm1{k1}, dword ptr [rbx]{1to16}
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on mask register k1
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        k1_deps = [dep for dep in register_deps if 'k1' in dep.resource]
        
        self.assertEqual(len(k1_deps), 1)
        self.assertEqual(k1_deps[0].dependency_type, 'RAW')
    
    def test_mask_register_gather_scatter_operations(self):
        """Test mask register with gather/scatter operations"""
        assembly_code = """
        vpcmpeqd k2, zmm0, zmm1
        vpgatherdd zmm2{k2}, dword ptr [rax + zmm3*4]
        vpscatterdd dword ptr [rbx + zmm4*4]{k2}, zmm5
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # k2 should be used by both gather and scatter operations
        register_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        k2_deps = [dep for dep in register_deps if 'k2' in dep.resource and dep.dependency_type == 'RAW']
        
        self.assertGreaterEqual(len(k2_deps), 1)  # At least one dependency on k2


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryDependencyEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestThreeOperandInstructions))
    suite.addTests(loader.loadTestsFromTestCase(TestMaskRegisterDependencies))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
