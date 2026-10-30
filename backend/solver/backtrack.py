from dataclasses import dataclass, field
from typing import Literal
import time


Grid = list[list[int]]
Strategy = Literal["naive", "mrv"]

# Step encoding: (row, col, value, action)
# action: 0 = try (place value), 1 = backtrack (clear cell)
Step = tuple[int, int, int, int]
TRY, BACKTRACK = 0, 1


class InvalidGridError(ValueError):
    pass


@dataclass
class SolveResult:
    solvable: bool
    solution: Grid | None
    steps: list[Step] = field(default_factory=list)
    total_steps: int = 0       # real count, even if steps list was capped
    backtracks: int = 0
    truncated: bool = False    # True if steps were capped
    aborted: bool = False        # NEW: hit max_total_steps, gave up
    elapsed_ms: float = 0.0      # NEW: wall time

def validate(grid: Grid) -> list[tuple[int, int]]:
    """Return a list of (row, col) cells that conflict. Empty list = valid.
    Raises InvalidGridError if the shape or values are wrong."""
    if len(grid) != 9 or any(len(row) != 9 for row in grid):
        raise InvalidGridError("Grid must be 9x9")
    if any(not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row):
        raise InvalidGridError("Cells must be integers 0-9")

    conflicts: set[tuple[int, int]] = set()
    units: list[list[tuple[int, int]]] = []
    for i in range(9):
        units.append([(i, j) for j in range(9)])  # row
        units.append([(j, i) for j in range(9)])  # column
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            units.append([(br + i, bc + j) for i in range(3) for j in range(3)])

    for unit in units:
        seen: dict[int, tuple[int, int]] = {}
        for r, c in unit:
            v = grid[r][c]
            if v == 0:
                continue
            if v in seen:
                conflicts.add(seen[v])
                conflicts.add((r, c))
            else:
                seen[v] = (r, c)
    return sorted(conflicts)


def solve(
    grid: Grid,
    strategy: Strategy = "mrv",
    max_recorded_steps: int = 200_000,
    max_total_steps: int = 5_000_000,
) -> SolveResult:
    conflicts = validate(grid)
    if conflicts:
        raise InvalidGridError(f"Conflicting cells: {conflicts}")

    board = [row[:] for row in grid]  # never mutate the caller's grid

    # Bitmasks: bit v set means digit v is used
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9
    empties: list[tuple[int, int]] = []
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v:
                bit = 1 << v
                rows[r] |= bit
                cols[c] |= bit
                boxes[r // 3 * 3 + c // 3] |= bit
            else:
                empties.append((r, c))

    steps: list[Step] = []
    state = {"total": 0, "backtracks": 0, "aborted": False}

    def record(step: Step) -> None:
        state["total"] += 1
        if len(steps) < max_recorded_steps:
            steps.append(step)

    def candidates_mask(r: int, c: int) -> int:
        used = rows[r] | cols[c] | boxes[r // 3 * 3 + c // 3]
        return ~used & 0b1111111110  # bits 1..9

    def pick_cell() -> tuple[int, int, int] | None:
        """Return (index in empties, ...) via the strategy."""
        if strategy == "naive":
            for idx, (r, c) in enumerate(empties):
                if board[r][c] == 0:
                    return idx, r, c
            return None
        # MRV: choose the empty cell with the fewest candidates
        best = None
        best_count = 10
        for idx, (r, c) in enumerate(empties):
            if board[r][c] != 0:
                continue
            count = candidates_mask(r, c).bit_count()
            if count < best_count:
                best, best_count = (idx, r, c), count
                if count <= 1:
                    break
        return best

    def bt() -> bool:
        if state["total"] >= max_total_steps:
            state["aborted"] = True
            return False
        pick = pick_cell()
        if pick is None:
            return True
        _, r, c = pick
        b = r // 3 * 3 + c // 3
        mask = candidates_mask(r, c)
        for v in range(1, 10):
            if not mask >> v & 1:
                continue
            bit = 1 << v
            board[r][c] = v
            rows[r] |= bit; cols[c] |= bit; boxes[b] |= bit
            record((r, c, v, TRY))
            if bt():
                return True
            board[r][c] = 0
            rows[r] &= ~bit; cols[c] &= ~bit; boxes[b] &= ~bit
            record((r, c, 0, BACKTRACK))
            state["backtracks"] += 1
            if state["aborted"]:
                return False
        return False

    t0 = time.perf_counter()
    ok = bt()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return SolveResult(
        solvable=ok,
        solution=board if ok else None,
        steps=steps,
        total_steps=state["total"],
        backtracks=state["backtracks"],
        truncated=state["total"] > len(steps),
        aborted=state["aborted"],
        elapsed_ms=elapsed_ms,
    )