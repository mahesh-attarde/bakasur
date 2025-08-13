"""
Data models for DFG analysis

Contains the core data structures used throughout the DFG analyzer.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Instruction:
    """Represents a single assembly instruction with its operands"""
    line_num: int
    label: Optional[str]
    opcode: str
    operands: List[str]
    raw_line: str
    
    def __str__(self):
        prefix = f"{self.label}:\n" if self.label else ""
        return f"{prefix}{self.opcode} {', '.join(self.operands)}"


@dataclass
class DataDependency:
    """Represents a data dependency between instructions"""
    source_line: int
    target_line: int
    resource: str  # register name or memory location
    dependency_type: str  # 'RAW', 'WAR', 'WAW'
    operand_type: str  # 'register' or 'memory'
    
    def __str__(self):
        return f"Line {self.source_line} -> Line {self.target_line} ({self.resource}, {self.dependency_type}, {self.operand_type})"


# Legacy models for compatibility with ASCII visualizer
class LegacyInstruction:
    def __init__(self, line_num, opcode, operands, full_text):
        self.line_num = line_num
        self.opcode = opcode
        self.operands = operands
        self.full_text = full_text.strip()
        self.reads = set()
        self.writes = set()
        self.memory_address_reads = set()  # Registers used only for memory addressing


class Dependency:
    def __init__(self, from_instr, to_instr, register, dep_type):
        self.from_instr = from_instr
        self.to_instr = to_instr
        self.register = register
        self.dep_type = dep_type
