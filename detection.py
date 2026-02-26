import cv2
import numpy as np
from ultralytics import YOLO

# Load the best fine-tuned YOLOv8 model (path relative to detection.py)
best_model = YOLO('models/best.pt')

# Define the threshold for considering traffic as heavy
heavy_traffic_threshold = 10

# Define the vertices for the quadrilaterals (left & right lane regions)
vertices1 = np.array([(465, 350), (609, 350), (510, 630), (2, 630)], dtype=np.int32)
vertices2 = np.array([(678, 350), (815, 350), (1203, 630), (743, 630)], dtype=np.int32)

# Define the vertical range for the detection slice
x1, x2 = 325, 635
lane_threshold = 609

# Text annotation positions
text_position_left_lane      = (10,  50)
text_position_right_lane     = (820, 50)
intensity_position_left_lane = (10,  100)
intensity_position_right_lane= (820, 100)

# Font settings
font             = cv2.FONT_HERSHEY_SIMPLEX
font_scale       = 1
font_color       = (255, 255, 255)   # White
background_color = (0, 0, 255)       # Red

# ✅ FIXED VIDEO PATH — matches your folder structure exactly
video_path = 'sample_video/120678-721759752_medium.mp4'
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"❌ ERROR: Could not open video at '{video_path}'")
    print("👉 Make sure you run this script from inside the TRAFIC/ folder")
    exit()

# Get video properties
frame_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps          = cap.get(cv2.CAP_PROP_FPS) or 20.0

# ✅ FIXED OUTPUT PATH — saves next to detection.py
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('processed_sample_video.avi', fourcc, fps, (frame_width, frame_height))

print(f"✅ Video opened: {frame_width}x{frame_height} @ {fps:.1f} FPS")
print("⏳ Processing... Press 'Q' to quit.\n")

frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # ── Detection on sliced region only (ignores top & bottom noise) ──
    detection_frame = frame.copy()
    detection_frame[:x1, :]  = 0   # black out above detection zone
    detection_frame[x2:, :]  = 0   # black out below detection zone

    # Run YOLOv8 inference
    results = best_model.predict(detection_frame, imgsz=640, conf=0.4, verbose=False)
    processed_frame = results[0].plot(line_width=1)

    # Restore original top and bottom regions (unblackened)
    processed_frame[:x1, :] = frame[:x1, :].copy()
    processed_frame[x2:, :]  = frame[x2:, :].copy()

    # Draw lane boundary polygons
    cv2.polylines(processed_frame, [vertices1], isClosed=True, color=(0, 255, 0), thickness=2)  # Green = Left
    cv2.polylines(processed_frame, [vertices2], isClosed=True, color=(255, 0, 0), thickness=2)  # Blue  = Right

    # ── Count vehicles per lane ──
    bounding_boxes = results[0].boxes
    vehicles_in_left_lane  = 0
    vehicles_in_right_lane = 0

    for box in bounding_boxes.xyxy:
        if box[0] < lane_threshold:
            vehicles_in_left_lane += 1
        else:
            vehicles_in_right_lane += 1

    # Traffic intensity
    traffic_intensity_left  = "🔴 Heavy" if vehicles_in_left_lane  > heavy_traffic_threshold else "🟢 Smooth"
    traffic_intensity_right = "🔴 Heavy" if vehicles_in_right_lane > heavy_traffic_threshold else "🟢 Smooth"

    # ── Overlay text: LEFT LANE ──
    cv2.rectangle(processed_frame,
                  (text_position_left_lane[0]-10, text_position_left_lane[1]-25),
                  (text_position_left_lane[0]+460, text_position_left_lane[1]+10),
                  background_color, -1)
    cv2.putText(processed_frame, f'Vehicles in Left Lane: {vehicles_in_left_lane}',
                text_position_left_lane, font, font_scale, font_color, 2, cv2.LINE_AA)

    cv2.rectangle(processed_frame,
                  (intensity_position_left_lane[0]-10, intensity_position_left_lane[1]-25),
                  (intensity_position_left_lane[0]+460, intensity_position_left_lane[1]+10),
                  background_color, -1)
    cv2.putText(processed_frame, f'Traffic: {traffic_intensity_left}',
                intensity_position_left_lane, font, font_scale, font_color, 2, cv2.LINE_AA)

    # ── Overlay text: RIGHT LANE ──
    cv2.rectangle(processed_frame,
                  (text_position_right_lane[0]-10, text_position_right_lane[1]-25),
                  (text_position_right_lane[0]+460, text_position_right_lane[1]+10),
                  background_color, -1)
    cv2.putText(processed_frame, f'Vehicles in Right Lane: {vehicles_in_right_lane}',
                text_position_right_lane, font, font_scale, font_color, 2, cv2.LINE_AA)

    cv2.rectangle(processed_frame,
                  (intensity_position_right_lane[0]-10, intensity_position_right_lane[1]-25),
                  (intensity_position_right_lane[0]+460, intensity_position_right_lane[1]+10),
                  background_color, -1)
    cv2.putText(processed_frame, f'Traffic: {traffic_intensity_right}',
                intensity_position_right_lane, font, font_scale, font_color, 2, cv2.LINE_AA)

    # ── Frame counter (top center) ──
    cv2.putText(processed_frame, f'Frame: {frame_count}',
                (frame_width//2 - 80, 40), font, 0.8, (0, 255, 255), 2, cv2.LINE_AA)

    # Write and show frame
    out.write(processed_frame)
    cv2.imshow('Real-time Traffic Analysis', processed_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n⛔ Stopped by user.")
        break

# ── Cleanup ──
cap.release()
out.release()
cv2.destroyAllWindows()
print(f"\n✅ Done! Processed {frame_count} frames.")
print("📁 Output saved as: processed_sample_video.avi")