from ultralytics import YOLO
import cv2
import os
import re


def get_latest_custom_model(base_dir="runs/detect"):
    custom_dirs = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and re.match(r"yolov8n_custom\d+", d)
    ]
    if not custom_dirs:
        raise FileNotFoundError("No custom YOLO model directories found.")

    # Extract the number and sort by it
    latest = max(custom_dirs, key=lambda d: int(re.search(r"\d+", d).group()))
    return os.path.join(base_dir, latest, "weights", "best.pt")

# --- Collect all PinkGorilla images ---
def get_pink_gorilla_images(img_dir="pink_gorilla_twitter"):
    return sorted([
        os.path.join(img_dir, f)
        for f in os.listdir(img_dir)
        if re.match(r"PinkGorilla_\d+\.jpg$", f, re.IGNORECASE)
    ])


model = YOLO(get_latest_custom_model()) # Replace with your chosen model path
img_paths = get_pink_gorilla_images()

for img_path in img_paths:
    results = model.predict(source=img_path)
    # Load the image to draw on
    image = cv2.imread(img_path)

    # Iterate through the results and draw bounding boxes
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = model.names[cls]

            # Draw rectangle and put text on the image
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, f"{label} {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save output image with bounding boxes
    out_path = os.path.splitext(img_path)[0] + "_boxed.png"
    cv2.imwrite(out_path, image)
    print(f"Saved: {out_path}")
