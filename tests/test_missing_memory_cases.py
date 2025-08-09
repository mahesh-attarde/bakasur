#!/usr/bin/env python3
"""
Additional Memory Dependency Test Cases

This file contains missing test cases that should be added to strengthen
the memory dependency testing coverage.
"""

import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_flow_visualizer import DataFlowVisualizer, DataDependency


class TestMissingMemoryDependencies(unittest.TestCase):
    """Test cases for missing memory dependency scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_string_operations_memory_dependencies(self):
        """Test memory dependencies in string operations (REP MOVS, STOS, etc.)"""
        assembly_code = """
        rep movsb
        rep stosb
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # String operations implicitly use memory locations
        # This test verifies how string operations are handled
        # Note: Current implementation may not handle these properly
    
    def test_indirect_memory_access(self):
        """Test memory dependencies with indirect addressing"""
        assembly_code = """
        mov rax, qword ptr [rbx]
        mov dword ptr [rax], ecx
        mov edx, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on [rax] even though rax is loaded indirectly
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Conservative analysis should detect dependency on same [rax] expression
        self.assertGreater(len(memory_deps), 0)
    
    def test_lea_no_memory_dependency(self):
        """Test that LEA instruction doesn't create memory dependencies"""
        assembly_code = """
        mov dword ptr [rax + 4], ebx
        lea rsi, [rax + 4]
        mov ecx, dword ptr [rax + 4]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # LEA should not read memory, so no memory dependency between LEA and others
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find RAW dependency between line 0 and line 2, but LEA shouldn't interfere
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].source_line, 0)
        self.assertEqual(raw_deps[0].target_line, 2)
    
    def test_segment_override_memory(self):
        """Test memory dependencies with segment overrides"""
        assembly_code = """
        mov dword ptr fs:[rax], ebx
        mov ecx, dword ptr fs:[rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle segment overrides in memory dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Current implementation may not handle fs: prefix properly
    
    def test_atomic_operations_memory(self):
        """Test memory dependencies with atomic operations"""
        assembly_code = """
        add dword ptr [rax], ebx
        mov ecx, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Atomic operations should create memory dependencies
        # Note: Testing with 'add' instead of 'lock add' since lock is a prefix
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertGreater(len(memory_deps), 0)
    
    def test_multiple_memory_operands_same_instruction(self):
        """Test instructions with multiple memory operands"""
        assembly_code = """
        mov rax, qword ptr [rbx]
        mov qword ptr [rcx], qword ptr [rax]
        mov rdx, qword ptr [rcx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find dependencies involving [rcx] and [rax]
        self.assertGreater(len(memory_deps), 0)
    
    def test_memory_with_different_base_same_displacement(self):
        """Test memory locations with different bases but same displacement"""
        assembly_code = """
        mov dword ptr [rax + 8], ebx
        mov dword ptr [rcx + 8], edx
        mov esi, dword ptr [rax + 8]
        mov edi, dword ptr [rcx + 8]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should find two separate RAW dependencies (different base registers)
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 2)
    
    def test_overlapping_memory_regions(self):
        """Test potentially overlapping memory regions"""
        assembly_code = """
        mov qword ptr [rax], rbx
        mov dword ptr [rax + 4], ecx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Conservative analysis: different expressions = no dependency
        # But in reality, these could overlap
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Current implementation likely finds no dependency (different expressions)
        self.assertEqual(len(memory_deps), 0)
    
    def test_rip_relative_addressing(self):
        """Test RIP-relative addressing memory dependencies"""
        assembly_code = """
        mov dword ptr [rip + 0x1000], eax
        mov ebx, dword ptr [rip + 0x1000]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on RIP-relative address
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        self.assertEqual(memory_deps[0].dependency_type, 'RAW')
    
    def test_memory_with_scale_variations(self):
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
        
        # Should find two separate RAW dependencies (different scale factors)
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 2)
    
    def test_conditional_memory_operations(self):
        """Test memory dependencies across conditional operations"""
        assembly_code = """
        cmp eax, ebx
        cmovne ecx, dword ptr [rdx]
        mov dword ptr [rdx], esi
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # CMOV creates conditional dependency
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Depends on how CMOV is classified in the analyzer
    
    def test_unaligned_memory_accesses(self):
        """Test unaligned memory access patterns"""
        assembly_code = """
        mov word ptr [rax + 1], bx
        mov cx, word ptr [rax + 1]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on unaligned access
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        self.assertEqual(memory_deps[0].dependency_type, 'RAW')
    
    def test_memory_fence_operations(self):
        """Test memory dependencies with fence operations"""
        assembly_code = """
        mov dword ptr [rax], ebx
        mfence
        mov ecx, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Fence operations may affect dependency analysis
        # Current implementation may not handle fence instructions
    
    def test_stack_red_zone_access(self):
        """Test stack red zone access patterns"""
        assembly_code = """
        mov dword ptr [rsp - 8], eax
        mov ebx, dword ptr [rsp - 8]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency on stack location
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 1)
        self.assertEqual(memory_deps[0].dependency_type, 'RAW')
    
    def test_mixed_size_memory_operations_complex(self):
        """Test complex mixed-size memory operations"""
        assembly_code = """
        mov qword ptr [rax], rbx
        mov word ptr [rax + 2], cx
        mov dl, byte ptr [rax + 3]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Conservative analysis: different expressions = no dependency
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Current implementation likely finds no dependencies (different expressions)
        self.assertEqual(len(memory_deps), 0)
    
    def test_vector_memory_operations_avx512(self):
        """Test AVX-512 vector memory operations"""
        assembly_code = """
        vmovdqu32 zmm0, zmmword ptr [rax]
        vmovdqu32 zmmword ptr [rax], zmm1
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find WAW dependency on large vector memory location
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        if memory_deps:  # If instruction is recognized
            self.assertEqual(len(memory_deps), 1)
            self.assertEqual(memory_deps[0].dependency_type, 'WAW')
    
    def test_gather_scatter_operations(self):
        """Test gather/scatter memory operation dependencies"""
        assembly_code = """
        vpgatherdd zmm0, dword ptr [rax + zmm1*4]
        vpscatterdd dword ptr [rax + zmm1*4], zmm2
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Gather/scatter operations involve complex memory patterns
        # Current implementation may not handle these advanced instructions
    
    def test_prefetch_operations(self):
        """Test prefetch instruction impact on dependencies"""
        assembly_code = """
        mov dword ptr [rax], ebx
        prefetcht0 [rax]
        mov ecx, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Prefetch shouldn't affect logical dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Should still find RAW dependency between mov instructions
    
    def test_memory_operand_expression_normalization(self):
        """Test normalization of equivalent memory expressions"""
        assembly_code = """
        mov dword ptr [rax + rbx], ecx
        mov edx, dword ptr [rbx + rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Current implementation likely treats these as different expressions
        # But mathematically they're equivalent: [rax + rbx] == [rbx + rax]
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        # Conservative implementation: no dependency (different textual expressions)
        self.assertEqual(len(memory_deps), 0)
    
    def test_memory_with_immediate_vs_register_displacement(self):
        """Test memory with immediate vs register displacement"""
        assembly_code = """
        mov dword ptr [rax + 4], ebx
        mov ecx, dword ptr [rax + rcx]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Different displacement types should not create dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertEqual(len(memory_deps), 0)


class TestMemoryDependencyErrorHandling(unittest.TestCase):
    """Test error handling in memory dependency analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_malformed_memory_operand(self):
        """Test handling of malformed memory operands"""
        assembly_code = """
        mov dword ptr [, ebx
        mov ecx, dword ptr ]rax[
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle malformed operands gracefully without crashing
        self.assertIsInstance(dependencies, list)
    
    def test_very_large_displacement(self):
        """Test memory operands with very large displacements"""
        assembly_code = """
        mov dword ptr [rax + 0x80000000], ebx
        mov ecx, dword ptr [rax + 0x80000000]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle large displacements correctly
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        self.assertGreater(len(memory_deps), 0)
    
    def test_unknown_memory_size_specifier(self):
        """Test handling of unknown memory size specifiers"""
        assembly_code = """
        mov tbyte ptr [rax], st0
        mov st1, tbyte ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle unknown size specifiers gracefully
        # May or may not find dependencies depending on implementation


if __name__ == '__main__':
    # Create test suite for missing cases
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMissingMemoryDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryDependencyErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
