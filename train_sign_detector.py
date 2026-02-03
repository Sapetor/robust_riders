"""
Train YOLOv8 Object Detection Model for Road Signs - ACC 2026

Prerequisites:
1. pip install ultralytics
2. Capture training images with: python capture_sign_data.py
3. Images should be in datasets/signs/images/
4. Labels should be in datasets/signs/labels/ (YOLO format)

This trains an object detection model (not classification) to find
and localize signs within images.

Classes:
- 0: stop
- 1: yield
- 2: roundabout

Usage:
    python train_sign_detector.py

Output:
    models/sign_detector.pt
"""

import os
import shutil
import random
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
DATASET_DIR = BASE_DIR / "datasets" / "signs"
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"

SPLIT_DIR = BASE_DIR / "datasets" / "signs_split"
TRAIN_IMAGES = SPLIT_DIR / "train" / "images"
TRAIN_LABELS = SPLIT_DIR / "train" / "labels"
VAL_IMAGES = SPLIT_DIR / "val" / "images"
VAL_LABELS = SPLIT_DIR / "val" / "labels"

MODEL_DIR = BASE_DIR / "models"

# Sign classes
SIGN_NAMES = ['stop', 'yield', 'roundabout']


def count_data():
    """Count images and labels."""
    if not IMAGES_DIR.exists() or not LABELS_DIR.exists():
        return 0, 0

    images = list(IMAGES_DIR.glob("*.jpg"))
    labels = list(LABELS_DIR.glob("*.txt"))

    return len(images), len(labels)


def count_labels_by_class():
    """Count labels by class."""
    counts = {name: 0 for name in SIGN_NAMES}

    if not LABELS_DIR.exists():
        return counts

    for label_file in LABELS_DIR.glob("*.txt"):
        with open(label_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    class_id = int(parts[0])
                    if 0 <= class_id < len(SIGN_NAMES):
                        counts[SIGN_NAMES[class_id]] += 1

    return counts


def create_dataset_yaml():
    """
    Create dataset.yaml for YOLO training.

    Format:
        path: /absolute/path/to/dataset
        train: train/images
        val: val/images

        names:
          0: stop
          1: yield
          2: roundabout
    """
    yaml_path = SPLIT_DIR / "dataset.yaml"

    content = f"""# Sign Detection Dataset - ACC 2026
path: {SPLIT_DIR.absolute()}
train: train/images
val: val/images

names:
  0: stop
  1: yield
  2: roundabout
"""

    with open(yaml_path, 'w') as f:
        f.write(content)

    print(f"Created: {yaml_path}")
    return yaml_path


def prepare_dataset(val_split: float = 0.2):
    """
    Split dataset into train/val for YOLO object detection.

    YOLO detection expects:
    datasets/signs_split/
        train/
            images/
            labels/
        val/
            images/
            labels/
        dataset.yaml
    """
    print("Preparing dataset...")

    # Clean existing split
    if SPLIT_DIR.exists():
        shutil.rmtree(SPLIT_DIR)

    # Create directories
    TRAIN_IMAGES.mkdir(parents=True, exist_ok=True)
    TRAIN_LABELS.mkdir(parents=True, exist_ok=True)
    VAL_IMAGES.mkdir(parents=True, exist_ok=True)
    VAL_LABELS.mkdir(parents=True, exist_ok=True)

    # Get all images that have corresponding labels
    images = []
    for img_path in IMAGES_DIR.glob("*.jpg"):
        label_path = LABELS_DIR / f"{img_path.stem}.txt"
        if label_path.exists():
            images.append(img_path)

    if not images:
        print("Error: No paired image/label files found!")
        return False

    # Shuffle and split
    random.shuffle(images)
    val_count = max(1, int(len(images) * val_split))
    val_images = images[:val_count]
    train_images = images[val_count:]

    # Copy train files
    for img_path in train_images:
        shutil.copy(img_path, TRAIN_IMAGES / img_path.name)
        label_path = LABELS_DIR / f"{img_path.stem}.txt"
        if label_path.exists():
            shutil.copy(label_path, TRAIN_LABELS / f"{img_path.stem}.txt")

    # Copy val files
    for img_path in val_images:
        shutil.copy(img_path, VAL_IMAGES / img_path.name)
        label_path = LABELS_DIR / f"{img_path.stem}.txt"
        if label_path.exists():
            shutil.copy(label_path, VAL_LABELS / f"{img_path.stem}.txt")

    print(f"  Train: {len(train_images)} images")
    print(f"  Val:   {len(val_images)} images")

    # Create dataset.yaml
    create_dataset_yaml()

    print("Dataset ready!")
    return True


def train_model(epochs: int = 100, imgsz: int = 640):
    """
    Train YOLOv8 object detection model.

    Args:
        epochs: Number of training epochs
        imgsz: Image size for training (640 is standard for detection)
    """
    print(f"\nTraining YOLOv8 object detection model...")
    print(f"  Epochs: {epochs}")
    print(f"  Image size: {imgsz}")

    # Use YOLOv8 nano detection model as base
    model = YOLO('yolov8n.pt')

    # Train
    results = model.train(
        data=str(SPLIT_DIR / "dataset.yaml"),
        epochs=epochs,
        imgsz=imgsz,
        batch=16,
        patience=20,  # Early stopping
        save=True,
        project=str(BASE_DIR / "runs"),
        name="sign_detector",
        exist_ok=True,
        verbose=True,
    )

    # Copy best model to models/
    MODEL_DIR.mkdir(exist_ok=True)
    best_model = Path(results.save_dir) / "weights" / "best.pt"

    if best_model.exists():
        dest = MODEL_DIR / "sign_detector.pt"
        shutil.copy(best_model, dest)
        print(f"\nModel saved to: {dest}")
    else:
        print("Warning: Could not find best.pt")

    return results


def test_model():
    """Quick test of trained model."""
    model_path = MODEL_DIR / "sign_detector.pt"

    if not model_path.exists():
        print("No trained model found. Train first!")
        return

    print(f"\nTesting model: {model_path}")

    model = YOLO(str(model_path))

    # Test on a few validation images
    val_images = list(VAL_IMAGES.glob("*.jpg"))[:5]

    if not val_images:
        print("No validation images to test")
        return

    print("\nSample predictions:")
    for img_path in val_images:
        results = model(str(img_path), verbose=False)

        if results and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                class_id = int(box.cls.item())
                conf = box.conf.item()
                class_name = SIGN_NAMES[class_id]
                print(f"  {img_path.name}: {class_name} ({conf:.0%})")
        else:
            print(f"  {img_path.name}: No detections")


def validate_dataset():
    """Check dataset for common issues."""
    print("\nValidating dataset...")

    issues = []

    # Check for images without labels
    for img_path in IMAGES_DIR.glob("*.jpg"):
        label_path = LABELS_DIR / f"{img_path.stem}.txt"
        if not label_path.exists():
            issues.append(f"Image without label: {img_path.name}")

    # Check for labels without images
    for label_path in LABELS_DIR.glob("*.txt"):
        img_path = IMAGES_DIR / f"{label_path.stem}.jpg"
        if not img_path.exists():
            issues.append(f"Label without image: {label_path.name}")

    # Check label format
    for label_path in LABELS_DIR.glob("*.txt"):
        with open(label_path, 'r') as f:
            for i, line in enumerate(f, 1):
                parts = line.strip().split()
                if len(parts) != 5:
                    issues.append(f"{label_path.name}:{i} - Invalid format (need 5 values)")
                    continue

                try:
                    class_id = int(parts[0])
                    if class_id < 0 or class_id >= len(SIGN_NAMES):
                        issues.append(f"{label_path.name}:{i} - Invalid class_id: {class_id}")

                    # Check normalized values
                    for j, val in enumerate(parts[1:], 1):
                        v = float(val)
                        if v < 0 or v > 1:
                            issues.append(f"{label_path.name}:{i} - Value {j} not normalized: {v}")

                except ValueError as e:
                    issues.append(f"{label_path.name}:{i} - Parse error: {e}")

    if issues:
        print(f"  Found {len(issues)} issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"    - {issue}")
        if len(issues) > 10:
            print(f"    ... and {len(issues) - 10} more")
        return False
    else:
        print("  Dataset is valid!")
        return True


def main():
    print("=" * 60)
    print("  YOLOv8 Sign Detection Training - ACC 2026")
    print("=" * 60)

    # Check dataset
    num_images, num_labels = count_data()
    print(f"\nDataset status:")
    print(f"  Images: {num_images}")
    print(f"  Labels: {num_labels}")

    if num_images == 0 or num_labels == 0:
        print("\nError: No training data found!")
        print("Run: python capture_sign_data.py")
        return

    # Show label distribution
    label_counts = count_labels_by_class()
    print("\nLabel distribution:")
    for name, count in label_counts.items():
        status = "OK" if count >= 10 else "LOW" if count > 0 else "EMPTY"
        print(f"  {name}: {count} [{status}]")

    total_labels = sum(label_counts.values())
    if total_labels < 30:
        print("\nWarning: Need more training data!")
        print("Recommended: At least 30 bounding boxes per class")
        print("             (can have multiple boxes per image)")

        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Validate dataset
    if not validate_dataset():
        response = input("\nDataset has issues. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Prepare dataset
    if not prepare_dataset():
        return

    # Train
    print("\n" + "=" * 60)
    epochs = 100
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
    print("  Model: models/sign_detector.pt")
    print("\n  To use in code:")
    print("    from perception.sign_detector import HybridSignDetector")
    print("    detector = HybridSignDetector()")
    print("    signs = detector.detect(image)")
    print("=" * 60)


if __name__ == '__main__':
    main()
