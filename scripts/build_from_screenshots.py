"""
Auto-label + retrain from real Sudoku screenshots.

HOW TO USE:
1. Drop Sudoku screenshot images into: data/raw_screenshots/
2. Run this script: python scripts/build_from_screenshots.py
3. It will:
   a. Detect the grid in each image
   b. Extract 81 cells
   c. Use current model to auto-label (high-confidence only)
   d. Save labeled cells to data/digits_real/
   e. Combine with synthetic digits_v2/ and retrain

4. Review data/digits_real/ visually before retraining if desired.
"""
import sys
import cv2
import numpy as np
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import tensorflow as tf
from backend.cv_pipeline import find_grid_corners, warp_grid, split_cells

PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "data" / "raw_screenshots"
REAL_DIGITS_DIR = PROJECT_ROOT / "data" / "digits_real"
SYNTHETIC_DIR   = PROJECT_ROOT / "data" / "digits_v2"
MODEL_PATH      = PROJECT_ROOT / "models" / "digit_classifier.keras"
MODELS_DIR      = PROJECT_ROOT / "models"

CLASS_NAMES = ["1","2","3","4","5","6","7","8","9","empty"]

# Only accept predictions with confidence above this for auto-labeling
AUTO_LABEL_CONFIDENCE = 0.92


def extract_and_label_screenshot(img_path: Path, model, out_dir: Path) -> dict:
    """
    Run CV pipeline on one screenshot, extract cells, auto-label confident ones.
    Returns stats dict.
    """
    img_bgr = cv2.imread(str(img_path))
    if img_bgr is None:
        print(f"  [SKIP] Cannot read: {img_path.name}")
        return {}

    corners = find_grid_corners(img_bgr)
    if corners is None:
        print(f"  [SKIP] Grid not detected in: {img_path.name}")
        return {}

    warped, _ = warp_grid(img_bgr, corners, size=900)
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    cells = split_cells(warped_gray, margin=4)

    # Batch preprocess
    preprocessed = []
    for cell in cells:
        _, thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        r = cv2.resize(thresh, (28, 28)).astype("float32") / 255.0
        preprocessed.append(r.reshape(28, 28, 1))

    batch = np.array(preprocessed)
    preds = model.predict(batch, verbose=0)

    saved = 0
    skipped_low_conf = 0

    for i, (cell, pred) in enumerate(zip(cells, preds)):
        cls_idx = int(np.argmax(pred))
        confidence = float(np.max(pred))
        label = CLASS_NAMES[cls_idx]

        if confidence < AUTO_LABEL_CONFIDENCE:
            skipped_low_conf += 1
            continue

        # Save the raw cell (pre-threshold) so retraining pipeline
        # can apply its own threshold — this is correct
        cls_dir = out_dir / label
        cls_dir.mkdir(parents=True, exist_ok=True)

        stem = f"{img_path.stem}_cell{i:02d}"
        save_path = cls_dir / f"{stem}.png"

        # Save resized to 28x28 (already processed)
        _, thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        final = cv2.resize(thresh, (28, 28))
        cv2.imwrite(str(save_path), final)
        saved += 1

    print(f"  {img_path.name}: {saved} cells labeled, {skipped_low_conf} skipped (low confidence)")
    return {"saved": saved, "skipped": skipped_low_conf}


def retrain_combined(real_dir: Path, synthetic_dir: Path, model_save_path: Path):
    """Train on combined real + synthetic data."""
    from tensorflow.keras import layers, models, callbacks

    tf.keras.utils.set_random_seed(42)
    IMG_SIZE = (28, 28)
    BATCH_SIZE = 64

    # Check counts
    total_real = sum(len(list(d.glob("*.png"))) for d in real_dir.iterdir() if d.is_dir()) if real_dir.exists() else 0
    total_syn  = sum(len(list(d.glob("*.png"))) for d in synthetic_dir.iterdir() if d.is_dir()) if synthetic_dir.exists() else 0
    print(f"\nDataset: {total_real} real + {total_syn} synthetic = {total_real+total_syn} total")

    # Combine via tf.data — load both directories, merge datasets
    def load_dir(path):
        return tf.keras.utils.image_dataset_from_directory(
            path,
            image_size=IMG_SIZE,
            color_mode="grayscale",
            batch_size=BATCH_SIZE,
            seed=42,
            interpolation="bilinear"
        )

    datasets = []
    class_names = None

    if synthetic_dir.exists() and total_syn > 0:
        ds_syn = load_dir(synthetic_dir)
        class_names = ds_syn.class_names
        datasets.append(ds_syn)

    if real_dir.exists() and total_real > 0:
        ds_real = load_dir(real_dir)
        if class_names is None:
            class_names = ds_real.class_names
        datasets.append(ds_real)

    if not datasets:
        print("ERROR: No training data found!")
        return

    # Split into train/val (80/20) — concatenate, split
    combined = datasets[0]
    for ds in datasets[1:]:
        combined = combined.concatenate(ds)

    # Rough 80/20 split: count batches
    total_batches = sum(1 for _ in combined)
    val_batches = max(1, int(total_batches * 0.15))
    train_ds = combined.skip(val_batches)
    val_ds   = combined.take(val_batches)

    num_classes = len(class_names)
    print(f"Classes ({num_classes}): {class_names}")

    # Normalize
    AUTOTUNE = tf.data.AUTOTUNE
    norm = layers.Rescaling(1.0 / 255.0)
    train_ds = train_ds.map(lambda x, y: (norm(x), y), num_parallel_calls=AUTOTUNE).cache().shuffle(3000).prefetch(AUTOTUNE)
    val_ds   = val_ds.map(lambda x, y: (norm(x), y), num_parallel_calls=AUTOTUNE).cache().prefetch(AUTOTUNE)

    # Architecture
    cnn = models.Sequential([
        layers.Input(shape=(28, 28, 1)),
        layers.RandomRotation(0.08),
        layers.RandomZoom(0.08),
        layers.RandomTranslation(0.06, 0.06),

        layers.Conv2D(32, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.Conv2D(32, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Dropout(0.2),

        layers.Conv2D(64, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.Conv2D(64, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Dropout(0.2),

        layers.Conv2D(128, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Dropout(0.25),

        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(num_classes, activation="softmax")
    ], name="sudoku_digit_cnn_v3")

    cnn.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    early_stop = callbacks.EarlyStopping(monitor="val_accuracy", patience=10, restore_best_weights=True, verbose=1)
    reduce_lr  = callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6, verbose=1)

    print("\nTraining ...")
    t0 = time.time()
    history = cnn.fit(
        train_ds,
        validation_data=val_ds,
        epochs=60,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )

    best_val = max(history.history["val_accuracy"])
    print(f"\nDone in {time.time()-t0:.0f}s | Best val_accuracy: {best_val*100:.2f}%")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    cnn.save(str(model_save_path))
    print(f"Model saved: {model_save_path}")


if __name__ == "__main__":
    screenshots = list(SCREENSHOTS_DIR.glob("*.png")) + list(SCREENSHOTS_DIR.glob("*.jpg")) + list(SCREENSHOTS_DIR.glob("*.jpeg"))

    if not screenshots:
        print(f"No screenshots found in {SCREENSHOTS_DIR}")
        print("Drop Sudoku screenshot images there and re-run.")
        sys.exit(0)

    print(f"Found {len(screenshots)} screenshot(s) in {SCREENSHOTS_DIR}")
    print(f"Loading model from {MODEL_PATH} ...")
    model = tf.keras.models.load_model(str(MODEL_PATH))

    REAL_DIGITS_DIR.mkdir(parents=True, exist_ok=True)

    total_saved = 0
    for img_path in screenshots:
        print(f"\nProcessing: {img_path.name}")
        stats = extract_and_label_screenshot(img_path, model, REAL_DIGITS_DIR)
        total_saved += stats.get("saved", 0)

    print(f"\n{'='*50}")
    print(f"Auto-labeled {total_saved} cells total -> {REAL_DIGITS_DIR}")

    # Show per-class counts
    if REAL_DIGITS_DIR.exists():
        print("\nPer-class real cell counts:")
        for cls_dir in sorted(REAL_DIGITS_DIR.iterdir()):
            n = len(list(cls_dir.glob("*.png")))
            print(f"  {cls_dir.name}: {n}")

    print(f"\nStarting combined retraining ...")
    retrain_combined(REAL_DIGITS_DIR, SYNTHETIC_DIR, MODEL_PATH)
