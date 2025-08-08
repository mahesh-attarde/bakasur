#!/usr/bin/env python3
"""
Test AT&T Assembly Syntax Support

Tests for the new AT&T assembly syntax parsing functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cfg_analyzer import (
    AssemblyParserFactory, 
    AssemblySyntax, 
    IntelAssemblyParser, 
    ATTAssemblyParser,
    CFGAssemblyParser  # Backward compatibility
)


class TestSyntaxSupport(unittest.TestCase):
    """Test assembly syntax support"""
    
    def test_assembly_syntax_enum(self):
        """Test AssemblySyntax enum"""
        self.assertEqual(AssemblySyntax.INTEL.value, "intel")
        self.assertEqual(AssemblySyntax.ATT.value, "att")
    
    def test_parser_factory_intel(self):
        """Test factory creates Intel parser"""
        parser = AssemblyParserFactory.create_parser(AssemblySyntax.INTEL)
        self.assertIsInstance(parser, IntelAssemblyParser)
        
        parser = AssemblyParserFactory.create_parser("intel")
        self.assertIsInstance(parser, IntelAssemblyParser)
    
    def test_parser_factory_att(self):
        """Test factory creates AT&T parser"""
        parser = AssemblyParserFactory.create_parser(AssemblySyntax.ATT)
        self.assertIsInstance(parser, ATTAssemblyParser)
        
        parser = AssemblyParserFactory.create_parser("att")
        self.assertIsInstance(parser, ATTAssemblyParser)
    
    def test_parser_factory_default(self):
        """Test factory defaults to Intel"""
        parser = AssemblyParserFactory.create_parser()
        self.assertIsInstance(parser, IntelAssemblyParser)
    
    def test_parser_factory_invalid_syntax(self):
        """Test factory raises error for invalid syntax"""
        with self.assertRaises(ValueError):
            AssemblyParserFactory.create_parser("invalid")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with original class name"""
        parser = CFGAssemblyParser()
        self.assertIsInstance(parser, IntelAssemblyParser)
    
    def test_supported_syntaxes(self):
        """Test getting supported syntaxes"""
        syntaxes = AssemblyParserFactory.get_supported_syntaxes()
        self.assertIn("intel", syntaxes)
        self.assertIn("att", syntaxes)


class TestATTParser(unittest.TestCase):
    """Test AT&T assembly parser"""
    
    def setUp(self):
        """Set up test parser"""
        self.parser = ATTAssemblyParser()
    
    def test_att_terminator_instructions(self):
        """Test AT&T terminator instruction recognition"""
        # Test basic terminators
        self.assertTrue(self.parser._is_terminator_opcode("jmp"))
        self.assertTrue(self.parser._is_terminator_opcode("je"))
        self.assertTrue(self.parser._is_terminator_opcode("retq"))
        
        # Test AT&T suffix variants
        self.assertTrue(self.parser._is_terminator_opcode("jmpq"))
        self.assertTrue(self.parser._is_terminator_opcode("jeq"))
        self.assertTrue(self.parser._is_terminator_opcode("retl"))
        
        # Test non-terminators
        self.assertFalse(self.parser._is_terminator_opcode("movq"))
        self.assertFalse(self.parser._is_terminator_opcode("pushq"))
    
    def test_att_jump_target_extraction(self):
        """Test AT&T jump target extraction"""
        # Test different AT&T jump target formats
        targets = self.parser._extract_jump_targets(".loop_start")
        self.assertIn("loop_start", targets)
        
        targets = self.parser._extract_jump_targets("$.loop_start")
        self.assertIn("loop_start", targets)
        
        targets = self.parser._extract_jump_targets("label")
        self.assertIn("label", targets)
        
        targets = self.parser._extract_jump_targets("$label")
        self.assertIn("label", targets)


class TestIntelParser(unittest.TestCase):
    """Test Intel assembly parser (refactored)"""
    
    def setUp(self):
        """Set up test parser"""
        self.parser = IntelAssemblyParser()
    
    def test_intel_terminator_instructions(self):
        """Test Intel terminator instruction recognition"""
        self.assertTrue(self.parser._is_terminator_opcode("jmp"))
        self.assertTrue(self.parser._is_terminator_opcode("je"))
        self.assertTrue(self.parser._is_terminator_opcode("ret"))
        
        self.assertFalse(self.parser._is_terminator_opcode("mov"))
        self.assertFalse(self.parser._is_terminator_opcode("push"))
    
    def test_intel_jump_target_extraction(self):
        """Test Intel jump target extraction"""
        targets = self.parser._extract_jump_targets(".loop_start")
        self.assertIn("loop_start", targets)


class TestSyntaxDetection(unittest.TestCase):
    """Test automatic syntax detection"""
    
    def test_detect_intel_syntax(self):
        """Test detection of Intel syntax"""
        intel_code = """
        mov eax, 10
        cmp eax, 5
        jl loop_start
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write(intel_code)
            f.flush()
            
            syntax = AssemblyParserFactory.detect_syntax(f.name)
            self.assertEqual(syntax, AssemblySyntax.INTEL)
            
            os.unlink(f.name)
    
    def test_detect_att_syntax(self):
        """Test detection of AT&T syntax"""
        att_code = """
        movl $10, %eax
        cmpl $5, %eax
        jl .loop_start
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write(att_code)
            f.flush()
            
            syntax = AssemblyParserFactory.detect_syntax(f.name)
            self.assertEqual(syntax, AssemblySyntax.ATT)
            
            os.unlink(f.name)
    
    def test_detect_syntax_file_not_found(self):
        """Test syntax detection with non-existent file defaults to Intel"""
        syntax = AssemblyParserFactory.detect_syntax("nonexistent.s")
        self.assertEqual(syntax, AssemblySyntax.INTEL)


class TestATTAssemblyParsing(unittest.TestCase):
    """Test parsing of actual AT&T assembly code"""
    
    def test_parse_att_function(self):
        """Test parsing an AT&T function"""
        att_code = """
	.text
	.globl	test_function_att
	.type	test_function_att, @function
test_function_att:
	pushq %rbp
	movq %rsp, %rbp
	movl $0, %eax
.loop:
	incl %eax
	cmpl $10, %eax
	jl .loop
	retq
.Lfunc_end0:
	.size	test_function_att, .Lfunc_end0-test_function_att
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write(att_code)
            f.flush()
            
            parser = ATTAssemblyParser()
            cfgs = parser.parse_file_with_cfg(f.name)
            
            self.assertIn("test_function_att", cfgs)
            cfg = cfgs["test_function_att"]
            
            # Check that we have blocks
            self.assertGreater(len(cfg.basic_blocks), 0)
            
            # Check that instructions are parsed correctly
            found_att_instruction = False
            for block in cfg.basic_blocks.values():
                for instruction in block.instructions:
                    # Should find AT&T syntax instructions with % and $
                    if '%' in instruction.operands or '$' in instruction.operands:
                        found_att_instruction = True
                        break
            
            self.assertTrue(found_att_instruction, "Should find AT&T syntax instructions")
            
            os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
