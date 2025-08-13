#!/usr/bin/env python3
"""
Unit tests for Sub-Register Dependencies in Data Flow Analyzer

Tests sub-register dependency detection for X86, X64, and SIMD registers
"""

import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dfg_analyzer import DataFlowVisualizer, DataDependency


class TestSubRegisterDependencies(unittest.TestCase):
    """Test cases for sub-register dependency analysis"""
    
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
    
    def test_8bit_high_low_interference(self):
        """Test interference between 8-bit high and low registers"""
        assembly_code = """
        mov al, bl
        mov ah, cl
        mov dl, al
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        # Should find dependencies within rax register family
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Check for RAW from line 0 to line 2 (al -> dl via rax)
        rax_deps = [dep for dep in reg_deps if dep.resource == 'rax']
        self.assertGreater(len(rax_deps), 0)
    
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
    
    def test_16bit_register_dependencies(self):
        """Test 16-bit register dependencies"""
        assembly_code = """
        mov ax, bx
        mov cx, ax
        mov dx, cx
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find RAW dependencies
        raw_deps = [dep for dep in reg_deps if dep.dependency_type == 'RAW']
        self.assertEqual(len(raw_deps), 2)  # ax->cx, cx->dx
    
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


class TestSIMDRegisterDependencies(unittest.TestCase):
    """Test cases for SIMD register (XMM/YMM/ZMM) dependencies"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
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
    
    def test_xmm_scalar_vs_vector(self):
        """Test scalar vs vector operations on XMM registers"""
        assembly_code = """
        vmovss xmm0, xmm1
        vmovaps xmm0, xmm2
        vmovsd xmm3, xmm0
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find WAW on zmm0 and RAW from zmm0
        zmm0_deps = [dep for dep in reg_deps if dep.resource == 'zmm0']
        self.assertGreater(len(zmm0_deps), 0)
    
    def test_ymm_lower_upper_lanes(self):
        """Test YMM register lower/upper lane dependencies"""
        assembly_code = """
        vmovaps ymm0, ymm1
        vextractf128 xmm2, ymm0, 1
        vinsertf128 ymm3, ymm0, xmm2, 1
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find RAW dependencies from ymm0
        ymm0_raw_deps = [dep for dep in reg_deps if 
                         dep.dependency_type == 'RAW' and dep.resource == 'zmm0']
        self.assertGreater(len(ymm0_raw_deps), 0)
    
    def test_zmm_masking_operations(self):
        """Test ZMM register operations with masking"""
        assembly_code = """
        vmovaps zmm0, zmm1
        vmovaps zmm0{k1}, zmm2
        vmovaps zmm3, zmm0
        """
        
        instructions = self.visualizer.analyzer.parse_basic_block(assembly_code)
        dependencies = self.visualizer.analyzer.find_dependencies(instructions)
        
        reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
        
        # Should find dependencies on zmm0
        zmm0_deps = [dep for dep in reg_deps if dep.resource == 'zmm0']
        self.assertGreater(len(zmm0_deps), 0)
    
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


class TestComplexSubRegisterScenarios(unittest.TestCase):
    """Test complex sub-register dependency scenarios"""
    
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


class TestEdgeCasesSubRegisters(unittest.TestCase):
    """Test edge cases for sub-register dependencies"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = DataFlowVisualizer()
    
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


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSubRegisterDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestSIMDRegisterDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexSubRegisterScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCasesSubRegisters))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
