#!/usr/bin/env python3
"""
Memory Dependency Test Demonstration

This script demonstrates various memory dependency scenarios and shows
how the data flow analyzer detects and classifies them.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_flow_visualizer import DataFlowVisualizer


def test_memory_dependency_scenario(name: str, assembly_code: str):
    """Test and display a memory dependency scenario"""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name}")
    print(f"{'='*60}")
    
    print("Assembly Code:")
    print("-" * 20)
    for i, line in enumerate(assembly_code.strip().split('\n')):
        if line.strip():
            print(f"Line {i}: {line.strip()}")
    
    visualizer = DataFlowVisualizer()
    instructions = visualizer.analyzer.parse_basic_block(assembly_code)
    dependencies = visualizer.analyzer.find_dependencies(instructions)
    
    # Separate dependencies by operand type
    reg_deps = [dep for dep in dependencies if dep.operand_type == 'register']
    mem_deps = [dep for dep in dependencies if dep.operand_type == 'memory']
    
    print(f"\nResults:")
    print(f"  Total dependencies: {len(dependencies)}")
    print(f"  Register dependencies: {len(reg_deps)}")
    print(f"  Memory dependencies: {len(mem_deps)}")
    
    if mem_deps:
        print(f"\nMemory Dependencies:")
        for dep in mem_deps:
            print(f"  {dep.dependency_type}: Line {dep.source_line} -> Line {dep.target_line}")
            print(f"    Resource: {dep.resource}")
            print(f"    Type: {dep.operand_type}")
    else:
        print(f"\nNo memory dependencies found")


def main():
    """Run memory dependency test demonstrations"""
    print("Memory Dependency Analysis Test Suite")
    print("=====================================")
    
    # Test Case 1: Basic RAW memory dependency
    test_memory_dependency_scenario(
        "Basic Read-After-Write Memory Dependency",
        """
        mov dword ptr [rax], ebx
        mov ecx, dword ptr [rax]
        """
    )
    
    # Test Case 2: WAR memory dependency
    test_memory_dependency_scenario(
        "Write-After-Read Memory Dependency",
        """
        mov eax, dword ptr [rbx]
        mov dword ptr [rbx], ecx
        """
    )
    
    # Test Case 3: WAW memory dependency
    test_memory_dependency_scenario(
        "Write-After-Write Memory Dependency",
        """
        mov dword ptr [rdx], eax
        mov dword ptr [rdx], ebx
        """
    )
    
    # Test Case 4: Complex memory addressing
    test_memory_dependency_scenario(
        "Complex Memory Addressing",
        """
        mov dword ptr [rax + rbx*2 + 8], ecx
        mov edx, dword ptr [rax + rbx*2 + 8]
        """
    )
    
    # Test Case 5: No memory dependencies (different addresses)
    test_memory_dependency_scenario(
        "Different Memory Locations (No Dependencies)",
        """
        mov dword ptr [rax], ebx
        mov ecx, dword ptr [rdx]
        """
    )
    
    # Test Case 6: Mixed register and memory dependencies
    test_memory_dependency_scenario(
        "Mixed Register and Memory Dependencies",
        """
        mov eax, ebx
        mov dword ptr [rcx], eax
        mov edx, dword ptr [rcx]
        mov eax, edx
        """
    )
    
    # Test Case 7: Floating-point memory operations
    test_memory_dependency_scenario(
        "Floating-Point Memory Operations",
        """
        vmovss dword ptr [rax], xmm0
        vmovss xmm1, dword ptr [rax]
        """
    )
    
    # Test Case 8: Different memory sizes
    test_memory_dependency_scenario(
        "Different Memory Operation Sizes",
        """
        mov byte ptr [rax], bl
        mov cx, word ptr [rax]
        """
    )
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print("Memory dependency detection covers:")
    print("✓ Read-After-Write (RAW) dependencies")
    print("✓ Write-After-Read (WAR) dependencies") 
    print("✓ Write-After-Write (WAW) dependencies")
    print("✓ Complex memory addressing modes")
    print("✓ Different operation sizes")
    print("✓ Floating-point memory operations")
    print("✓ Conservative analysis (same expression = same location)")
    print("✓ Operand type classification (register vs memory)")


if __name__ == '__main__':
    main()
