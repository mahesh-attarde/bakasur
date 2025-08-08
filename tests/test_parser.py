"""
Unit tests for CFG Parser

Tests the assembly parsing and CFG construction functionality
"""

import unittest
import tempfile
import os
from src.cfg_analyzer.intel_parser import CFGAssemblyParser
from src.cfg_analyzer.models import TerminatorType


class TestCFGAssemblyParser(unittest.TestCase):
    """Test cases for CFG Assembly Parser"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = CFGAssemblyParser()
    
    def test_extract_function_name_from_type(self):
        """Test function name extraction from .type directive"""
        line = ".type test_function, @function"
        name = self.parser._extract_function_name_from_type(line)
        self.assertEqual(name, "test_function")
        
        # Test with spacing variations
        line2 = ".type  my_func  ,  @function"
        name2 = self.parser._extract_function_name_from_type(line2)
        self.assertEqual(name2, "my_func")
        
        # Test non-function type
        line3 = ".type data_var, @object"
        name3 = self.parser._extract_function_name_from_type(line3)
        self.assertIsNone(name3)
    
    def test_is_function_label(self):
        """Test function label detection"""
        self.assertTrue(self.parser._is_function_label("test_function:", "test_function"))
        self.assertTrue(self.parser._is_function_label("  test_function:  ", "test_function"))
        self.assertFalse(self.parser._is_function_label("other_function:", "test_function"))
    
    def test_is_terminator_opcode(self):
        """Test terminator opcode detection"""
        # Unconditional jumps
        self.assertTrue(self.parser._is_terminator_opcode("jmp"))
        self.assertTrue(self.parser._is_terminator_opcode("br"))
        
        # Conditional jumps
        self.assertTrue(self.parser._is_terminator_opcode("je"))
        self.assertTrue(self.parser._is_terminator_opcode("jne"))
        self.assertTrue(self.parser._is_terminator_opcode("jl"))
        
        # Returns
        self.assertTrue(self.parser._is_terminator_opcode("ret"))
        self.assertTrue(self.parser._is_terminator_opcode("retq"))
        
        # Non-terminators
        self.assertFalse(self.parser._is_terminator_opcode("mov"))
        self.assertFalse(self.parser._is_terminator_opcode("add"))
        self.assertFalse(self.parser._is_terminator_opcode("call"))
    
    def test_get_terminator_type(self):
        """Test terminator type classification"""
        self.assertEqual(
            self.parser._get_terminator_type("jmp"),
            TerminatorType.UNCONDITIONAL_JUMP
        )
        self.assertEqual(
            self.parser._get_terminator_type("je"),
            TerminatorType.CONDITIONAL_JUMP
        )
        self.assertEqual(
            self.parser._get_terminator_type("ret"),
            TerminatorType.RETURN
        )
        self.assertIsNone(self.parser._get_terminator_type("mov"))
    
    def test_extract_jump_targets(self):
        """Test jump target extraction"""
        # Single target
        targets = self.parser._extract_jump_targets(".LBB0_1")
        self.assertEqual(targets, ["LBB0_1"])
        
        # Multiple targets (shouldn't happen in real assembly, but test robustness)
        targets2 = self.parser._extract_jump_targets("test .LBB0_1 and .LBB0_2")
        self.assertEqual(set(targets2), {"LBB0_1", "LBB0_2"})
        
        # No targets
        targets3 = self.parser._extract_jump_targets("eax, ebx")
        self.assertEqual(targets3, [])
    
    def test_parse_instruction(self):
        """Test instruction parsing"""
        # Regular instruction
        inst = self.parser._parse_instruction("  mov eax, ebx", 10)
        self.assertIsNotNone(inst)
        self.assertEqual(inst.opcode, "mov")
        self.assertEqual(inst.operands, "eax, ebx")
        self.assertEqual(inst.line_number, 10)
        self.assertFalse(inst.is_terminator)
        
        # Terminator instruction
        inst2 = self.parser._parse_instruction("  jmp .L1", 15)
        self.assertIsNotNone(inst2)
        self.assertEqual(inst2.opcode, "jmp")
        self.assertTrue(inst2.is_terminator)
        self.assertEqual(inst2.jump_targets, ["L1"])
        
        # Skip comments and directives
        self.assertIsNone(self.parser._parse_instruction("# comment", 20))
        self.assertIsNone(self.parser._parse_instruction(".directive", 21))
        self.assertIsNone(self.parser._parse_instruction("", 22))
    
    def test_find_basic_block_starts(self):
        """Test basic block boundary detection"""
        lines = [
            "test_func:",          # 0 - function start
            "  push rbp",          # 1 - first instruction
            "  mov rbp, rsp",      # 2 - regular instruction
            "  jmp .L1",           # 3 - terminator
            ".L1:",                # 4 - label (new block)
            "  mov eax, 0",        # 5 - instruction
            "  ret"                # 6 - terminator
        ]
        
        starts = self.parser._find_basic_block_starts(lines)
        
        # Should start at: 0 (function), 4 (after terminator/label), 5 (after label)
        expected_starts = {0, 4}  # Line 4 is the label, line 5 would be after terminator
        self.assertTrue(starts.issuperset(expected_starts))
    
    def test_parse_simple_function(self):
        """Test parsing a simple function"""
        assembly_code = """.type test_func, @function
test_func:
    push rbp
    mov rbp, rsp
    mov eax, 0
    ret
.Lfunc_end0:
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write(assembly_code)
            temp_path = f.name
        
        try:
            cfgs = self.parser.parse_file_with_cfg(temp_path)
            
            self.assertIn("test_func", cfgs)
            cfg = cfgs["test_func"]
            
            self.assertEqual(cfg.function_name, "test_func")
            self.assertGreater(len(cfg.basic_blocks), 0)
            
            # Should have at least one block with instructions
            total_instructions = sum(len(block.instructions) for block in cfg.basic_blocks.values())
            self.assertGreater(total_instructions, 0)
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_function_with_loop(self):
        """Test parsing a function with a loop"""
        assembly_code = """.type loop_func, @function
loop_func:
    push rbp
    mov rbp, rsp
    mov eax, 0
.L1:
    inc eax
    cmp eax, 10
    jl .L1
    ret
.Lfunc_end1:
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write(assembly_code)
            temp_path = f.name
        
        try:
            cfgs = self.parser.parse_file_with_cfg(temp_path)
            
            self.assertIn("loop_func", cfgs)
            cfg = cfgs["loop_func"]
            
            # Should detect back edges (loops)
            back_edges = cfg.detect_back_edges()
            self.assertGreater(len(back_edges), 0)
            
            # Should have multiple blocks
            self.assertGreater(len(cfg.basic_blocks), 1)
            
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """Test handling of non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file_with_cfg("nonexistent_file.s")
    
    def test_empty_file(self):
        """Test handling of empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            cfgs = self.parser.parse_file_with_cfg(temp_path)
            self.assertEqual(len(cfgs), 0)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
