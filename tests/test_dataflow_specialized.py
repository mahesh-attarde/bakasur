#!/usr/bin/env python3
"""
Specialized Data Flow Dependency Tests

This module contains advanced and specialized data flow dependency tests including:
- Complex architectural scenarios (cross-instruction sets, renaming, stalls)
- Stress tests with large numbers of dependencies
- Performance-critical edge cases
- Standalone testing capabilities
- Advanced AVX-512 and modern instruction support

This complements test_dataflow_comprehensive.py with more specialized scenarios.
"""

import unittest
import sys
import os
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

# Add parent directory to Python path for data_flow_visualizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_flow_visualizer import DataFlowVisualizer, DataDependency


class TestAdvancedArchitecturalScenarios(unittest.TestCase):
    """Advanced architectural scenarios and cross-instruction set dependencies"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_mixed_gpr_simd_dependencies(self):
        """Test mixed general purpose and SIMD register dependencies"""
        assembly_code = """
        mov rax, rbx
        movq xmm0, rax
        movd eax, xmm0
        mov rcx, rax
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find dependencies through the register chain
        self.assertGreater(len(reg_deps), 0)
    
    def test_partial_register_stalls(self):
        """Test scenarios that can cause partial register stalls"""
        assembly_code = """
        mov rax, rbx
        mov al, cl
        mov rdx, rax
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find dependencies on rax
        rax_deps = [dep for dep in reg_deps if dep.resource == 'rax']
        self.assertGreater(len(rax_deps), 0)
    
    def test_register_renaming_scenario(self):
        """Test scenario relevant to register renaming"""
        assembly_code = """
        mov eax, ebx
        mov ecx, edx
        add eax, ecx
        mov esi, eax
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find RAW dependencies
        raw_deps = [dep for dep in reg_deps if dep.dependency_type == 'RAW']
        self.assertGreater(len(raw_deps), 0)
    
    def test_cross_instruction_set_dependencies(self):
        """Test dependencies across different instruction sets"""
        assembly_code = """
        mov rax, rbx
        vmovq xmm0, rax
        vmovd ecx, xmm0
        vaddps ymm1, ymm0, ymm2
        vmovaps zmm3, zmm1
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find multiple dependencies
        self.assertGreater(len(reg_deps), 0)
    
    def test_high_numbered_simd_registers(self):
        """Test high-numbered SIMD registers (16-31)"""
        assembly_code = """
        vmovaps zmm16, zmm17
        vmovaps ymm16, ymm18
        vmovaps xmm19, xmm16
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find dependencies on zmm16
        zmm16_deps = [dep for dep in reg_deps if dep.resource == 'zmm16']
        self.assertGreater(len(zmm16_deps), 0)


class TestComplexMemoryPatterns(unittest.TestCase):
    """Complex memory access patterns and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
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


class TestAdvancedMaskRegisterScenarios(unittest.TestCase):
    """Advanced AVX-512 mask register scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
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


class TestStressTestsAndPerformance(unittest.TestCase):
    """Stress tests and performance-critical scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_very_large_basic_block(self):
        """Test with very large basic blocks"""
        assembly_lines = []
        
        # Create 100 instructions with various dependency patterns
        for i in range(50):
            assembly_lines.append(f"mov dword ptr [rax + {i*4}], ebx")
        
        for i in range(50):
            assembly_lines.append(f"mov ecx, dword ptr [rax + {i*4}]")
        
        assembly_code = '\n'.join(assembly_lines)
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle large blocks efficiently
        self.assertEqual(len(instructions), 100)
        
        # Should find many RAW dependencies
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 50)  # Each write->read pair
    
    def test_complex_register_interference(self):
        """Test complex register interference patterns"""
        assembly_code = """
        mov rax, rbx
        mov eax, ecx    # Overwrites lower 32 bits, zeros upper
        mov al, dl      # Overwrites lower 8 bits only
        mov ah, ch      # Overwrites upper 8 bits of lower 16
        mov r8w, ax     # Copy 16 bits to different register
        mov r9d, eax    # Copy 32 bits to different register
        mov r10, rax    # Copy full 64 bits
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find complex dependency chain
        self.assertGreater(len(reg_deps), 5)
    
    def test_mixed_memory_sizes_stress(self):
        """Test stress scenario with mixed memory operation sizes"""
        assembly_code = """
        mov qword ptr [rax], rbx      # 8 bytes
        mov dword ptr [rax + 8], ecx  # 4 bytes  
        mov word ptr [rax + 12], dx   # 2 bytes
        mov byte ptr [rax + 14], al   # 1 byte
        
        mov bl, byte ptr [rax + 14]   # Read 1 byte
        mov cx, word ptr [rax + 12]   # Read 2 bytes
        mov edx, dword ptr [rax + 8]  # Read 4 bytes
        mov rsi, qword ptr [rax]      # Read 8 bytes
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        # Should find 4 RAW dependencies (each write->read pair)
        self.assertEqual(len(raw_deps), 4)
    
    def test_pathological_addressing_modes(self):
        """Test pathological complex addressing modes"""
        assembly_code = """
        mov rax, qword ptr [rbx + rcx*8 + 0x12345678]
        mov qword ptr [rsi + rdi*4 + 0x87654321], rax
        mov rdx, qword ptr [rsi + rdi*4 + 0x87654321]
        
        mov qword ptr [r8 + r9*2 + 0xABCDEF00], rdx
        mov qword ptr [r10 + r11*1 + 0x11223344], rax
        mov r12, qword ptr [r8 + r9*2 + 0xABCDEF00]
        mov r13, qword ptr [r10 + r11*1 + 0x11223344]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        # Should handle complex addressing modes correctly
        self.assertGreater(len(memory_deps), 0)


class TestCaseInsensitiveAndErrorHandling(unittest.TestCase):
    """Test case insensitive handling and error scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_case_insensitive_registers(self):
        """Test case insensitive register handling"""
        assembly_code = """
        MOV EAX, EBX
        mov ecx, EAX
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find RAW dependency despite case differences
        raw_deps = [dep for dep in reg_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 1)
    
    def test_unknown_register_handling(self):
        """Test handling of unknown or unsupported registers"""
        assembly_code = """
        mov unknownreg, ebx
        mov eax, unknownreg
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle gracefully without crashing
        self.assertIsInstance(dependencies, list)
    
    def test_malformed_memory_operands(self):
        """Test handling of malformed memory operands"""
        assembly_code = """
        mov dword ptr [rax, ebx
        mov ecx, dword ptr ]rdx[
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle gracefully
        self.assertIsInstance(dependencies, list)
    
    def test_register_in_memory_operands(self):
        """Test sub-registers used in memory addressing"""
        assembly_code = """
        mov eax, 0
        mov dword ptr [rbx + eax*4], ecx
        inc eax
        mov edx, dword ptr [rbx + eax*4]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should handle register dependencies correctly
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        self.assertGreater(len(reg_deps), 0)


class TestStandaloneThreeOperandScenarios(unittest.TestCase):
    """Additional three-operand instruction scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
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
        
        # Should find multiple RAW dependencies
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


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes in logical order
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedArchitecturalScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexMemoryPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedMaskRegisterScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestStressTestsAndPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestCaseInsensitiveAndErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestStandaloneThreeOperandScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
