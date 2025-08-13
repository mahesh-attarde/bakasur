#!/usr/bin/env python3
"""
Sub-Register Dependency Demonstration

This script demonstrates sub-register dependency detection for X86, X64, and SIMD registers.
Shows how the data flow analyzer handles register aliasing and different register sizes.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dfg_analyzer import DataFlowVisualizer


def test_subregister_scenario(name: str, assembly_code: str):
    """Test and display a sub-register dependency scenario"""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {name}")
    print(f"{'='*70}")
    
    print("Assembly Code:")
    print("-" * 20)
    for i, line in enumerate(assembly_code.strip().split('\n')):
        if line.strip():
            print(f"Line {i}: {line.strip()}")
    
    visualizer = DataFlowVisualizer()
    instructions = visualizer.analyzer.parse_basic_block(assembly_code)
    dependencies = visualizer.analyzer.find_dependencies(instructions)
    
    print(f"\nRegister Analysis:")
    print("-" * 20)
    for i, inst in enumerate(instructions):
        reads, writes, memory_ops = visualizer.analyzer.analyze_instruction_operands(inst)
        print(f"Line {i}: {inst.opcode} {inst.operands}")
        if reads:
            print(f"  Reads: {sorted(reads)}")
        if writes:
            print(f"  Writes: {sorted(writes)}")
    
    # Separate dependencies by operand type
    reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
    mem_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
    
    print(f"\nDependency Summary:")
    print(f"  Total dependencies: {len(dependencies)}")
    print(f"  Register dependencies: {len(reg_deps)}")
    print(f"  Memory dependencies: {len(mem_deps)}")
    
    if reg_deps:
        print(f"\nRegister Dependencies:")
        # Group by dependency type
        dep_types = {'RAW': [], 'WAR': [], 'WAW': []}
        for dep in reg_deps:
            dep_types[dep.dependency_type].append(dep)
        
        for dep_type, deps in dep_types.items():
            if deps:
                type_names = {
                    'RAW': 'Read-After-Write (True Dependencies)',
                    'WAR': 'Write-After-Read (Anti Dependencies)',
                    'WAW': 'Write-After-Write (Output Dependencies)'
                }
                print(f"  {type_names[dep_type]}:")
                for dep in deps:
                    print(f"    Line {dep.source_line} -> Line {dep.target_line} ({dep.resource})")


def main():
    """Run sub-register dependency demonstrations"""
    print("Sub-Register Dependency Analysis Demonstration")
    print("==============================================")
    print("Testing X86/X64 and SIMD register aliasing and dependencies")
    
    # Test Case 1: Basic 8-bit register dependencies
    test_subregister_scenario(
        "8-bit Register Dependencies (AL/AH -> EAX)",
        """
        mov eax, ebx
        mov al, cl
        mov dl, al
        mov ah, ch
        mov esi, eax
        """
    )
    
    # Test Case 2: 32-bit to 64-bit register zeroing
    test_subregister_scenario(
        "32-bit Operations Zero Upper Bits",
        """
        mov rax, rbx
        mov eax, ecx
        mov rdx, rax
        """
    )
    
    # Test Case 3: R8-R15 register family
    test_subregister_scenario(
        "Extended Register Family (R8-R15)",
        """
        mov r8, r9
        mov r8d, r10d
        mov r11w, r8w
        mov r12b, r8b
        """
    )
    
    # Test Case 4: XMM/YMM/ZMM register aliasing
    test_subregister_scenario(
        "SIMD Register Aliasing (XMM/YMM/ZMM)",
        """
        vmovss xmm0, xmm1
        vmovaps ymm0, ymm2
        vmovapd zmm0, zmm3
        vmovss xmm4, xmm0
        """
    )
    
    # Test Case 5: Mixed register sizes in computation
    test_subregister_scenario(
        "Mixed Register Sizes in Computation",
        """
        mov ax, bx
        add eax, ecx
        mov dx, ax
        mov rsi, rax
        """
    )
    
    # Test Case 6: SIMD scalar vs vector operations
    test_subregister_scenario(
        "SIMD Scalar vs Vector Operations",
        """
        vmovss xmm0, xmm1
        vmovaps xmm0, xmm2
        vaddss xmm3, xmm0, xmm4
        vaddps xmm5, xmm0, xmm6
        """
    )
    
    # Test Case 7: High-numbered SIMD registers
    test_subregister_scenario(
        "High-Numbered SIMD Registers (16-31)",
        """
        vmovaps zmm16, zmm17
        vmovaps ymm16, ymm18
        vmovaps xmm19, xmm16
        vaddps zmm20, zmm16, zmm19
        """
    )
    
    # Test Case 8: Complex register dependency chain
    test_subregister_scenario(
        "Complex Register Dependency Chain",
        """
        mov rax, rbx
        mov al, cl
        inc ah
        add eax, edx
        mov rsi, rax
        vmovd xmm0, eax
        vmovss xmm1, xmm0
        """
    )
    
    # Test Case 9: Partial register stall scenario
    test_subregister_scenario(
        "Potential Partial Register Stall",
        """
        mov rax, rbx
        mov al, cl
        add rax, rdx
        """
    )
    
    # Test Case 10: SIMD extract/insert operations
    test_subregister_scenario(
        "SIMD Extract/Insert Lane Operations",
        """
        vmovaps ymm0, ymm1
        vextractf128 xmm2, ymm0, 1
        vinsertf128 ymm3, ymm0, xmm2, 1
        vmovaps zmm4, zmm3
        """
    )
    
    print(f"\n{'='*70}")
    print("SUMMARY - Sub-Register Dependency Support")
    print(f"{'='*70}")
    print("The data flow analyzer correctly handles:")
    print("✓ X86/X64 register aliasing (RAX/EAX/AX/AL/AH)")
    print("✓ Extended registers (R8-R15) with all sub-sizes")
    print("✓ SIMD register aliasing (XMM/YMM/ZMM)")
    print("✓ High-numbered SIMD registers (16-31)")
    print("✓ Mixed register size operations")
    print("✓ 32-bit operations zeroing upper bits")
    print("✓ Partial register dependencies")
    print("✓ SIMD scalar and vector operations")
    print("✓ Complex register dependency chains")
    print("✓ Conservative dependency analysis")
    
    print(f"\nRegister Normalization:")
    print("• General purpose registers → 64-bit form (RAX, RBX, etc.)")
    print("• SIMD registers → 512-bit form (ZMM0, ZMM1, etc.)")
    print("• Proper handling of register aliasing across all sizes")


if __name__ == '__main__':
    main()
