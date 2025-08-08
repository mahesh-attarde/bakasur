# CFG Analyzer Development

## Development Environment Setup

1. Clone the repository
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv cfg-env
   source cfg-env/bin/activate  # On Windows: cfg-env\Scripts\activate
   ```
3. Install in development mode:
   ```bash
   pip install -e .
   ```

## Running Tests

```bash
# Run all tests (63 tests total)
python tests/run_tests.py

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=src/cfg_analyzer --cov-report=html

# Run specific test modules
python -m unittest tests.test_models
python -m unittest tests.test_parser
python -m unittest tests.test_visualization
python -m unittest tests.test_integration
python -m unittest tests.test_syntax_support  # New: Multi-syntax tests
```

## Code Quality

If you have the development dependencies installed:

```bash
# Format code
black src/ tests/ cfg_tool.py

# Lint code
flake8 src/ tests/ cfg_tool.py

# Type checking
mypy src/cfg_analyzer/
```

## Project Structure

```
cfg-analyzer/
├── src/cfg_analyzer/          # Main package source code
│   ├── __init__.py           # Package initialization and exports
│   ├── models.py             # Core data structures (CFG, BasicBlock, Instruction)
│   ├── base_parser.py        # Abstract base parser with common functionality
│   ├── intel_parser.py       # Intel assembly syntax parser
│   ├── att_parser.py         # AT&T assembly syntax parser
│   ├── parser_factory.py     # Parser factory and syntax detection
│   └── visualization.py      # Visualization and export functions
├── tests/                    # Comprehensive test suite (63 tests)
│   ├── test_models.py        # Unit tests for data structures
│   ├── test_parser.py        # Unit tests for Intel parser (backward compatibility)
│   ├── test_syntax_support.py # Unit tests for multi-syntax support
│   ├── test_visualization.py # Unit tests for visualization
│   ├── test_integration.py   # End-to-end integration tests
│   └── run_tests.py          # Test runner script
├── test_data/                # Test assembly files
│   ├── test_simple_loop.s    # Simple test cases (Intel syntax)
│   ├── test_simple_loop_att.s # Simple test cases (AT&T syntax)
│   └── MonteCarlo_demo.s     # Complex real-world examples
├── build_/                   # Build artifacts and unused files (excluded from git)
│   ├── unused_files/         # Deprecated source files
│   ├── cache/               # Python bytecode cache
│   └── [output_dirs]/       # Test outputs and DOT files
├── cfg_tool.py               # Command-line interface with multi-syntax support
├── setup.py                  # Package setup and installation
├── .gitignore               # Git ignore rules
├── README.md                 # User documentation
└── DEVELOPMENT.md            # This file
```

## Adding New Features

### 1. Extending Data Models

Add new data structures in `src/cfg_analyzer/models.py`:

```python
from dataclasses import dataclass
from enum import Enum

@dataclass
class NewDataStructure:
    """New data structure for CFG analysis"""
    field1: str
    field2: int = 0
```

### 2. Adding New Assembly Syntax Support

To add support for a new assembly syntax (e.g., MASM, NASM):

1. **Create a new parser class** in `src/cfg_analyzer/new_syntax_parser.py`:

```python
from .base_parser import BaseAssemblyParser

class NewSyntaxParser(BaseAssemblyParser):
    """Parser for new assembly syntax"""
    
    def _init_syntax_specific_patterns(self):
        """Initialize syntax-specific patterns"""
        self.unconditional_jumps = {'jmp', 'branch', ...}
        self.conditional_jumps = {'je', 'jne', ...}
        self.return_instructions = {'ret', 'return', ...}
        # Add syntax-specific patterns
    
    def _parse_operands(self, operands: str) -> str:
        """Parse and normalize operands for this syntax"""
        # Implement syntax-specific operand parsing
        return operands
    
    def _extract_jump_targets(self, operands: str) -> List[str]:
        """Extract jump targets for this syntax"""
        # Implement syntax-specific target extraction
        return []
```

2. **Update the parser factory** in `src/cfg_analyzer/parser_factory.py`:

```python
# Add to AssemblySyntax enum
class AssemblySyntax(Enum):
    INTEL = "intel"
    ATT = "att"
    NEW_SYNTAX = "new_syntax"  # Add new syntax

# Update factory method
@staticmethod
def create_parser(syntax: Union[AssemblySyntax, str] = AssemblySyntax.INTEL) -> BaseAssemblyParser:
    # ... existing code ...
    elif syntax == AssemblySyntax.NEW_SYNTAX:
        return NewSyntaxParser()
```

3. **Add detection heuristics** for auto-detection capability

4. **Write comprehensive tests** in `tests/test_syntax_support.py`

### 3. Extending Base Parser Functionality

Add common functionality in `src/cfg_analyzer/base_parser.py`:

```python
def parse_new_construct(self, line: str) -> Optional[SomeType]:
    """Parse a new assembly construct (common across syntaxes)"""
    # Implementation here
    pass
```

### 4. Extending Visualization

Add new visualization features in `src/cfg_analyzer/visualization.py`:

```python
def export_new_format(cfg: ControlFlowGraph, output_path: str):
    """Export CFG in a new format"""
    # Implementation here
    pass
```

### 5. Adding Tests

Always add corresponding tests in the `tests/` directory:

```python
import unittest
from src.cfg_analyzer.models import NewDataStructure

class TestNewFeature(unittest.TestCase):
    def test_new_functionality(self):
        """Test description"""
        # Test implementation
        self.assertEqual(expected, actual)
```

## Architecture Overview

### Multi-Syntax Support Architecture

The project uses a clean architecture pattern for supporting multiple assembly syntaxes:

1. **BaseAssemblyParser**: Abstract base class containing common parsing logic
2. **Syntax-Specific Parsers**: Concrete implementations for Intel, AT&T, etc.
3. **Parser Factory**: Creates appropriate parser based on syntax specification
4. **Auto-Detection**: Heuristic-based syntax detection from file content

### Key Design Principles

- **Separation of Concerns**: Common logic in base class, syntax-specific in subclasses
- **Backward Compatibility**: Original `CFGAssemblyParser` still works as alias
- **Extensibility**: Easy to add new syntaxes without modifying existing code
- **Clean Interface**: Factory pattern hides complexity from users
- **Comprehensive Testing**: Each component has dedicated test coverage

### Command Line Interface

The CLI supports syntax selection and auto-detection:

```bash
# Default Intel syntax
python cfg_tool.py program.s

# Explicit syntax selection
python cfg_tool.py program.s -s intel
python cfg_tool.py program.s -s att

# Auto-detection
python cfg_tool.py program.s --auto-detect
```

### API Usage Patterns

```python
# Backward compatible approach
from cfg_analyzer import CFGAssemblyParser
parser = CFGAssemblyParser()  # Intel syntax

# New syntax-aware approach
from cfg_analyzer import AssemblyParserFactory, AssemblySyntax
parser = AssemblyParserFactory.create_parser(AssemblySyntax.ATT)

# Auto-detection approach
syntax = AssemblyParserFactory.detect_syntax("file.s")
parser = AssemblyParserFactory.create_parser(syntax)
```