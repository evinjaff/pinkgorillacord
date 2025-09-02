from ultralytics import YOLO
 
# Load the model.
model = YOLO('yolov8n.pt')
 
# Training.
results = model.train(
   data='games_v8.yaml',
   imgsz=640,
   epochs=150,
   batch=8,
   name='yolov8n_custom',
   device="mps"
   )