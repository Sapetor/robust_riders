"""
Train YOLOv8 Classification Model for Road Features - ACC 2026

Prerequisites:
1. pip install ultralytics
2. Capture training images with: python capture_training_data.py
3. Images should be in datasets/road_features/{class_name}/

This trains a classification model (not detection) since we want
to classify the entire frame as a road type.

Usage:
    python train_yolo.py

Output:
    models/road_features.pt
"""

import os
import shutil
from pathlib import Path

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Error: ultralytics not installed")
    print("Run: pip install ultralytics")
    exit(1)


# Paths
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "datasets" / "road_features"
TRAIN_DIR = BASE_DIR / "datasets" / "road_features_split" / "train"
VAL_DIR = BASE_DIR / "datasets" / "road_features_split" / "val"
MODEL_DIR = BASE_DIR / "models"

# Classes
CLASSES = ['straight', 'curve_left', 'curve_right', 'intersection', 'roundabout']


def count_images():
    """Count images in each class."""
    counts = {}
    total = 0
    for class_name in CLASSES:
        class_dir = DATASET_DIR / class_name
        if class_dir.exists():
            count = len(list(class_dir.glob("*.jpg")))
            counts[class_name] = count
            total += count
        else:
            counts[class_name] = 0
    return counts, total


def prepare_dataset(val_split: float = 0.2):
    """
    Split dataset into train/val folders for YOLO.

    YOLO classification expects:
    datasets/road_features_split/
        train/
            straight/
            curve_left/
            ...
        val/
            straight/
            curve_left/
            ...
    """
    import random

    print("Preparing dataset...")

    # Clean existing split
    split_dir = BASE_DIR / "datasets" / "road_features_split"
    if split_dir.exists():
        shutil.rmtree(split_dir)

    # Create directories
    for class_name in CLASSES:
        (TRAIN_DIR / class_name).mkdir(parents=True, exist_ok=True)
        (VAL_DIR / class_name).mkdir(parents=True, exist_ok=True)

    # Split each class
    for class_name in CLASSES:
        source_dir = DATASET_DIR / class_name
        if not source_dir.exists():
            print(f"  Warning: No images for {class_name}")
            continue

        images = list(source_dir.glob("*.jpg"))
        random.shuffle(images)

        val_count = max(1, int(len(images) * val_split))
        val_images = images[:val_count]
        train_images = images[val_count:]

        for img in train_images:
            shutil.copy(img, TRAIN_DIR / class_name / img.name)

        for img in val_images:
            shutil.copy(img, VAL_DIR / class_name / img.name)

        print(f"  {class_name}: {len(train_images)} train, {len(val_images)} val")

    print("Dataset ready!")


def train_model(epochs: int = 50, imgsz: int = 224):
    """
    Train YOLOv8 classification model.

    Args:
        epochs: Number of training epochs
        imgsz: Image size for training
    """
    print(f"\nTraining YOLOv8 classification model...")
    print(f"  Epochs: {epochs}")
    print(f"  Image size: {imgsz}")

    # Use YOLOv8 nano classification model as base
    model = YOLO('yolov8n-cls.pt')

    # Train
    results = model.train(
        data=str(BASE_DIR / "datasets" / "road_features_split"),
        epochs=epochs,
        imgsz=imgsz,
        batch=16,
        patience=10,  # Early stopping
        save=True,
        project=str(BASE_DIR / "runs"),
        name="road_features",
        exist_ok=True,
    )

    # Copy best model to models/
    MODEL_DIR.mkdir(exist_ok=True)
    best_model = Path(results.save_dir) / "weights" / "best.pt"

    if best_model.exists():
        dest = MODEL_DIR / "road_features.pt"
        shutil.copy(best_model, dest)
        print(f"\nModel saved to: {dest}")
    else:
        print("Warning: Could not find best.pt")

    return results


def test_model():
    """Quick test of trained model."""
    model_path = MODEL_DIR / "road_features.pt"

    if not model_path.exists():
        print("No trained model found. Train first!")
        return

    print(f"\nTesting model: {model_path}")

    model = YOLO(str(model_path))

    # Test on a few validation images
    val_images = list(VAL_DIR.glob("*/*.jpg"))[:5]

    if not val_images:
        print("No validation images to test")
        return

    for img_path in val_images:
        results = model(str(img_path), verbose=False)
        if results and results[0].probs:
            probs = results[0].probs
            pred_class = results[0].names[probs.top1]
            confidence = probs.top1conf.item()
            actual_class = img_path.parent.name
            match = "OK" if pred_class == actual_class else "WRONG"
            print(f"  {actual_class} -> {pred_class} ({confidence:.0%}) {match}")


def main():
    print("=" * 60)
    print("  YOLOv8 Road Feature Training - ACC 2026")
    print("=" * 60)

    # Check dataset
    counts, total = count_images()
    print("\nDataset status:")
    for class_name, count in counts.items():
        status = "OK" if count >= 20 else "LOW" if count > 0 else "EMPTY"
        print(f"  {class_name}: {count} images [{status}]")
    print(f"  Total: {total} images")

    if total < 50:
        print("\nWarning: Need more training images!")
        print("Recommended: At least 50 images per class (250 total)")
        print("Run: python capture_training_data.py")

        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Prepare dataset
    prepare_dataset()

    # Train
    print("\n" + "=" * 60)
    epochs = 50
    try:
        epochs_input = input(f"Training epochs [{epochs}]: ").strip()
        if epochs_input:
            epochs = int(epochs_input)
    except ValueError:
        pass

    train_model(epochs=epochs)

    # Test
    print("\n" + "=" * 60)
    test_model()

    print("\n" + "=" * 60)
    print("  Training complete!")
    print("  Model: models/road_features.pt")
    print("  To use: from yolo_road_detector import YOLONavigationAdvisor")
    print("=" * 60)


if __name__ == '__main__':
    main()
