# CFG Analyzer
PET Project For easing my own work around analysing large assembly files.


A comprehensive Control Flow Graph analysis toolkit for assembly code with loop detection and visualization capabilities. **Now supports both Intel and AT&T assembly syntax!**
!!! Dont use handwritten assembly yet!!
## Features

- **Multi-Syntax Support**: Supports both Intel and AT&T assembly syntax with automatic detection
- **Assembly Parsing**: Robust parsing of assembly files with function detection
- **CFG Construction**: Automatic basic block identification and control flow graph building
- **Loop Detection**: DFS-based back edge detection for loop identification
- **Visualization**: GraphViz DOT export with professional styling and left-aligned text
- **Command-Line Interface**: Easy-to-use tool for analyzing assembly files

## Assembly Syntax Support

The tool supports both major x86 assembly syntaxes:

- **Intel Syntax** (default): `mov eax, 10`, `jmp label`
- **AT&T Syntax**: `movl $10, %eax`, `jmp label`

### Syntax Detection
- **Manual**: Use `-s intel` or `-s att` to specify syntax
- **Automatic**: Use `--auto-detect` to automatically detect syntax from file content

## Project Structure

```
cfg-analyzer/
├── src/                    # Source code
│   └── cfg_analyzer/       # Main package
│       ├── __init__.py     # Package initialization
│       ├── base_parser.py  # Base parser class with common functionality
│       ├── intel_parser.py # Intel syntax parser
│       ├── att_parser.py   # AT&T syntax parser  
│       ├── parser_factory.py # Parser factory and syntax detection
│       ├── models.py       # Data structures (Instruction, BasicBlock, CFG)
│       └── visualization.py # DOT export and printing functions
├── tests/                  # Unit tests
│   ├── test_models.py      # Tests for data structures
│   ├── test_parser.py      # Tests for parsing logic
│   ├── test_syntax_support.py # Tests for syntax support
│   ├── test_visualization.py # Tests for visualization
│   ├── test_integration.py # Integration tests
│   └── run_tests.py        # Test runner
├── test_data/              # Test assembly files
│   ├── test_simple_loop.s  # Simple loop test case (Intel)
│   ├── test_simple_loop_att.s # Simple loop test case (AT&T)
│   └── MonteCarlo_demo.s   # Complex real-world example
├── cfg_tool.py             # Command-line interface
└── README.md               # This file
```

## Installation

No installation required. This is a standalone Python project.

### Requirements

- Python 3.6+
- GraphViz (for PNG generation from DOT files)

## Usage

### Command Line Tool

```bash
# Analyze all functions in an assembly file (Intel syntax, default)
python cfg_tool.py program.s

# Analyze with specific syntax
python cfg_tool.py program.s -s att          # AT&T syntax
python cfg_tool.py program.s -s intel        # Intel syntax (default)

# Auto-detect syntax
python cfg_tool.py program.s --auto-detect

# Analyze specific function with AT&T syntax
python cfg_tool.py program.s -f function_name -s att -v

# Export to GraphViz DOT format
python cfg_tool.py program.s -f function_name --export-dot -s att

# Export with limited instructions per block  
python cfg_tool.py program.s --export-all-dot --max-instructions 5 -o output_dir
```

#### Syntax Examples

**Intel Syntax (default):**
```bash
python cfg_tool.py test_data/test_simple_loop.s -f simple_loop_function -v
```

**AT&T Syntax:**
```bash
python cfg_tool.py test_data/test_simple_loop_att.s -f simple_loop_function_att -s att -v
```

**Auto-detection:**
```bash
python cfg_tool.py test_data/test_simple_loop_att.s --auto-detect -f simple_loop_function_att -v
```
## Examples

### Simple Loop Detection

Input assembly (Intel syntax):
```assembly
.type simple_loop, @function
simple_loop:
    push rbp
    mov rbp, rsp
    mov eax, 0
.loop_start:
    inc eax
    cmp eax, 10
    jl .loop_start    # Back edge - creates loop
    pop rbp
    ret
```
![Visual](test_data/simple_loop_function_cfg.png)
Input assembly (AT&T syntax):
```assembly
.type simple_loop, @function
simple_loop:
    pushq %rbp
    movq %rsp, %rbp
    movl $0, %eax
.loop_start:
    incl %eax
    cmpl $10, %eax
    jl .loop_start    # Back edge - creates loop
    popq %rbp
    retq
```
![Visual](test_data/simple_loop_function_att_cfg.png)
Output: Detects 1 back edge (loop_start -> loop_start) colored red in visualization.

### Complex Function Analysis

The tool successfully analyzed the MonteCarlo_integrate function with:
- 59 basic blocks
- 19 detected loop edges
- Professional visualization with clear loop identification

## Development

### Adding New Features

1. **Models**: Add new data structures in `src/cfg_analyzer/models.py`
2. **Parser**: Extend parsing logic in `src/cfg_analyzer/parser.py`  
3. **Visualization**: Add new visualization features in `src/cfg_analyzer/visualization.py`
4. **Tests**: Add corresponding tests in `tests/`

## Programming Interface

### Python API

```python
# Backward compatible (Intel syntax)
from src.cfg_analyzer import CFGAssemblyParser, export_cfg_to_dot

parser = CFGAssemblyParser()  # Defaults to Intel syntax
cfgs = parser.parse_file_with_cfg("program.s")

# New syntax-aware API
from src.cfg_analyzer import AssemblyParserFactory, AssemblySyntax

# Create parser for specific syntax
parser = AssemblyParserFactory.create_parser(AssemblySyntax.ATT)
cfgs = parser.parse_file_with_cfg("program.s")

# Auto-detect syntax
syntax = AssemblyParserFactory.detect_syntax("program.s")
parser = AssemblyParserFactory.create_parser(syntax)
cfgs = parser.parse_file_with_cfg("program.s")

# Analyze a specific function
cfg = cfgs["function_name"]
print(f"Function: {cfg.function_name}")
print(f"Blocks: {len(cfg.basic_blocks)}")

# Detect loops
back_edges = cfg.detect_back_edges()
print(f"Loop edges: {len(back_edges)}")

# Export to DOT format
export_cfg_to_dot(cfg, "output.dot", include_instructions=True, max_instructions=10)
```

## Development

### Adding New Features

1. **Models**: Add new data structures in `src/cfg_analyzer/models.py`
2. **Base Parser**: Extend common functionality in `src/cfg_analyzer/base_parser.py`
3. **Syntax Parsers**: Add syntax-specific parsing in `src/cfg_analyzer/intel_parser.py` or `src/cfg_analyzer/att_parser.py`
4. **Visualization**: Add new visualization features in `src/cfg_analyzer/visualization.py`
5. **Tests**: Add corresponding tests in `tests/`

### Code Quality

- Comprehensive unit test coverage (63+ tests)
- Integration tests for end-to-end functionality
- Type hints throughout the codebase
- Docstrings for all public functions
- Clean separation of concerns
- Backward compatibility maintained

## License

This project was developed during a CFG analysis session focused on loop detection and visualization enhancement.

### Python API

```python
from src.cfg_analyzer import CFGAssemblyParser, export_cfg_to_dot

# Parse assembly file
parser = CFGAssemblyParser()
cfgs = parser.parse_file_with_cfg("assembly_file.s")

# Analyze a specific function
cfg = cfgs["function_name"]
print(f"Function: {cfg.function_name}")
print(f"Blocks: {len(cfg.basic_blocks)}")

# Detect loops
back_edges = cfg.detect_back_edges()
print(f"Loop edges: {len(back_edges)}")

# Export to DOT format
export_cfg_to_dot(cfg, "output.dot", include_instructions=True, max_instructions=10)
```

## Testing

Run the test suite:

```bash
# Run all tests
python tests/run_tests.py

# Run specific test module
python -m unittest tests.test_models
python -m unittest tests.test_parser
python -m unittest tests.test_visualization
python -m unittest tests.test_integration
```

## Key Features Implemented

### Loop Detection
- ✅ DFS-based back edge detection algorithm
- ✅ Red-colored loop edges in DOT visualization
- ✅ Comprehensive loop analysis reporting

### Visual Enhancements
- ✅ Left-aligned text formatting for better readability
- ✅ Professional color coding (entry=green, exit=red, unreachable=grey)
- ✅ Clear type indicators (ENTRY, EXIT, UNREACHABLE)
- ✅ Terminator instruction markers ([TERM])
- ✅ Enhanced typography and visual separators

### Technical Improvements
- ✅ Robust assembly label parsing (supports various formats)
- ✅ Comprehensive basic block analysis
- ✅ GraphViz DOT format compatibility
- ✅ Scalable instruction display with truncation options

## Usage Examples

```bash
# Analyze function and export CFG
python3 cfg_tool.py MonteCarlo_demo.s -f MonteCarlo_integrate --export-dot --max-instructions 5

# Generate PNG visualization
dot -Tpng MonteCarlo_integrate_cfg.dot -o MonteCarlo_integrate_cfg.png
```


</content>
</invoke>
