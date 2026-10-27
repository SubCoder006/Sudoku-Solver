import base64
import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

def order_corners(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 polygon corners as:
    [top-left, top-right, bottom-right, bottom-left]
    """
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()

    return np.array([
        pts[np.argmin(s)],  # top-left
        pts[np.argmin(d)],  # top-right
        pts[np.argmax(s)],  # bottom-right
        pts[np.argmax(d)]   # bottom-left
    ], dtype=np.float32)


def find_grid_corners(img: np.ndarray) -> Optional[np.ndarray]:
    """
    Detects the 4 corners of the Sudoku outer square border.
    Uses adaptive thresholding, contour area filtering, and aspect ratio checks.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    image_area = img.shape[0] * img.shape[1]
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours[:100]:
        area = cv2.contourArea(contour)
        if area < image_area * 0.05:
            continue

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

        if len(approx) != 4:
            continue

        if not cv2.isContourConvex(approx):
            continue

        corners = order_corners(approx)
        top = np.linalg.norm(corners[1] - corners[0])
        bottom = np.linalg.norm(corners[2] - corners[3])
        left = np.linalg.norm(corners[3] - corners[0])
        right = np.linalg.norm(corners[2] - corners[1])

        width = (top + bottom) / 2
        height = (left + right) / 2

        if min(width, height) < 1:
            continue

        ratio = width / height
        if 0.65 <= ratio <= 1.5:
            return corners

    return None


def warp_grid(img: np.ndarray, corners: np.ndarray, size: int = 900) -> Tuple[np.ndarray, np.ndarray]:
    """
    Applies perspective transformation to crop and rectify the Sudoku grid to size x size.
    """
    dst = np.array([
        [0, 0],
        [size - 1, 0],
        [size - 1, size - 1],
        [0, size - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
    warped = cv2.warpPerspective(img, M, (size, size))
    return warped, M


def split_cells(warped_gray: np.ndarray, margin: int = 4) -> List[np.ndarray]:
    """
    Splits the 9x9 warped grayscale image into 81 individual cell patches.
    Margin strips border lines from interfering with CNN digit classification.
    """
    size = warped_gray.shape[0]
    cell_size = size // 9
    cells = []
    for row in range(9):
        for col in range(9):
            y1 = row * cell_size + margin
            y2 = (row + 1) * cell_size - margin
            x1 = col * cell_size + margin
            x2 = (col + 1) * cell_size - margin
            cells.append(warped_gray[y1:y2, x1:x2])
    return cells


def overlay_solution(
    warped_img: np.ndarray,
    original_grid: List[List[int]],
    solved_grid: List[List[int]],
    cell_size: Optional[int] = None
) -> np.ndarray:
    """
    Renders the newly solved numbers in vibrant modern emerald green with an elegant backing glow
    onto the warped grid.
    """
    overlay = warped_img.copy()
    if cell_size is None:
        cell_size = warped_img.shape[0] // 9

    font = cv2.FONT_HERSHEY_DUPLEX
    scale = cell_size / 75.0
    thickness = max(2, int(cell_size / 30.0))

    for row in range(9):
        for col in range(9):
            if original_grid[row][col] == 0 and solved_grid[row][col] != 0:
                digit = str(solved_grid[row][col])
                text_size, _ = cv2.getTextSize(digit, font, scale, thickness)
                x = col * cell_size + (cell_size - text_size[0]) // 2
                y = row * cell_size + (cell_size + text_size[1]) // 2

                # Subtle shadow for clarity
                cv2.putText(overlay, digit, (x + 2, y + 2), font, scale, (15, 35, 20), thickness + 2, cv2.LINE_AA)
                # Emerald green solved digit
                cv2.putText(overlay, digit, (x, y), font, scale, (34, 197, 94), thickness, cv2.LINE_AA)

    return overlay


def unwarp_overlay(
    original_img: np.ndarray,
    overlay_img: np.ndarray,
    M: np.ndarray
) -> np.ndarray:
    """
    Inverts the perspective transform M to cast the solved digits back onto the original angled photo.
    """
    h, w = original_img.shape[:2]
    M_inv = np.linalg.inv(M)

    unwarped_overlay = cv2.warpPerspective(overlay_img, M_inv, (w, h))
    mask = cv2.warpPerspective(np.ones_like(overlay_img) * 255, M_inv, (w, h))

    mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    _, mask_binary = cv2.threshold(mask_gray, 1, 255, cv2.THRESH_BINARY)

    final = original_img.copy()
    final[mask_binary > 0] = unwarped_overlay[mask_binary > 0]
    return final


def image_to_base64(img: np.ndarray, format: str = ".jpg", quality: int = 88) -> str:
    """Converts an OpenCV image to a base64 Data URL."""
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality] if format in [".jpg", ".jpeg"] else []
    success, buffer = cv2.imencode(format, img, encode_params)
    if not success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    mime = "image/jpeg" if format in [".jpg", ".jpeg"] else "image/png"
    return f"data:{mime};base64,{b64_str}"
