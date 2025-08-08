"""
Unit tests for CFG Visualization

Tests the visualization and DOT export functionality
"""

import unittest
import tempfile
import os
from src.cfg_analyzer.models import BasicBlock, ControlFlowGraph, Instruction, TerminatorType
from src.cfg_analyzer.visualization import (
    export_cfg_to_dot, _get_node_style, _create_detailed_node_label, 
    _create_summary_node_label, print_cfg_summary, print_cfg_detailed
)
from io import StringIO
import sys


class TestVisualization(unittest.TestCase):
    """Test cases for CFG visualization functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a simple CFG for testing
        self.cfg = ControlFlowGraph("test_func", "bb_0")
        
        # Create test blocks
        bb_0 = BasicBlock("bb_0", 1, 3)
        bb_1 = BasicBlock("bb_1", 4, 6) 
        bb_2 = BasicBlock("bb_2", 7, 9)
        
        # Add instructions to bb_0
        inst1 = Instruction(1, "push", "rbp", "push rbp")
        inst2 = Instruction(2, "mov", "rbp, rsp", "mov rbp, rsp")
        inst3 = Instruction(3, "jmp", ".bb_1", "jmp .bb_1",
                          is_terminator=True,
                          terminator_type=TerminatorType.UNCONDITIONAL_JUMP,
                          jump_targets=["bb_1"])
        bb_0.instructions = [inst1, inst2, inst3]
        
        # Add instructions to bb_1
        inst4 = Instruction(4, "mov", "eax, 0", "mov eax, 0")
        inst5 = Instruction(5, "cmp", "eax, 10", "cmp eax, 10")
        inst6 = Instruction(6, "jl", ".bb_1", "jl .bb_1",
                          is_terminator=True,
                          terminator_type=TerminatorType.CONDITIONAL_JUMP,
                          jump_targets=["bb_1"])
        bb_1.instructions = [inst4, inst5, inst6]
        
        # Add instruction to bb_2 (exit block)
        inst7 = Instruction(7, "ret", "", "ret",
                          is_terminator=True,
                          terminator_type=TerminatorType.RETURN)
        bb_2.instructions = [inst7]
        
        self.cfg.basic_blocks = {"bb_0": bb_0, "bb_1": bb_1, "bb_2": bb_2}
        
        # Set up edges
        self.cfg.add_edge("bb_0", "bb_1")
        self.cfg.add_edge("bb_1", "bb_1")  # Self-loop
        self.cfg.add_edge("bb_1", "bb_2")
        
        # Apply optimizations
        self.cfg.optimize()
    
    def test_get_node_style_entry_block(self):
        """Test node styling for entry block"""
        style = _get_node_style(self.cfg.basic_blocks["bb_0"])
        self.assertIn("lightgreen", style)
        self.assertIn("filled,bold", style)
        self.assertIn("darkgreen", style)
    
    def test_get_node_style_exit_block(self):
        """Test node styling for exit block"""
        style = _get_node_style(self.cfg.basic_blocks["bb_2"])
        self.assertIn("lightcoral", style)
        self.assertIn("filled,bold", style)
        self.assertIn("darkred", style)
    
    def test_get_node_style_regular_block(self):
        """Test node styling for regular block"""
        style = _get_node_style(self.cfg.basic_blocks["bb_1"])
        self.assertIn("white", style)
        self.assertIn("style=filled", style)
        self.assertIn("black", style)
    
    def test_get_node_style_unreachable_block(self):
        """Test node styling for unreachable block"""
        # Create unreachable block
        unreachable = BasicBlock("bb_unreachable", 10, 12)
        unreachable.is_unreachable = True
        
        style = _get_node_style(unreachable)
        self.assertIn("lightgrey", style)
        self.assertIn("filled,dashed", style)
        self.assertIn("grey", style)
    
    def test_create_detailed_node_label(self):
        """Test detailed node label creation"""
        label = _create_detailed_node_label("bb_0", self.cfg.basic_blocks["bb_0"])
        
        # Should contain block info
        self.assertIn("[bb_0] ENTRY", label)
        self.assertIn("Lines: 1-3", label)
        
        # Should contain instructions
        self.assertIn("push", label)
        self.assertIn("mov", label)
        self.assertIn("jmp", label)
        
        # Should have terminator marker
        self.assertIn("[TERM]", label)
        
        # Should use left-aligned formatting
        self.assertIn("\\l", label)
    
    def test_create_detailed_node_label_with_limit(self):
        """Test detailed node label with instruction limit"""
        label = _create_detailed_node_label("bb_0", self.cfg.basic_blocks["bb_0"], max_instructions=2)
        
        # Should show only 2 instructions
        self.assertIn("push", label)
        self.assertIn("mov", label)
        # Should show truncation info
        self.assertIn("(1 more instructions)", label)
    
    def test_create_summary_node_label(self):
        """Test summary node label creation"""
        label = _create_summary_node_label("bb_0", self.cfg.basic_blocks["bb_0"])
        
        # Should contain basic info
        self.assertIn("Block: bb_0", label)
        self.assertIn("[ENTRY]", label)
        self.assertIn("Lines: 1-3", label)
        self.assertIn("Instructions: 3", label)
        self.assertIn("Terminator: jmp", label)
        
        # Should use left-aligned formatting
        self.assertIn("\\l", label)
    
    def test_export_cfg_to_dot(self):
        """Test DOT file export"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            temp_path = f.name
        
        try:
            export_cfg_to_dot(self.cfg, temp_path, include_instructions=True)
            
            # Verify file was created and has content
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Should contain DOT structure
            self.assertIn('digraph "test_func"', content)
            self.assertIn('rankdir=TB', content)
            self.assertIn('labeljust=l', content)
            
            # Should contain nodes
            self.assertIn('"bb_0"', content)
            self.assertIn('"bb_1"', content)
            self.assertIn('"bb_2"', content)
            
            # Should contain edges
            self.assertIn('"bb_0" -> "bb_1"', content)
            self.assertIn('"bb_1" -> "bb_2"', content)
            
            # Should have red back edge for loop
            self.assertIn('"bb_1" -> "bb_1"', content)
            self.assertIn('color=red', content)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_cfg_to_dot_summary_only(self):
        """Test DOT export with summary only"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            temp_path = f.name
        
        try:
            export_cfg_to_dot(self.cfg, temp_path, include_instructions=False)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Should not contain detailed instructions
            self.assertNotIn("push rbp", content)
            # Should contain block summary info
            self.assertIn("Block: bb_0", content)
            self.assertIn("Instructions: 3", content)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_print_cfg_summary(self):
        """Test CFG summary printing"""
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            print_cfg_summary(self.cfg)
            output = captured_output.getvalue()
            
            # Should contain function info
            self.assertIn("Function: test_func", output)
            self.assertIn("Entry Block: bb_0", output)
            self.assertIn("Total Blocks: 3", output)
            
            # Should contain loop info
            self.assertIn("Back Edges (Loop Edges): 1", output)
            self.assertIn("bb_1 -> bb_1", output)
            
            # Should contain block details
            self.assertIn("bb_0: lines 1-3", output)
            self.assertIn("bb_1: lines 4-6", output)
            self.assertIn("bb_2: lines 7-9", output)
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_print_cfg_detailed(self):
        """Test detailed CFG printing"""
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            print_cfg_detailed(self.cfg)
            output = captured_output.getvalue()
            
            # Should contain detailed function info
            self.assertIn("=== Detailed CFG for Function: test_func ===", output)
            
            # Should contain detailed block info
            self.assertIn("Basic Block: bb_0", output)
            self.assertIn("Type: ENTRY BLOCK", output)
            self.assertIn("Basic Block: bb_2", output)
            self.assertIn("Type: EXIT BLOCK", output)
            
            # Should contain instruction details
            self.assertIn("push", output)
            self.assertIn("mov", output)
            self.assertIn("jmp", output)
            self.assertIn("ret", output)
            
        finally:
            sys.stdout = sys.__stdout__


if __name__ == '__main__':
    unittest.main()
