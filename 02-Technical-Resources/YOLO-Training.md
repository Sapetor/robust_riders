# YOLO Road Feature Detection - Training Guide

This guide covers training a YOLOv8 classification model to detect road features (straight roads, curves, intersections, roundabouts) for the ACC 2026 competition.

## Overview

The classical computer vision approach (edge detection, Hough transforms) proved unreliable for road feature detection. YOLO provides more robust classification by learning patterns directly from labeled images.

**Model Type:** YOLOv8 Classification (not detection)
- Classifies the entire camera frame as a road type
- Faster and simpler than object detection
- Works well for "what's ahead" classification

## Classes

| Class | Key | Description |
|-------|-----|-------------|
| `straight` | S | Straight road ahead |
| `curve_left` | L | Road curves to the left |
| `curve_right` | R | Road curves to the right |
| `intersection` | I | Junction or crossroad ahead |
| `roundabout` | O | Roundabout ahead |

## Step 1: Install Dependencies

```bash
pip install ultralytics
```

Verify installation:
```bash
python -c "from ultralytics import YOLO; print('OK')"
```

## Step 2: Capture Training Data

### Run the capture script

```bash
# In QLabs PLANE workspace
python capture_training_data.py
```

### Controls

| Key | Action |
|-----|--------|
| Arrow keys | Drive the car |
| SPACE | Stop |
| **S** | Label as STRAIGHT |
| **L** | Label as CURVE_LEFT |
| **R** | Label as CURVE_RIGHT |
| **I** | Label as INTERSECTION |
| **O** | Label as ROUNDABOUT |
| Q | Quit |

### Tips for Good Training Data

1. **Quantity**: Aim for **50+ images per class** (250+ total)
2. **Variety**: Capture from different:
   - Distances (far, medium, close)
   - Angles (centered, slightly offset)
   - Positions on the track
3. **Timing**: Press the label key when the feature is **clearly visible** ahead
4. **Multiple captures**: Press the key multiple times as you approach a feature
5. **Avoid ambiguity**: Don't label when transitioning between features

### Dataset Location

Images are saved to:
```
datasets/road_features/
├── straight/
├── curve_left/
├── curve_right/
├── intersection/
└── roundabout/
```

## Step 3: Train the Model

```bash
python train_yolo.py
```

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Epochs | 50 | Training iterations |
| Image size | 224 | Input resolution |
| Batch size | 16 | Images per batch |
| Patience | 10 | Early stopping patience |

### Training Output

- **Model saved to:** `models/road_features.pt`
- **Training logs:** `runs/road_features/`

### Expected Training Time

- ~50 images/class: 5-10 minutes (CPU)
- ~200 images/class: 15-30 minutes (CPU), 5-10 minutes (GPU)

## Step 4: Test the Model

The training script automatically tests on validation images after training.

Manual testing:
```python
from yolo_road_detector import YOLONavigationAdvisor

advisor = YOLONavigationAdvisor()
print(f"Model loaded: {advisor.is_available()}")

# Test on an image
import cv2
image = cv2.imread("test_image.jpg")
feature = advisor.update(image)
print(f"Detected: {feature.road_type.name} ({feature.confidence:.0%})")
```

## Step 5: Integration

The YOLO detector integrates into `hybrid_navigation.py` by replacing the classical CV `NavigationAdvisor` with `YOLONavigationAdvisor`.

### Current Status

- Classical CV road features: **Disabled** (toggle with R key)
- YOLO integration: **Ready** (once model is trained)

### To Enable YOLO

After training, update `hybrid_navigation.py`:

```python
# Replace this import:
from road_features import NavigationAdvisor, RoadType

# With:
from yolo_road_detector import YOLONavigationAdvisor as NavigationAdvisor, RoadType
```

## Troubleshooting

### "Model not found"
- Train the model first: `python train_yolo.py`
- Check that `models/road_features.pt` exists

### Low accuracy
- Need more training data (aim for 50+ per class)
- Check for mislabeled images
- Increase training epochs

### Slow inference
- Use smaller image size (160 instead of 224)
- Use GPU if available

## File Reference

| File | Purpose |
|------|---------|
| `capture_training_data.py` | Capture & label images |
| `train_yolo.py` | Train the model |
| `yolo_road_detector.py` | YOLO detector class |
| `models/road_features.pt` | Trained model (after training) |
| `datasets/road_features/` | Training images |

## Related

- [[Progress-Log]] - Development progress
- [[Development-Plan]] - Overall project plan
