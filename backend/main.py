import os
import io
import time
from uuid import uuid4
from typing import List, Optional, Dict, Any

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from backend.solver_service import solve_sudoku, find_conflicts, validate_grid
from backend.cv_pipeline import (
    find_grid_corners,
    warp_grid,
    split_cells,
    overlay_solution,
    unwarp_overlay,
    image_to_base64
)
from backend.model_service import SudokuDigitRecognizer

# Setup directories
SAMPLES_DIR = os.path.abspath("data/raw")
TEST_SAMPLES_DIR = os.path.abspath("data/test_set")

app = FastAPI(
    title="Sudoku AI Engine API",
    description="State-of-the-art Computer Vision & Deep Learning Sudoku Detection and Solver API",
    version="2.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize CNN digit recognizer
recognizer = SudokuDigitRecognizer("models/digit_classifier.keras")


# ----------------------------------------------------
# Request & Response Schemas
# ----------------------------------------------------

class GridSolveRequest(BaseModel):
    grid: List[List[int]] = Field(..., description="9x9 integer grid, 0 for empty")
    record_steps: Optional[bool] = False

class GridSolveResponse(BaseModel):
    success: bool
    solved_grid: Optional[List[List[int]]] = None
    nodes_explored: int
    solve_time_ms: float
    conflicts: List[Dict[str, Any]] = []
    message: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None

class ValidationResponse(BaseModel):
    valid: bool
    conflicts: List[Dict[str, Any]]


# ----------------------------------------------------
# API Routes
# ----------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "engine": "FastAPI + OpenCV + TensorFlow",
        "model_loaded": recognizer.is_loaded,
        "classes": recognizer.class_names
    }


@app.get("/api/samples")
def get_sample_images():
    """Return available pre-packaged Sudoku sample images."""
    samples = []

    # Check data/test_set
    if os.path.exists(TEST_SAMPLES_DIR):
        for f in os.listdir(TEST_SAMPLES_DIR):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                samples.append({
                    "id": f"test_{f}",
                    "name": f"Digital Crisp ({f})",
                    "filename": f,
                    "category": "Digital",
                    "folder": "test_set"
                })

    # Check data/raw
    if os.path.exists(SAMPLES_DIR):
        for f in os.listdir(SAMPLES_DIR):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                samples.append({
                    "id": f"raw_{f}",
                    "name": f"Real-world Photo ({f})",
                    "filename": f,
                    "category": "Perspective Paper",
                    "folder": "raw"
                })

    return {"samples": samples}


@app.get("/api/sample-image/{folder}/{filename}")
def get_sample_file(folder: str, filename: str):
    base_folder = SAMPLES_DIR if folder == "raw" else TEST_SAMPLES_DIR
    file_path = os.path.join(base_folder, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample image not found")
    return FileResponse(file_path)


@app.post("/api/validate-grid", response_model=ValidationResponse)
def validate_user_grid(req: GridSolveRequest):
    conflicts = find_conflicts(req.grid)
    return ValidationResponse(valid=(len(conflicts) == 0), conflicts=conflicts)


@app.post("/api/solve-grid", response_model=GridSolveResponse)
def solve_grid_endpoint(req: GridSolveRequest):
    conflicts = find_conflicts(req.grid)
    if conflicts:
        return GridSolveResponse(
            success=False,
            solved_grid=req.grid,
            nodes_explored=0,
            solve_time_ms=0.0,
            conflicts=conflicts,
            message="The grid contains contradictory numbers in row, column, or 3x3 block."
        )

    success, solved_grid, nodes, time_ms, steps = solve_sudoku(
        req.grid,
        record_steps=req.record_steps or False
    )

    if not success:
        return GridSolveResponse(
            success=False,
            solved_grid=req.grid,
            nodes_explored=nodes,
            solve_time_ms=time_ms,
            conflicts=[],
            message="No valid solution exists for this configuration."
        )

    return GridSolveResponse(
        success=True,
        solved_grid=solved_grid,
        nodes_explored=nodes,
        solve_time_ms=time_ms,
        conflicts=[],
        steps=steps if req.record_steps else None
    )


@app.post("/api/process-image")
async def process_image_endpoint(
    file: Optional[UploadFile] = File(None),
    sample_folder: Optional[str] = Query(None),
    sample_file: Optional[str] = Query(None)
):
    """
    Main Computer Vision & Deep Learning pipeline:
    1. Read and decode image
    2. Detect outer 4 corners of Sudoku grid
    3. Warp perspective to 900x900 square
    4. Extract 81 cell images and predict digits via CNN
    5. Solve via Backtracking
    6. Overlay solution on warped grid & unwarp onto original photo
    """
    image_bytes = None

    if file is not None and file.filename:
        image_bytes = await file.read()
    elif sample_folder and sample_file:
        base_folder = SAMPLES_DIR if sample_folder == "raw" else TEST_SAMPLES_DIR
        file_path = os.path.join(base_folder, sample_file)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Sample image not found")
        with open(file_path, "rb") as f:
            image_bytes = f.read()
    else:
        raise HTTPException(status_code=400, detail="No image file or sample provided.")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image data.")

    # Decode image with OpenCV
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Unable to decode image file. Please provide a valid JPG, PNG, or WEBP image.")

    # 1. Grid Corner Detection
    corners = find_grid_corners(image)
    if corners is None:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error_type": "GRID_DETECTION_FAILED",
                "message": "Could not detect a 9x9 Sudoku grid. Ensure good lighting, high contrast, and that all four grid borders are clearly visible."
            }
        )

    # 2. Perspective Warp
    try:
        warped, M = warp_grid(image, corners, size=900)
    except Exception as e:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error_type": "WARP_FAILED",
                "message": f"Perspective transformation failed: {str(e)}"
            }
        )

    # 3. Cell Extraction & CNN Digit Recognition
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    cells = split_cells(warped_gray, margin=4)

    try:
        original_grid, confidences, cell_details = recognizer.recognize_sudoku(cells)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_type": "CNN_INFERENCE_FAILED",
                "message": f"Digit classification error: {str(e)}"
            }
        )

    # Calculate recognition stats
    digits_detected = sum(1 for row in original_grid for val in row if val != 0)
    avg_confidence = float(np.mean([conf for row in confidences for conf in row]))

    # Identify low-confidence cells for diagnostics
    low_confidence_cells = [
        d for d in cell_details
        if d["digit"] != 0 and d["confidence"] < 0.90
    ]

    # Check for digit conflicts before solving
    conflicts = find_conflicts(original_grid)

    # 4. Solve Puzzle
    solved_grid = None
    solve_success = False
    nodes_explored = 0
    solve_time_ms = 0.0
    solve_message = None

    if not conflicts:
        solve_success, solved_grid, nodes_explored, solve_time_ms, _ = solve_sudoku(original_grid)
        if not solve_success:
            solve_message = (
                "The CNN recognized the grid but the puzzle has no valid solution. "
                "This usually means one or more digits were misclassified. "
                f"{len(low_confidence_cells)} cell(s) had confidence < 90%. "
                "Try a higher-quality image or better lighting."
            )
    else:
        solve_message = (
            f"Detected {len(conflicts)} conflicting digit(s) — likely misclassification. "
            f"{len(low_confidence_cells)} cell(s) had confidence < 90%. "
            "Check the cell_details field for suspect predictions."
        )

    # 5. Visual Overlays
    warped_solution_b64 = None
    augmented_solution_b64 = None

    if solve_success and solved_grid:
        # Overlay on warped
        warped_solution = overlay_solution(warped, original_grid, solved_grid)
        # Unwarp back to original photo
        augmented_solution = unwarp_overlay(image, warped_solution, M)

        warped_solution_b64 = image_to_base64(warped_solution)
        augmented_solution_b64 = image_to_base64(augmented_solution)

    # Draw detected polygon outline on copy of original image
    annotated_orig = image.copy()
    cv2.polylines(annotated_orig, [corners.astype(np.int32)], isClosed=True, color=(0, 240, 255), thickness=3)

    return {
        "success": True,
        "solve_success": solve_success,
        "solve_message": solve_message,
        "corners": corners.tolist(),
        "original_grid": original_grid,
        "solved_grid": solved_grid if solve_success else None,
        "confidences": confidences,
        "cell_details": cell_details,
        "low_confidence_cells": low_confidence_cells,
        "conflicts": conflicts,
        "metrics": {
            "digits_detected": digits_detected,
            "avg_confidence": round(avg_confidence, 3),
            "solve_time_ms": solve_time_ms,
            "nodes_explored": nodes_explored,
            "image_dimensions": {"width": image.shape[1], "height": image.shape[0]}
        },
        "images": {
            "original_b64": image_to_base64(image),
            "detected_corners_b64": image_to_base64(annotated_orig),
            "warped_b64": image_to_base64(warped),
            "warped_solution_b64": warped_solution_b64,
            "augmented_solution_b64": augmented_solution_b64
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
