import cv2
import time
from ultralytics import YOLO
from collections import defaultdict

# loadin the modellll
model = YOLO('models/yolo11l.pt')#changing th emodel to yolo26l 
model.to('cuda') 
class_list = model.names

# load the video 
cap = cv2.VideoCapture('sample_video/4.mp4')

if not cap.isOpened():
    print("❌ ERROR: Could not open video!")
    print("👉 make sure you run this from inside the TRAFIC/ folder")
    exit()

frame_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0

print(f"✅ Model loaded: models/yolo11l.pt")
print(f"✅ Video opened: {frame_width}x{frame_height} @ {fps:.1f} FPS")
print("⏳ Processing... Press 'Q' to quit.\n")

# ── Output Video ──
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output_tracked.avi', fourcc, fps, (frame_width, frame_height))

# count line Y position
line_y_red = 350

# count line X — left road only (x=160 to x=770)
LINE_START_X = 680   # left edge of left road
LINE_END_X   = 1030   # right edge of left road (road divider)
# Fine-tune above values if line is not perfectly on your road:
# too far left  → increase LINE_START_X (e.g. 200)
# too far right → decrease LINE_END_X   (e.g. 720)

# ── vehicle counts & tracking ──
class_counts = defaultdict(int)
crossed_ids  = set()

# COCO class indices: 1=bicycle, 2=car, 3=motorcycle, 5=bus, 6=train, 7=truck for ambulance thing idk 
VEHICLE_CLASSES = [1, 2, 3, 5, 6, 7]

# color per vehicle type
COLOR_MAP = {
    'car':        (0, 255, 0),      # green
    'bus':        (0, 165, 255),    # orange
    'truck':      (0, 0, 255),      # red
    'motorcycle': (255, 255, 0),    # cyan
    'bicycle':    (255, 0, 255),    # magenta
    'train':      (128, 0, 128),    # purple
}

# speed: skip frames
SKIP         = 2
frame_count  = 0
last_results = None
prev_time    = time.time()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # run YOLO only every nth frame
    if frame_count % SKIP == 0:
        last_results = model.track(
            frame,
            persist=True,
            classes=VEHICLE_CLASSES,
            verbose=False,
            imgsz=640,
            device='cuda',# use gpu for speed 
            conf=0.5
        )

    results = last_results
    if results is None:
        continue

    # draw count line — LEFT ROAD ONLY
    cv2.line(frame, (LINE_START_X, line_y_red), (LINE_END_X, line_y_red), (0, 0, 255), 3)
    cv2.putText(frame, 'COUNT LINE', (LINE_START_X + 5, line_y_red - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    if results[0].boxes.data is not None and results[0].boxes.id is not None:

        boxes         = results[0].boxes.xyxy.cpu()
        track_ids     = results[0].boxes.id.int().cpu().tolist()
        class_indices = results[0].boxes.cls.int().cpu().tolist()
        confidences   = results[0].boxes.conf.cpu()

        for box, track_id, class_idx, conf in zip(boxes, track_ids, class_indices, confidences):
            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            class_name = class_list[class_idx]
            color      = COLOR_MAP.get(class_name, (200, 200, 200))

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Center dot
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

            # Label
            label = f"ID:{track_id} {class_name} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            # Count only if crossing LEFT road line
            if (cy > line_y_red and
                track_id not in crossed_ids and
                LINE_START_X < cx < LINE_END_X):
                crossed_ids.add(track_id)
                class_counts[class_name] += 1
            

    # ── Dashboard (top left) ──
    total   = sum(class_counts.values())
    panel_h = 40 + len(class_counts) * 32 + 35
    cv2.rectangle(frame, (0, 0), (290, panel_h), (0, 0, 0), -1)

    y_offset = 35
    for class_name, count in class_counts.items():
        color = COLOR_MAP.get(class_name, (200, 200, 200))
        cv2.putText(frame, f"  {class_name}: {count}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
        y_offset += 32

    cv2.putText(frame, f"  TOTAL: {total}", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

    # ── Live FPS (top right) ──
    now       = time.time()
    fps_live  = 1.0 / (now - prev_time + 1e-9)
    prev_time = now
    cv2.putText(frame, f"FPS: {fps_live:.1f}", (frame_width - 140, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

    out.write(frame)
    cv2.imshow("YOLO Vehicle Tracking & Counting", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n⛔ Stopped by user.")
        break

# ── cleanup ──
cap.release()
out.release()
cv2.destroyAllWindows()

print(f"\n✅ Done! {frame_count} frames processed.")
print("📊 Final Vehicle Counts (crossed left road line):")
for class_name, count in class_counts.items():
    print(f"   {class_name}: {count}")
print(f"   TOTAL: {sum(class_counts.values())}")
print("📁 Output saved: output_tracked.avi")