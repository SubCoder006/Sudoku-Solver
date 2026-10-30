from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from solver.backtrack import InvalidGridError, solve, validate

app = FastAPI(title="Sudoku Solver API")


class SolveRequest(BaseModel):
    grid: list[list[int]]
    strategy: Literal["naive", "mrv"] = "mrv"

    @field_validator("grid")
    @classmethod
    def check_shape(cls, g):
        if len(g) != 9 or any(len(r) != 9 for r in g):
            raise ValueError("grid must be 9x9")
        if any(not 0 <= v <= 9 for r in g for v in r):
            raise ValueError("cells must be 0-9")
        return g


class SolveResponse(BaseModel):
    solvable: bool
    solution: list[list[int]] | None
    steps: list[tuple[int, int, int, int]]
    total_steps: int
    backtracks: int
    truncated: bool
    aborted: bool
    elapsed_ms: float


class ValidateResponse(BaseModel):
    valid: bool
    conflicts: list[tuple[int, int]]


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/validate", response_model=ValidateResponse)
def validate_grid(req: SolveRequest):
    conflicts = validate(req.grid)
    return ValidateResponse(valid=not conflicts, conflicts=conflicts)


@app.post("/api/solve", response_model=SolveResponse)
def solve_grid(req: SolveRequest):
    try:
        result = solve(req.grid, req.strategy)
    except InvalidGridError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SolveResponse(**result.__dict__)

class GridRequest(BaseModel):
    grid: list[list[int]]

    @field_validator("grid")
    @classmethod
    def check_shape(cls, g):
        if len(g) != 9 or any(len(r) != 9 for r in g):
            raise ValueError("grid must be 9x9")
        if any(not 0 <= v <= 9 for r in g for v in r):
            raise ValueError("cells must be 0-9")
        return g


class SolveRequest(GridRequest):
    strategy: Literal["naive", "mrv"] = "mrv"
    
class CompareRow(BaseModel):
    strategy: str
    solvable: bool
    aborted: bool
    total_steps: int
    backtracks: int
    elapsed_ms: float


class CompareResponse(BaseModel):
    results: list[CompareRow]


@app.post("/api/compare", response_model=CompareResponse)
def compare(req: GridRequest):
    rows = []
    for strategy in ("naive", "mrv"):
        try:
            r = solve(req.grid, strategy, max_recorded_steps=0, max_total_steps=1_000_000)
        except InvalidGridError as e:
            raise HTTPException(status_code=422, detail=str(e))
        rows.append(CompareRow(
            strategy=strategy, solvable=r.solvable, aborted=r.aborted,
            total_steps=r.total_steps, backtracks=r.backtracks, elapsed_ms=r.elapsed_ms,
        ))
    return CompareResponse(results=rows)



STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.is_dir():  # only exists inside the Docker image
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")