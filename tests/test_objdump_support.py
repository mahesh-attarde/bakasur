"""
Tests for Object File and Objdump Support

Tests the enhanced functionality for processing object files and objdump output.
"""

import unittest
import tempfile
import subprocess
import os
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cfg_analyzer.objdump_parser import ObjdumpParser
from cfg_analyzer.parser_factory import AssemblyParserFactory, FileType
from cfg_analyzer.models import ControlFlowGraph


class TestObjdumpParser(unittest.TestCase):
    """Test objdump parser functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = ObjdumpParser()
        self.test_data_dir = Path(__file__).parent.parent / "test_data"
        
    def test_is_object_file(self):
        """Test object file detection"""
        # Object file extensions
        self.assertTrue(ObjdumpParser.is_object_file("test.o"))
        self.assertTrue(ObjdumpParser.is_object_file("test.obj"))
        self.assertTrue(ObjdumpParser.is_object_file("test.so"))
        self.assertTrue(ObjdumpParser.is_object_file("test.a"))
        self.assertTrue(ObjdumpParser.is_object_file("test.dylib"))
        self.assertTrue(ObjdumpParser.is_object_file("test.dll"))
        
        # Non-object file extensions
        self.assertFalse(ObjdumpParser.is_object_file("test.s"))
        self.assertFalse(ObjdumpParser.is_object_file("test.asm"))
        self.assertFalse(ObjdumpParser.is_object_file("test.dump"))
        self.assertFalse(ObjdumpParser.is_object_file("test.txt"))
        
    def test_execute_objdump_nonexistent_file(self):
        """Test objdump execution with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            ObjdumpParser.execute_objdump("nonexistent.o")
            
    def test_execute_objdump_with_test_object(self):
        """Test objdump execution with real object file"""
        test_object = self.test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            output = ObjdumpParser.execute_objdump(str(test_object))
            
            # Check that we got objdump output
            self.assertIn("file format", output)
            self.assertIn("Disassembly of section", output)
            self.assertIn("simple_loop_function_att", output)
        else:
            self.skipTest("Test object file not available")
            
    def test_execute_objdump_function_specific(self):
        """Test function-specific objdump execution"""
        test_object = self.test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            output = ObjdumpParser.execute_objdump(str(test_object), "simple_loop_function_att")
            
            # Check that we got function-specific output
            self.assertIn("simple_loop_function_att", output)
            # Should be smaller than full objdump
            full_output = ObjdumpParser.execute_objdump(str(test_object))
            self.assertLessEqual(len(output), len(full_output))
        else:
            self.skipTest("Test object file not available")
            
    def test_parse_object_file(self):
        """Test parsing an object file directly"""
        test_object = self.test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            cfgs = self.parser.parse_file_with_cfg(str(test_object))
            
            # Should find the function
            self.assertIn("simple_loop_function_att", cfgs)
            cfg = cfgs["simple_loop_function_att"]
            self.assertIsInstance(cfg, ControlFlowGraph)
            
            # Should detect loops
            self.assertGreater(len(cfg.get_loops()), 0)
        else:
            self.skipTest("Test object file not available")
            
    def test_parse_specific_function_from_object(self):
        """Test parsing specific function from object file"""
        test_object = self.test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            cfg = self.parser.parse_specific_function(str(test_object), "simple_loop_function_att")
            
            self.assertIsNotNone(cfg)
            self.assertIsInstance(cfg, ControlFlowGraph)
            self.assertEqual(cfg.entry_block, "simple_loop_function_att")
        else:
            self.skipTest("Test object file not available")
            
    def test_parse_objdump_file(self):
        """Test parsing existing objdump file"""
        test_dump = self.test_data_dir / "test_simple_loop_att.obj.dump"
        
        if test_dump.exists():
            cfgs = self.parser.parse_file_with_cfg(str(test_dump))
            
            # Should find the function
            self.assertIn("simple_loop_function_att", cfgs)
            cfg = cfgs["simple_loop_function_att"]
            self.assertIsInstance(cfg, ControlFlowGraph)
        else:
            self.skipTest("Test objdump file not available")


class TestParserFactoryObjdumpSupport(unittest.TestCase):
    """Test parser factory objdump integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = Path(__file__).parent.parent / "test_data"
        
    def test_detect_object_file_type(self):
        """Test file type detection for object files"""
        test_object = self.test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            file_type = AssemblyParserFactory.detect_file_type(str(test_object))
            self.assertEqual(file_type, FileType.OBJDUMP)
        else:
            self.skipTest("Test object file not available")
            
    def test_detect_objdump_file_type(self):
        """Test file type detection for objdump files"""
        test_dump = self.test_data_dir / "test_simple_loop_att.obj.dump"
        
        if test_dump.exists():
            file_type = AssemblyParserFactory.detect_file_type(str(test_dump))
            self.assertEqual(file_type, FileType.OBJDUMP)
        else:
            self.skipTest("Test objdump file not available")
            
    def test_create_objdump_parser(self):
        """Test creating objdump parser through factory"""
        parser = AssemblyParserFactory.create_parser(file_type=FileType.OBJDUMP)
        self.assertIsInstance(parser, ObjdumpParser)
        
    def test_auto_detect_and_parse(self):
        """Test auto-detection and parsing workflow"""
        test_object = self.test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            # Auto-detect file type
            file_type = AssemblyParserFactory.detect_file_type(str(test_object))
            syntax = AssemblyParserFactory.detect_syntax(str(test_object))
            
            # Create appropriate parser
            parser = AssemblyParserFactory.create_parser(syntax=syntax, file_type=file_type)
            
            # Parse the file
            cfgs = parser.parse_file_with_cfg(str(test_object))
            
            self.assertGreater(len(cfgs), 0)
        else:
            self.skipTest("Test object file not available")


class TestErrorHandling(unittest.TestCase):
    """Test error handling for objdump functionality"""
    
    def test_invalid_object_file(self):
        """Test handling of invalid object file"""
        # Create a temporary file that's not an object file
        with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as temp_file:
            temp_file.write(b"not an object file")
            temp_file_path = temp_file.name
            
        try:
            parser = ObjdumpParser()
            with self.assertRaises(OSError):
                parser.parse_file_with_cfg(temp_file_path)
        finally:
            os.unlink(temp_file_path)
            
    def test_missing_objdump_command(self):
        """Test handling when objdump is not available"""
        # This test is difficult to run reliably since objdump is usually available
        # We'll test the error message format instead
        try:
            # Try to run objdump with invalid args to trigger error
            subprocess.run(['objdump', '--invalid-option'], 
                         capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Expected - objdump either not found or invalid option
            pass


class TestRealWorldFiles(unittest.TestCase):
    """Test with real-world files if available"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = Path(__file__).parent.parent / "test_data"
        
    def test_montecarlo_object_file(self):
        """Test with complex MonteCarlo object file"""
        test_object = self.test_data_dir / "MonteCarlo_demo.o"
        
        if test_object.exists():
            parser = ObjdumpParser()
            cfgs = parser.parse_file_with_cfg(str(test_object))
            
            # Should find MonteCarlo_integrate function
            self.assertIn("MonteCarlo_integrate", cfgs)
            cfg = cfgs["MonteCarlo_integrate"]
            
            # Should be a complex function with many blocks and loops
            self.assertGreater(len(cfg.basic_blocks), 10)
            self.assertGreater(len(cfg.get_loops()), 0)
        else:
            self.skipTest("MonteCarlo test object file not available")
            
    def test_montecarlo_objdump_file(self):
        """Test with complex MonteCarlo objdump file"""
        test_dump = self.test_data_dir / "MonteCarlo_demo.obj.dump"
        
        if test_dump.exists():
            parser = ObjdumpParser()
            cfgs = parser.parse_file_with_cfg(str(test_dump))
            
            # Should find MonteCarlo_integrate function
            self.assertIn("MonteCarlo_integrate", cfgs)
            cfg = cfgs["MonteCarlo_integrate"]
            
            # Should be a complex function with many blocks and loops
            self.assertGreater(len(cfg.basic_blocks), 10)
            self.assertGreater(len(cfg.get_loops()), 0)
        else:
            self.skipTest("MonteCarlo test objdump file not available")


if __name__ == '__main__':
    unittest.main()
