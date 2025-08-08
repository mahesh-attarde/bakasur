"""
Unit tests for CFG Analyzer models

Tests the core data structures: Instruction, BasicBlock, and ControlFlowGraph
"""

import unittest
from src.cfg_analyzer.models import (
    Instruction, BasicBlock, ControlFlowGraph, TerminatorType
)


class TestInstruction(unittest.TestCase):
    """Test cases for Instruction class"""
    
    def test_instruction_creation(self):
        """Test basic instruction creation"""
        inst = Instruction(
            line_number=10,
            opcode="mov",
            operands="eax, ebx",
            raw_line="  mov eax, ebx"
        )
        
        self.assertEqual(inst.line_number, 10)
        self.assertEqual(inst.opcode, "mov")
        self.assertEqual(inst.operands, "eax, ebx")
        self.assertEqual(inst.raw_line, "  mov eax, ebx")
        self.assertFalse(inst.is_terminator)
        self.assertIsNone(inst.terminator_type)
        self.assertEqual(inst.jump_targets, [])
    
    def test_terminator_instruction(self):
        """Test terminator instruction creation"""
        inst = Instruction(
            line_number=20,
            opcode="jmp",
            operands=".L1",
            raw_line="  jmp .L1",
            is_terminator=True,
            terminator_type=TerminatorType.UNCONDITIONAL_JUMP,
            jump_targets=["L1"]
        )
        
        self.assertTrue(inst.is_terminator)
        self.assertEqual(inst.terminator_type, TerminatorType.UNCONDITIONAL_JUMP)
        self.assertEqual(inst.jump_targets, ["L1"])


class TestBasicBlock(unittest.TestCase):
    """Test cases for BasicBlock class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.block = BasicBlock(
            label="bb_0",
            start_line=1,
            end_line=5
        )
        
        # Add some test instructions
        inst1 = Instruction(1, "push", "rbp", "push rbp")
        inst2 = Instruction(2, "mov", "rbp, rsp", "mov rbp, rsp")
        inst3 = Instruction(3, "jmp", ".L1", "jmp .L1", 
                          is_terminator=True, 
                          terminator_type=TerminatorType.UNCONDITIONAL_JUMP,
                          jump_targets=["L1"])
        
        self.block.instructions = [inst1, inst2, inst3]
    
    def test_basic_block_creation(self):
        """Test basic block creation"""
        self.assertEqual(self.block.label, "bb_0")
        self.assertEqual(self.block.start_line, 1)
        self.assertEqual(self.block.end_line, 5)
        self.assertEqual(len(self.block.instructions), 3)
        self.assertFalse(self.block.is_unreachable)
        self.assertEqual(self.block.background_color, "white")
    
    def test_is_entry_block(self):
        """Test entry block detection"""
        # No predecessors = entry block
        self.assertTrue(self.block.is_entry_block)
        
        # Add predecessor
        self.block.predecessors.add("bb_1")
        self.assertFalse(self.block.is_entry_block)
    
    def test_is_exit_block(self):
        """Test exit block detection"""
        # No successors = exit block
        self.assertTrue(self.block.is_exit_block)
        
        # Add successor
        self.block.successors.add("bb_1")
        self.assertFalse(self.block.is_exit_block)
    
    def test_terminator_property(self):
        """Test terminator instruction detection"""
        terminator = self.block.terminator
        self.assertIsNotNone(terminator)
        self.assertEqual(terminator.opcode, "jmp")
        self.assertTrue(terminator.is_terminator)
    
    def test_no_terminator(self):
        """Test block with no terminator"""
        block = BasicBlock("bb_1", 6, 8)
        inst = Instruction(6, "mov", "eax, 0", "mov eax, 0")
        block.instructions = [inst]
        
        self.assertIsNone(block.terminator)


class TestControlFlowGraph(unittest.TestCase):
    """Test cases for ControlFlowGraph class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cfg = ControlFlowGraph("test_func", "bb_0")
        
        # Create test blocks
        bb_0 = BasicBlock("bb_0", 1, 3)
        bb_1 = BasicBlock("bb_1", 4, 6)
        bb_2 = BasicBlock("bb_2", 7, 9)
        
        self.cfg.basic_blocks = {
            "bb_0": bb_0,
            "bb_1": bb_1,
            "bb_2": bb_2
        }
    
    def test_cfg_creation(self):
        """Test CFG creation"""
        self.assertEqual(self.cfg.function_name, "test_func")
        self.assertEqual(self.cfg.entry_block, "bb_0")
        self.assertEqual(len(self.cfg.basic_blocks), 3)
    
    def test_add_edge(self):
        """Test edge addition"""
        self.cfg.add_edge("bb_0", "bb_1")
        
        self.assertIn("bb_1", self.cfg.basic_blocks["bb_0"].successors)
        self.assertIn("bb_0", self.cfg.basic_blocks["bb_1"].predecessors)
    
    def test_get_reachable_blocks(self):
        """Test reachable block detection"""
        # Add edges: bb_0 -> bb_1, bb_2 is unreachable
        self.cfg.add_edge("bb_0", "bb_1")
        
        reachable = self.cfg.get_reachable_blocks()
        self.assertIn("bb_0", reachable)
        self.assertIn("bb_1", reachable)
        self.assertNotIn("bb_2", reachable)
    
    def test_detect_back_edges_simple_loop(self):
        """Test back edge detection for simple self-loop"""
        # Create self-loop: bb_1 -> bb_1
        self.cfg.add_edge("bb_0", "bb_1")
        self.cfg.add_edge("bb_1", "bb_1")  # Self-loop
        
        back_edges = self.cfg.detect_back_edges()
        self.assertIn(("bb_1", "bb_1"), back_edges)
    
    def test_detect_back_edges_cycle(self):
        """Test back edge detection for cycle"""
        # Create cycle: bb_0 -> bb_1 -> bb_2 -> bb_0
        self.cfg.add_edge("bb_0", "bb_1")
        self.cfg.add_edge("bb_1", "bb_2")
        self.cfg.add_edge("bb_2", "bb_0")  # Back edge
        
        back_edges = self.cfg.detect_back_edges()
        self.assertIn(("bb_2", "bb_0"), back_edges)
    
    def test_optimize_marks_unreachable(self):
        """Test optimization marks unreachable blocks"""
        # Only bb_0 -> bb_1, bb_2 is unreachable
        self.cfg.add_edge("bb_0", "bb_1")
        
        self.cfg.optimize()
        
        self.assertFalse(self.cfg.basic_blocks["bb_0"].is_unreachable)
        self.assertFalse(self.cfg.basic_blocks["bb_1"].is_unreachable)
        self.assertTrue(self.cfg.basic_blocks["bb_2"].is_unreachable)
    
    def test_optimize_sets_colors(self):
        """Test optimization sets block colors"""
        self.cfg.add_edge("bb_0", "bb_1")
        # bb_0 = entry, bb_1 = exit, bb_2 = unreachable
        
        self.cfg.optimize()
        
        self.assertEqual(self.cfg.basic_blocks["bb_0"].background_color, "lightgreen")  # entry
        self.assertEqual(self.cfg.basic_blocks["bb_1"].background_color, "lightcoral")  # exit
        self.assertEqual(self.cfg.basic_blocks["bb_2"].background_color, "grey")  # unreachable
    
    def test_get_loops(self):
        """Test loop detection"""
        # Create a simple loop: bb_0 -> bb_1 -> bb_0
        self.cfg.add_edge("bb_0", "bb_1")
        self.cfg.add_edge("bb_1", "bb_0")
        
        loops = self.cfg.get_loops()
        self.assertGreater(len(loops), 0)
        
        # Should find a loop containing bb_0 and bb_1
        loop_found = False
        for loop in loops:
            if "bb_0" in loop and "bb_1" in loop:
                loop_found = True
                break
        self.assertTrue(loop_found)


if __name__ == '__main__':
    unittest.main()
