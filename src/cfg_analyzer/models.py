"""
CFG Data Models

Contains all data structures for representing assembly instructions,
basic blocks, and control flow graphs.
"""

import re
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class TerminatorType(Enum):
    """Types of terminator instructions"""
    UNCONDITIONAL_JUMP = "jmp"
    CONDITIONAL_JUMP = "conditional"
    RETURN = "ret"
    CALL_RETURN = "call_ret"
    FALLTHROUGH = "fallthrough"


@dataclass
class Instruction:
    """Represents a single assembly instruction"""
    line_number: int
    opcode: str
    operands: str
    raw_line: str
    is_terminator: bool = False
    terminator_type: Optional[TerminatorType] = None
    jump_targets: List[str] = field(default_factory=list)


@dataclass
class BasicBlock:
    """Represents a basic block in the control flow graph"""
    label: str
    start_line: int
    end_line: int
    instructions: List[Instruction] = field(default_factory=list)
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    # Optimization attributes
    is_unreachable: bool = False
    background_color: str = "white"
    
    @property
    def is_entry_block(self) -> bool:
        """Check if this is an entry block (no predecessors)"""
        return len(self.predecessors) == 0
    
    @property
    def is_exit_block(self) -> bool:
        """Check if this is an exit block (no successors)"""
        return len(self.successors) == 0
    
    @property
    def terminator(self) -> Optional[Instruction]:
        """Get the terminator instruction of this block"""
        for inst in reversed(self.instructions):
            if inst.is_terminator:
                return inst
        return None


@dataclass
class ControlFlowGraph:
    """Represents a control flow graph for a function"""
    function_name: str
    entry_block: str
    basic_blocks: Dict[str, BasicBlock] = field(default_factory=dict)
    
    def add_edge(self, from_block: str, to_block: str):
        """Add an edge between two basic blocks"""
        if from_block in self.basic_blocks:
            self.basic_blocks[from_block].successors.add(to_block)
        if to_block in self.basic_blocks:
            self.basic_blocks[to_block].predecessors.add(from_block)
    
    def get_reachable_blocks(self, start_block: str = None) -> Set[str]:
        """Get all blocks reachable from start_block (or entry if None)"""
        start = start_block or self.entry_block
        visited = set()
        stack = [start]
        
        while stack:
            block = stack.pop()
            if block in visited or block not in self.basic_blocks:
                continue
            visited.add(block)
            stack.extend(self.basic_blocks[block].successors)
        
        return visited
    
    def get_loops(self) -> List[Set[str]]:
        """Detect loops in the CFG using simple back-edge detection"""
        loops = []
        visited = set()
        rec_stack = set()
        
        def dfs(block: str, path: List[str]) -> None:
            if block in rec_stack:
                # Found a back edge - extract loop
                loop_start = path.index(block)
                loop_blocks = set(path[loop_start:])
                loops.append(loop_blocks)
                return
            
            if block in visited or block not in self.basic_blocks:
                return
            
            visited.add(block)
            rec_stack.add(block)
            path.append(block)
            
            for successor in self.basic_blocks[block].successors:
                dfs(successor, path.copy())
            
            rec_stack.remove(block)
        
        dfs(self.entry_block, [])
        return loops
    
    def detect_back_edges(self) -> Set[Tuple[str, str]]:
        """Detect back edges in the CFG using DFS"""
        back_edges = set()
        visited = set()
        rec_stack = set()
        
        def dfs(block: str) -> None:
            if block not in self.basic_blocks:
                return
                
            visited.add(block)
            rec_stack.add(block)
            
            for successor in self.basic_blocks[block].successors:
                if successor in rec_stack:
                    # This is a back edge (creates a loop)
                    back_edges.add((block, successor))
                elif successor not in visited:
                    dfs(successor)
            
            rec_stack.remove(block)
        
        # Start DFS from entry block
        if self.entry_block in self.basic_blocks:
            dfs(self.entry_block)
            
        # Also check any unreachable components
        for block_label in self.basic_blocks:
            if block_label not in visited:
                dfs(block_label)
        
        return back_edges
    
    def optimize(self):
        """Apply optimization passes to the CFG"""
        self._mark_unreachable_blocks()
        self._set_block_colors()
        # Note: Loop detection is done on-demand via detect_back_edges()
    
    def print_loop_info(self):
        """Print information about detected loops"""
        back_edges = self.detect_back_edges()
        loops = self.get_loops()
        
        print(f"Loop Analysis for {self.function_name}:")
        print(f"  Back edges found: {len(back_edges)}")
        
        if back_edges:
            print("  Back edges (loop edges):")
            for from_block, to_block in sorted(back_edges):
                print(f"    {from_block} -> {to_block} (RED)")
        
        print(f"  Loops detected: {len(loops)}")
        if loops:
            for i, loop_blocks in enumerate(loops, 1):
                print(f"    Loop {i}: {{{', '.join(sorted(loop_blocks))}}}")
        
        print()
    
    def _mark_unreachable_blocks(self):
        """Mark blocks that are unreachable from the entry block"""
        reachable = self.get_reachable_blocks()
        
        for label, block in self.basic_blocks.items():
            if label not in reachable:
                block.is_unreachable = True
            else:
                block.is_unreachable = False
    
    def _set_block_colors(self):
        """Set background colors for blocks based on their properties"""
        for label, block in self.basic_blocks.items():
            if block.is_unreachable:
                block.background_color = "grey"
            elif block.is_entry_block:
                block.background_color = "lightgreen"
            elif block.is_exit_block:
                block.background_color = "lightcoral"
            else:
                block.background_color = "white"
