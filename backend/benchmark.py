from solver.backtrack import solve
from tests.test_solver import EASY, HARD

for name, grid in [("easy", EASY), ("hard", HARD)]:
    for strategy in ("naive", "mrv"):
        r = solve(grid, strategy, max_recorded_steps=0, max_total_steps=2_000_000)
        status = "solved" if r.solvable else "gave up (hit cap)"
        print(f"{name:5} {strategy:6} steps={r.total_steps:>9,} "
              f"backtracks={r.backtracks:>9,} {status}")