import pytest
from solver.backtrack import solve, validate, InvalidGridError

EASY = [
    [5,3,0,0,7,0,0,0,0],
    [6,0,0,1,9,5,0,0,0],
    [0,9,8,0,0,0,0,6,0],
    [8,0,0,0,6,0,0,0,3],
    [4,0,0,8,0,3,0,0,1],
    [7,0,0,0,2,0,0,0,6],
    [0,6,0,0,0,0,2,8,0],
    [0,0,0,4,1,9,0,0,5],
    [0,0,0,0,8,0,0,7,9],
]

HARD = [  # Arto Inkala's puzzle
    [8,0,0,0,0,0,0,0,0],
    [0,0,3,6,0,0,0,0,0],
    [0,7,0,0,9,0,2,0,0],
    [0,5,0,0,0,7,0,0,0],
    [0,0,0,0,4,5,7,0,0],
    [0,0,0,1,0,0,0,3,0],
    [0,0,1,0,0,0,0,6,8],
    [0,0,8,5,0,0,0,1,0],
    [0,9,0,0,0,0,4,0,0],
]


def is_complete_valid(g):
    return all(v != 0 for row in g for v in row) and validate(g) == []


@pytest.mark.parametrize("strategy", ["naive", "mrv"])
def test_easy_solves(strategy):
    r = solve(EASY, strategy)
    assert r.solvable and is_complete_valid(r.solution)


def test_solution_keeps_givens():
    r = solve(EASY)
    for i in range(9):
        for j in range(9):
            if EASY[i][j]:
                assert r.solution[i][j] == EASY[i][j]


def test_hard_solves_with_mrv():
    r = solve(HARD, "mrv")
    assert r.solvable and is_complete_valid(r.solution)


def test_mrv_uses_fewer_steps_than_naive():
    # sanity comparison on the same puzzle:
    assert solve(EASY, "mrv").total_steps <= solve(EASY, "naive").total_steps


def test_input_not_mutated():
    copy = [row[:] for row in EASY]
    solve(EASY)
    assert EASY == copy


def test_conflict_detected():
    bad = [row[:] for row in EASY]
    bad[0][2] = 5  # duplicate 5 in row 0
    assert (0, 0) in validate(bad) and (0, 2) in validate(bad)
    with pytest.raises(InvalidGridError):
        solve(bad)


def test_unsolvable_but_valid():
    g = [[0]*9 for _ in range(9)]
    g[0][:8] = [1,2,3,4,5,6,7,8]
    g[1][8] = 9  # cell (0,8) has no candidate
    r = solve(g)
    assert validate(g) == [] and not r.solvable


@pytest.mark.parametrize("bad", [[[0]*9]*8, [[0]*8]*9, [[10]+[0]*8]+[[0]*9]*8])
def test_bad_shape_or_values(bad):
    with pytest.raises(InvalidGridError):
        validate(bad)


def test_step_cap_truncates():
    r = solve(HARD, "naive", max_recorded_steps=100, max_total_steps=10_000)
    assert len(r.steps) <= 100
    assert r.total_steps >= len(r.steps)


def test_steps_replay_to_solution():
    r = solve(EASY)
    board = [row[:] for row in EASY]
    for rr, cc, v, _ in r.steps:
        board[rr][cc] = v
    assert board == r.solution