from ultralytics import YOLO
import cv2
import os

model = YOLO("runs/detect/yolov8n_custom15/weights/best.pt") # Replace with your chosen model path

img_paths = [
    "pink_gorilla_twitter/PinkGorilla_1.jpg",
    "pink_gorilla_twitter/PinkGorilla_2.jpg",
    "pink_gorilla_twitter/PinkGorilla_3.jpg",
    "pink_gorilla_twitter/PinkGorilla_4.jpg"
]

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
