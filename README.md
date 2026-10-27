# 🧩 Sudoku AI Engine 2.0 | Neural Vision & Logic Solver

A state-of-the-art Computer Vision & Deep Learning full-stack application that detects 9×9 Sudoku puzzles from photos, corrects camera perspective tilt, recognizes handwritten/printed digits using a Convolutional Neural Network (CNN), and solves the puzzle in real-time with an optimized backtracking algorithm with Most Constrained Variable (MCV) heuristics.

---

## ⚡ Architecture Overview

```
Sudoku-Solver/
├── backend/
│   ├── main.py              # FastAPI application (REST API, CORS, static serving)
│   ├── cv_pipeline.py       # OpenCV corner detection, 900x900 warp, cell split, AR overlay
│   ├── model_service.py     # TensorFlow Keras CNN batch digit classification & confidence
│   └── solver_service.py    # Backtracking solver (MCV heuristic) & conflict validation
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SudokuBoard.jsx      # Interactive 9x9 grid with keyboard & keypad entry
│   │   │   ├── VisionInspector.jsx  # Multi-stage CV inspection (AR overlay, rectified grid)
│   │   │   ├── ImageDropzone.jsx    # Glassmorphic drag-and-drop upload zone
│   │   │   ├── SampleGallery.jsx    # 1-Click test presets (digital & perspective newspaper)
│   │   │   └── SolverStats.jsx      # Real-time metrics (confidence, nodes, duration)
│   │   ├── index.css                # Obsidian & Cyber-Indigo design system
│   │   └── App.jsx                  # Main application state & confetti celebration
│   └── vite.config.js               # Dev server with /api proxy to FastAPI
│
├── models/
│   └── digit_classifier.keras       # Trained CNN digit recognition weights
└── data/
    ├── raw/                         # Real-world photo samples
    └── test_set/                    # Crisp digital test samples
```

---

## 🚀 Getting Started

### 1. Backend (Python + FastAPI)

Activate the virtual environment and start the server:

```bash
# Windows
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

API documentation is automatically available at:
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Frontend (React + Vite)

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open your browser at:
- **Application UI**: [http://localhost:5173/](http://localhost:5173/)

---

## ✨ Features

- **Augmented Reality Unwarping**: Solved digits are projected back onto the original tilted photo angle using inverse homography perspective matrices.
- **Interactive 9×9 Matrix**: Click any cell, use arrow keys, or use the on-screen keypad to edit digits, test custom puzzles, or fix misread numbers.
- **Real-Time Conflict Highlighting**: Detects rule violations in rows, columns, or 3×3 blocks before solving.
- **Multi-Stage Computer Vision Inspector**: View Raw Upload, Detected Polygon Outline, 900×900 Rectified Grayscale Grid, and AR Solution Overlay.
- **1-Click Preset Gallery**: Test immediately with digital and perspective newspaper camera samples.
- **Comprehensive Metrics**: Displays digits detected, average CNN recognition confidence, solver search nodes, and solve execution duration.
