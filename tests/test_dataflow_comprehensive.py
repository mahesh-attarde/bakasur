#!/usr/bin/env python3
"""
Comprehensive Data Flow Dependency Tests

This module consolidates all core data flow dependency tests including:
- Basic memory dependencies (RAW, WAR, WAW)
- Sub-register dependencies for all register families
- Three-operand instruction support
- AVX-512 mask register dependencies
- Complex addressing modes and edge cases

Merged from: test_memory_dependencies.py, test_subregister_dependencies.py,
            test_three_operand_standalone.py, test_mask_basic.py
"""

import unittest
import sys
import os

# Add parent directory to Python path for data_flow_visualizer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dfg_analyzer import DataFlowVisualizer, DataDependency


class TestBasicMemoryDependencies(unittest.TestCase):
    """Core memory dependency detection tests"""
    
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


class TestSubRegisterDependencies(unittest.TestCase):
    """Sub-register dependency detection tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_x86_32bit_to_8bit_dependency(self):
        """Test dependency from 32-bit to 8-bit register"""
        assembly_code = """
        mov eax, ebx
        mov cl, al
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW dependency from rax (eax) to rcx (cl)
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Look for dependency involving rax and rcx
        rax_to_rcx = [dep for dep in reg_deps if 
                      dep.source_line == 0 and dep.target_line == 1 and 
                      dep.resource == 'rax']
        self.assertEqual(len(rax_to_rcx), 1)
        self.assertEqual(rax_to_rcx[0].dependency_type, 'RAW')
    
    def test_64bit_to_32bit_zeroing(self):
        """Test 64-bit to 32-bit register dependency (32-bit ops zero upper bits)"""
        assembly_code = """
        mov rax, rbx
        mov eax, ecx
        mov rdx, rax
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should have WAW from line 0 to line 1 (both write rax)
        waw_deps = [dep for dep in reg_deps if dep.dependency_type == 'WAW' and dep.resource == 'rax']
        self.assertEqual(len(waw_deps), 1)
        
        # Should have RAW from line 1 to line 2 (read rax after write)
        raw_deps = [dep for dep in reg_deps if dep.dependency_type == 'RAW' and dep.resource == 'rax']
        self.assertEqual(len(raw_deps), 1)
    
    def test_r8_register_family(self):
        """Test dependencies in R8-R15 register family"""
        assembly_code = """
        mov r8, r9
        mov r8d, r10d
        mov r11w, r8w
        mov r12b, r8b
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find WAW dependency on r8 (line 0 -> line 1)
        waw_deps = [dep for dep in reg_deps if dep.dependency_type == 'WAW' and dep.resource == 'r8']
        self.assertEqual(len(waw_deps), 1)
        
        # Should find RAW dependencies from r8 to r11 and r12
        raw_deps = [dep for dep in reg_deps if dep.dependency_type == 'RAW' and dep.source_line == 1]
        self.assertEqual(len(raw_deps), 2)
    
    def test_xmm_ymm_zmm_aliasing(self):
        """Test aliasing between XMM, YMM, and ZMM registers"""
        assembly_code = """
        vmovss xmm0, xmm1
        vmovaps ymm0, ymm2
        vmovapd zmm0, zmm3
        vmovss xmm4, xmm0
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find WAW dependencies on zmm0 (all three instructions write to same physical reg)
        zmm0_waw_deps = [dep for dep in reg_deps if 
                         dep.dependency_type == 'WAW' and dep.resource == 'zmm0']
        self.assertEqual(len(zmm0_waw_deps), 2)  # line 0->1, line 1->2
        
        # Should find RAW dependency from zmm0 to zmm4 (line 2->3)
        raw_deps = [dep for dep in reg_deps if 
                    dep.dependency_type == 'RAW' and dep.resource == 'zmm0']
        self.assertEqual(len(raw_deps), 1)


class TestThreeOperandInstructions(unittest.TestCase):
    """Three-operand x86 instruction dependency tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
    def test_vfmadd_memory_destination_overlap(self):
        """Test FMA instruction where destination overlaps with source in memory"""
        assembly_code = """
        vmovss dword ptr [rax], xmm1
        vfmadd213ss dword ptr [rax], xmm2, xmm3
        vmovss xmm0, dword ptr [rax]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find RAW and WAR dependencies on memory location
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        war_deps = [dep for dep in memory_deps if dep.dependency_type == 'WAR']
        
        self.assertEqual(len(raw_deps), 1)
        self.assertEqual(len(war_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[rax]')
        self.assertEqual(war_deps[0].resource, '[rax]')
    
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
    
    def test_lea_three_operand_no_memory_dependency(self):
        """Test LEA doesn't create memory dependencies (address calculation only)"""
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
        """Test SHLD three-operand instructions with memory"""
        assembly_code = """
        mov dword ptr [r8], eax
        shld dword ptr [r8], ebx, 4
        mov ecx, dword ptr [r8]
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # SHLD reads and writes the first operand (memory location)
        memory_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
        raw_deps = [dep for dep in memory_deps if dep.dependency_type == 'RAW']
        
        # At least one RAW dependency (mov write -> shld read)
        self.assertGreaterEqual(len(raw_deps), 1)
        self.assertEqual(raw_deps[0].resource, '[r8]')


class TestMaskRegisterDependencies(unittest.TestCase):
    """AVX-512 mask register dependency tests"""
    
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
    
    def test_mask_register_with_merging_zeroing(self):
        """Test mask register with merging vs zeroing semantics"""
        assembly_code = """
        vpcmpeqd k3, zmm0, zmm1
        vmovaps zmm2{k3}, zmm3         
        vmovaps zmm4{k3}{z}, zmm5      
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


class TestAdvancedMemoryScenarios(unittest.TestCase):
    """Advanced memory dependency scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
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


class TestEdgeCasesAndStress(unittest.TestCase):
    """Edge cases and stress tests"""
    
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
    
    def test_register_normalization_correctness(self):
        """Test that register normalization works correctly"""
        test_cases = [
            ('al', 'rax'), ('ah', 'rax'), ('ax', 'rax'), ('eax', 'rax'), ('rax', 'rax'),
            ('bl', 'rbx'), ('bh', 'rbx'), ('bx', 'rbx'), ('ebx', 'rbx'), ('rbx', 'rbx'),
            ('r8b', 'r8'), ('r8w', 'r8'), ('r8d', 'r8'), ('r8', 'r8'),
            ('xmm0', 'zmm0'), ('ymm0', 'zmm0'), ('zmm0', 'zmm0'),
            ('xmm15', 'zmm15'), ('ymm31', 'zmm31'), ('zmm31', 'zmm31')
        ]
        
        for input_reg, expected_output in test_cases:
            with self.subTest(input_reg=input_reg):
                normalized = self.visualizer.analyzer.parser.normalize_register(input_reg)
                self.assertEqual(normalized, expected_output,
                               f"Expected {input_reg} -> {expected_output}, got {normalized}")


class TestMixedDependencyScenarios(unittest.TestCase):
    """Test complex scenarios mixing multiple dependency types"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
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


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes in logical order
    suite.addTests(loader.loadTestsFromTestCase(TestBasicMemoryDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestSubRegisterDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestThreeOperandInstructions))
    suite.addTests(loader.loadTestsFromTestCase(TestMaskRegisterDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedMemoryScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCasesAndStress))
    suite.addTests(loader.loadTestsFromTestCase(TestMixedDependencyScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
