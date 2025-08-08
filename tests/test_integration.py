"""
Integration tests for CFG Tool

Tests the command-line interface and end-to-end functionality
"""

import unittest
import tempfile
import os
import subprocess
import sys
from pathlib import Path


class TestCFGToolIntegration(unittest.TestCase):
    """Integration tests for cfg_tool.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test assembly file
        self.test_assembly = """.type simple_func, @function
simple_func:
    push rbp
    mov rbp, rsp
    mov eax, 0
.loop_start:
    inc eax
    cmp eax, 10
    jl .loop_start
    pop rbp
    ret
.Lfunc_end0:

.type another_func, @function
another_func:
    push rbp
    mov rbp, rsp
    mov eax, 1
    pop rbp
    ret
.Lfunc_end1:
"""
        
        # Create temporary assembly file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write(self.test_assembly)
            self.temp_assembly_path = f.name
        
        # Get path to cfg_tool.py
        self.cfg_tool_path = Path(__file__).parent.parent / "cfg_tool.py"
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_assembly_path):
            os.unlink(self.temp_assembly_path)
    
    def run_cfg_tool(self, args):
        """Helper to run cfg_tool.py with given arguments"""
        cmd = [sys.executable, str(self.cfg_tool_path)] + args
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            cwd=str(self.cfg_tool_path.parent)
        )
        return result
    
    def test_parse_all_functions(self):
        """Test parsing all functions in file"""
        result = self.run_cfg_tool([self.temp_assembly_path])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("simple_func", result.stdout)
        self.assertIn("another_func", result.stdout)
        self.assertIn("Found 2 function(s)", result.stdout)
    
    def test_parse_specific_function(self):
        """Test parsing a specific function"""
        result = self.run_cfg_tool([self.temp_assembly_path, "-f", "simple_func"])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Control Flow Graph for function: simple_func", result.stdout)
        self.assertIn("Back Edges (Loop Edges)", result.stdout)
        # Should detect the loop
        self.assertIn("loop_start -> loop_start", result.stdout)
    
    def test_parse_specific_function_verbose(self):
        """Test parsing with verbose output"""
        result = self.run_cfg_tool([self.temp_assembly_path, "-f", "simple_func", "-v"])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Detailed Block Information", result.stdout)
        self.assertIn("push", result.stdout)
        self.assertIn("mov", result.stdout)
        self.assertIn("inc", result.stdout)
    
    def test_parse_specific_function_detailed(self):
        """Test parsing with detailed output"""
        result = self.run_cfg_tool([self.temp_assembly_path, "-f", "simple_func", "--detailed"])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("=== Detailed CFG for Function: simple_func ===", result.stdout)
        self.assertIn("Basic Block:", result.stdout)
        self.assertIn("Instructions (", result.stdout)
    
    def test_export_dot_file(self):
        """Test DOT file export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cfg_tool([
                self.temp_assembly_path, 
                "-f", "simple_func", 
                "--export-dot", 
                "-o", temp_dir
            ])
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("CFG exported to:", result.stdout)
            
            # Check if DOT file was created
            dot_file = Path(temp_dir) / "simple_func_cfg.dot"
            self.assertTrue(dot_file.exists())
            
            # Check DOT file content
            with open(dot_file, 'r') as f:
                content = f.read()
            
            self.assertIn('digraph "simple_func"', content)
            self.assertIn('color=red', content)  # Should have red loop edges
    
    def test_export_dot_with_instruction_limit(self):
        """Test DOT export with instruction limit"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cfg_tool([
                self.temp_assembly_path,
                "-f", "simple_func",
                "--export-dot",
                "--max-instructions", "2",
                "-o", temp_dir
            ])
            
            self.assertEqual(result.returncode, 0)
            
            dot_file = Path(temp_dir) / "simple_func_cfg.dot"
            self.assertTrue(dot_file.exists())
            
            with open(dot_file, 'r') as f:
                content = f.read()
            
            # Should contain truncation indicator since first block has 3 instructions
            self.assertIn("more instructions", content)
    
    def test_export_dot_no_instructions(self):
        """Test DOT export without instructions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cfg_tool([
                self.temp_assembly_path,
                "-f", "simple_func", 
                "--export-dot",
                "--no-instructions",
                "-o", temp_dir
            ])
            
            self.assertEqual(result.returncode, 0)
            
            dot_file = Path(temp_dir) / "simple_func_cfg.dot"
            self.assertTrue(dot_file.exists())
            
            with open(dot_file, 'r') as f:
                content = f.read()
            
            # Should contain block summary, not detailed instructions
            self.assertIn("Block: ", content)
            self.assertIn("Instructions: ", content)
            # Should not contain actual instruction text
            self.assertNotIn("push rbp", content)
    
    def test_export_all_dot_files(self):
        """Test exporting all functions to DOT files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cfg_tool([
                self.temp_assembly_path,
                "--export-all-dot",
                "-o", temp_dir
            ])
            
            self.assertEqual(result.returncode, 0)
            
            # Should create DOT files for both functions
            simple_dot = Path(temp_dir) / "simple_func_cfg.dot"
            another_dot = Path(temp_dir) / "another_func_cfg.dot"
            
            self.assertTrue(simple_dot.exists())
            self.assertTrue(another_dot.exists())
    
    def test_nonexistent_file(self):
        """Test handling of non-existent file"""
        result = self.run_cfg_tool(["nonexistent.s"])
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stdout)
    
    def test_nonexistent_function(self):
        """Test handling of non-existent function"""
        result = self.run_cfg_tool([self.temp_assembly_path, "-f", "nonexistent_func"])
        
        self.assertEqual(result.returncode, 0)  # Doesn't crash, just reports
        self.assertIn("Function 'nonexistent_func' not found", result.stdout)
        self.assertIn("Available functions:", result.stdout)
    
    def test_help_message(self):
        """Test help message display"""
        result = self.run_cfg_tool(["--help"])
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Parse assembly files, objdump files, or object files to build control flow graphs", result.stdout)
        self.assertIn("Examples:", result.stdout)
        self.assertIn("-f", result.stdout)
        self.assertIn("--export-dot", result.stdout)

    def test_object_file_parsing(self):
        """Test parsing object files directly"""
        test_data_dir = Path(__file__).parent.parent / "test_data"
        test_object = test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            result = self.run_cfg_tool([str(test_object), "-f", "simple_loop_function_att", "--auto-detect"])
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Auto-detected file type: OBJDUMP", result.stdout)
            self.assertIn("Executing objdump on object file", result.stdout)
            self.assertIn("simple_loop_function_att", result.stdout)
            self.assertIn("Detected Loops:", result.stdout)
        else:
            self.skipTest("Test object file not available")

    def test_object_file_all_functions(self):
        """Test parsing all functions from object file"""
        test_data_dir = Path(__file__).parent.parent / "test_data"
        test_object = test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            result = self.run_cfg_tool([str(test_object), "--auto-detect"])
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Auto-detected file type: OBJDUMP", result.stdout)
            self.assertIn("Executing objdump on object file", result.stdout)
            self.assertIn("Found", result.stdout)
            self.assertIn("function(s)", result.stdout)
        else:
            self.skipTest("Test object file not available")

    def test_object_file_export_dot(self):
        """Test DOT export from object file"""
        test_data_dir = Path(__file__).parent.parent / "test_data"
        test_object = test_data_dir / "test_simple_loop_att.o"
        
        if test_object.exists():
            with tempfile.TemporaryDirectory() as temp_dir:
                result = self.run_cfg_tool([
                    str(test_object), 
                    "-f", "simple_loop_function_att", 
                    "--export-dot", 
                    "--auto-detect",
                    "-o", temp_dir
                ])
                
                self.assertEqual(result.returncode, 0)
                self.assertIn("CFG exported to:", result.stdout)
                
                # Check that DOT file was created
                dot_files = list(Path(temp_dir).glob("*.dot"))
                self.assertGreater(len(dot_files), 0)
        else:
            self.skipTest("Test object file not available")

    def test_complex_object_file(self):
        """Test with complex object file"""
        test_data_dir = Path(__file__).parent.parent / "test_data"
        test_object = test_data_dir / "MonteCarlo_demo.o"
        
        if test_object.exists():
            result = self.run_cfg_tool([
                str(test_object), 
                "-f", "MonteCarlo_integrate", 
                "--auto-detect"
            ])
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Auto-detected file type: OBJDUMP", result.stdout)
            self.assertIn("MonteCarlo_integrate", result.stdout)
            self.assertIn("Total Blocks:", result.stdout)
            self.assertIn("Detected Loops:", result.stdout)
        else:
            self.skipTest("MonteCarlo test object file not available")

    def test_objdump_file_parsing(self):
        """Test parsing existing objdump files"""
        test_data_dir = Path(__file__).parent.parent / "test_data"
        test_dump = test_data_dir / "test_simple_loop_att.obj.dump"
        
        if test_dump.exists():
            result = self.run_cfg_tool([
                str(test_dump), 
                "-f", "simple_loop_function_att",
                "--auto-detect"
            ])
            
            self.assertEqual(result.returncode, 0)
            self.assertIn("Auto-detected file type: OBJDUMP", result.stdout)
            self.assertIn("simple_loop_function_att", result.stdout)
            # Should NOT contain "Executing objdump" since it's already a dump file
            self.assertNotIn("Executing objdump", result.stdout)
        else:
            self.skipTest("Test objdump file not available")

    def test_invalid_object_file(self):
        """Test error handling with invalid object file"""
        # Create a temporary file with .o extension but invalid content
        with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as temp_file:
            temp_file.write(b"not an object file")
            temp_file_path = temp_file.name
            
        try:
            result = self.run_cfg_tool([temp_file_path, "--auto-detect"])
            
            # Should fail gracefully
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Error", result.stdout)
        finally:
            os.unlink(temp_file_path)


if __name__ == '__main__':
    unittest.main()
