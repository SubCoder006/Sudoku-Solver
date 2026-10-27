import os
import cv2
import numpy as np
import tensorflow as tf
from typing import Tuple, List, Dict, Any, Optional

CLASS_NAMES = [
    "1", "2", "3", "4", "5",
    "6", "7", "8", "9", "empty"
]

# Minimum confidence to trust a digit prediction.
# Cells below this threshold are treated as empty to avoid
# injecting false digits that make the puzzle unsolvable.
DIGIT_CONFIDENCE_THRESHOLD = 0.75


class SudokuDigitRecognizer:
    def __init__(self, model_path: str = "models/digit_classifier.keras"):
        self.model_path = model_path
        self.model: Optional[tf.keras.Model] = None
        self.class_names = CLASS_NAMES
        self.is_loaded = False
        self.load_model()

    def load_model(self):
        if not os.path.exists(self.model_path):
            print(f"Warning: Model file not found at {self.model_path}")
            return
        try:
            self.model = tf.keras.models.load_model(self.model_path)
            self.is_loaded = True
            print(f"Successfully loaded CNN model from {self.model_path}")
        except Exception as e:
            print(f"Failed to load model from {self.model_path}: {e}")

    def _preprocess_cell(self, cell: np.ndarray, size: int = 28) -> np.ndarray:
        """
        Preprocess a single grayscale cell crop for CNN inference.

        Pipeline (must match training data generation exactly):
          1. Otsu THRESH_BINARY  — training data is black digit on white bg,
             so we keep the same polarity (no INV needed).
          2. cv2.resize to 28×28
          3. Normalize to float32 [0, 1]
        """
        _, thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        resized = cv2.resize(thresh, (size, size))
        return resized.astype("float32") / 255.0

    def predict_cell(self, cell_img: np.ndarray, size: int = 28) -> Tuple[str, float]:
        """
        Preprocesses a single cell patch and returns predicted class and confidence.
        """
        if self.model is None:
            raise RuntimeError("CNN model is not loaded.")

        norm = self._preprocess_cell(cell_img, size)
        input_tensor = norm.reshape(1, size, size, 1)

        pred = self.model.predict(input_tensor, verbose=0)
        class_idx = int(np.argmax(pred))
        confidence = float(np.max(pred))
        label = self.class_names[class_idx]

        # Low-confidence predictions default to empty to prevent
        # injecting wrong digits that make the puzzle unsolvable.
        if confidence < DIGIT_CONFIDENCE_THRESHOLD and label != "empty":
            label = "empty"
            confidence = 0.0

        return label, confidence

    def recognize_sudoku(
        self, cells: List[np.ndarray]
    ) -> Tuple[List[List[int]], List[List[float]], List[Dict[str, Any]]]:
        """
        Runs batch inference on 81 cell crops.

        Returns:
            - original_grid: 9×9 list of ints (0 for empty)
            - confidences:   9×9 list of float confidences (0.0 to 1.0)
            - cell_details:  list of 81 dicts with {row, col, digit, confidence, label}
        """
        if self.model is None:
            raise RuntimeError("CNN model is not loaded.")

        # Batch preprocess (faster than 81 individual predict calls)
        preprocessed = [
            self._preprocess_cell(cell).reshape(28, 28, 1)
            for cell in cells
        ]
        batch_tensor = np.array(preprocessed)
        predictions = self.model.predict(batch_tensor, verbose=0)

        grid: List[List[int]] = []
        confidences: List[List[float]] = []
        details: List[Dict[str, Any]] = []

        for row in range(9):
            grid_row: List[int] = []
            conf_row: List[float] = []
            for col in range(9):
                idx = row * 9 + col
                pred = predictions[idx]
                class_idx = int(np.argmax(pred))
                confidence = float(np.max(pred))
                label = self.class_names[class_idx]

                # Treat low-confidence digit predictions as empty to prevent
                # false conflicts that block the solver from running.
                if confidence < DIGIT_CONFIDENCE_THRESHOLD and label != "empty":
                    label = "empty"
                    confidence = 0.0

                digit = 0 if label == "empty" else int(label)

                grid_row.append(digit)
                conf_row.append(confidence)
                details.append({
                    "row": row,
                    "col": col,
                    "digit": digit,
                    "confidence": round(confidence, 3),
                    "label": label
                })
            grid.append(grid_row)
            confidences.append(conf_row)

        return grid, confidences, details
