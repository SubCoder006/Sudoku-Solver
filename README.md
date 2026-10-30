# Sudoku Solver

Backtracking Sudoku solver with a live, scrubbable step-by-step animation.
FastAPI backend, React frontend, tested and containerized.

![demo](docs/demo.gif)

## Features
- Edit the grid with the keyboard, with live conflict highlighting
- Solve with **naive** or **MRV** (Minimum Remaining Values) backtracking
- Animated playback: play/pause, step back and forward, speed control, scrubber
- Compare strategies side by side (steps, backtracks, wall time)
- Input validation, step and runtime caps, 24 automated tests, CI on every push

## Results

| Puzzle | Strategy | Steps | Backtracks |
|---|---|---|---|
| Easy | Naive | 8,365 | 4,157 |
| Easy | MRV | 51 | 0 |
| Hard (Inkala) | Naive | 99,056 | 49,498 |
| Hard (Inkala) | MRV | 27,560 | 13,750 |

MRV cut search steps by about 164x on the easy puzzle and 3.6x on the hard one.

## Architecture

    React (Vite)  --/api-->  FastAPI  -->  solver (bitmask backtracking)

The backend records every step as a compact (row, col, value, action) tuple.
The browser replays them, so scrubbing and speed control cost nothing.

## Run locally

    # backend
    cd backend
    python -m venv .venv && .venv\Scripts\activate
    pip install -r requirements-dev.txt
    uvicorn main:app --reload --port 8000

    # frontend (second terminal)
    cd frontend
    npm install && npm run dev

Open http://localhost:5173.

## Run with Docker

    docker build -t sudoku .
    docker run --rm -p 8000:8000 sudoku

Open http://localhost:8000.

## Tests

    cd backend
    python -m pytest -q

## Roadmap
- [x] v1: solver, API, animated UI, tests, CI, Docker
- [ ] v2: photo recognition (OpenCV + CNN) with a correction UI
- [ ] v3: LLM explanations and an evaluation harness