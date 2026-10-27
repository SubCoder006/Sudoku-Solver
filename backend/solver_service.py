import time
from typing import List, Tuple, Dict, Any, Optional

def is_valid_placement(grid: List[List[int]], row: int, col: int, num: int) -> bool:
    """Check if placing `num` at (row, col) is valid in the given 9x9 grid."""
    # Row check
    if any(grid[row][c] == num for c in range(9) if c != col):
        return False

    # Column check
    if any(grid[r][col] == num for r in range(9) if r != row):
        return False

    # 3x3 Box check
    box_r = (row // 3) * 3
    box_c = (col // 3) * 3
    for r in range(box_r, box_r + 3):
        for c in range(box_c, box_c + 3):
            if (r != row or c != col) and grid[r][c] == num:
                return False

    return True


def find_conflicts(grid: List[List[int]]) -> List[Dict[str, Any]]:
    """
    Find any existing contradictory placements in the 9x9 grid.
    Returns a list of conflicting coordinates with the conflicting value and reason.
    """
    conflicts = []
    # Check rows
    for r in range(9):
        seen: Dict[int, int] = {}
        for c in range(9):
            val = grid[r][c]
            if val != 0:
                if val in seen:
                    conflicts.append({"row": r, "col": c, "val": val, "reason": "row"})
                    conflicts.append({"row": r, "col": seen[val], "val": val, "reason": "row"})
                else:
                    seen[val] = c

    # Check columns
    for c in range(9):
        seen = {}
        for r in range(9):
            val = grid[r][c]
            if val != 0:
                if val in seen:
                    conflicts.append({"row": r, "col": c, "val": val, "reason": "col"})
                    conflicts.append({"row": seen[val], "col": c, "val": val, "reason": "col"})
                else:
                    seen[val] = r

    # Check 3x3 boxes
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            seen = {}
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    val = grid[r][c]
                    if val != 0:
                        if val in seen:
                            conflicts.append({"row": r, "col": c, "val": val, "reason": "box"})
                            orig_r, orig_c = seen[val]
                            conflicts.append({"row": orig_r, "col": orig_c, "val": val, "reason": "box"})
                        else:
                            seen[val] = (r, c)

    # Deduplicate conflict coords
    unique_conflicts = []
    seen_keys = set()
    for item in conflicts:
        key = (item["row"], item["col"])
        if key not in seen_keys:
            seen_keys.add(key)
            unique_conflicts.append(item)

    return unique_conflicts


def validate_grid(grid: List[List[int]]) -> bool:
    """Validate 9x9 dimensions and absence of rule conflicts."""
    if len(grid) != 9:
        return False
    for row in grid:
        if len(row) != 9:
            return False
        if any(not isinstance(val, int) or val < 0 or val > 9 for val in row):
            return False

    conflicts = find_conflicts(grid)
    return len(conflicts) == 0


def solve_sudoku(
    grid: List[List[int]],
    max_nodes: int = 150000,
    max_seconds: float = 30.0,
    record_steps: bool = False,
    max_recorded_steps: int = 1000
) -> Tuple[bool, List[List[int]], int, float, List[Dict[str, Any]]]:
    """
    Solves the 9x9 Sudoku using Backtracking with Most Constrained Variable (MCV) heuristic.
    Returns:
        (success, solved_grid, nodes_explored, time_taken_ms, steps_list)
    """
    conflicts = find_conflicts(grid)
    if conflicts:
        return False, [row[:] for row in grid], 0, 0.0, []

    # Deep copy working grid
    working_grid = [row[:] for row in grid]
    start_time = time.perf_counter()
    nodes = 0
    steps: List[Dict[str, Any]] = []

    def backtrack() -> bool:
        nonlocal nodes
        nodes += 1

        if nodes > max_nodes:
            return False
        if (time.perf_counter() - start_time) > max_seconds:
            return False

        # MCV: Find empty cell with fewest legal options
        best_cell = None
        best_options = None

        for r in range(9):
            for c in range(9):
                if working_grid[r][c] != 0:
                    continue

                options = [
                    num for num in range(1, 10)
                    if is_valid_placement(working_grid, r, c, num)
                ]

                if not options:
                    return False  # Dead end

                if best_options is None or len(options) < len(best_options):
                    best_cell = (r, c)
                    best_options = options
                    if len(options) == 1:
                        break
            if best_options is not None and len(best_options) == 1:
                break

        if best_cell is None:
            return True  # All cells filled!

        r, c = best_cell
        for num in best_options:
            working_grid[r][c] = num

            if record_steps and len(steps) < max_recorded_steps:
                steps.append({"row": r, "col": c, "val": num, "action": "set"})

            if backtrack():
                return True

            working_grid[r][c] = 0
            if record_steps and len(steps) < max_recorded_steps:
                steps.append({"row": r, "col": c, "val": 0, "action": "backtrack"})

        return False

    success = backtrack()
    time_taken_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return success, working_grid, nodes, time_taken_ms, steps
