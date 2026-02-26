# ============================================================
# FOLDER STRUCTURE
# TRAFIC/
# ├── images/
# ├── models/
# │   ├── best.onnx
# │   └── best.pt          ← pretrained model
# ├── sample_video/
# │   └── 120678-721759752_medium.mp4  ← your video
  ├──  detection.py       ← detection code
# └── main.py             ← THIS FILE (run from here)
# ============================================================


till now i am using yolo11l , that is the large model of yolo11 but now for this the latest model of ultralytics will be much better that is yolo26l or yolo26x  , also for run this smoothly in real time we should implemnt gpu 

## This system uses real-time YOLO-based vehicle detection to intelligently control four traffic signals at an intersection. It detects and counts vehicles, classifies traffic as low, medium, or heavy, and automatically adjusts green light timing based on actual road conditions rather than fixed timers. The fourth signal acts as a dedicated emergency alert light — when an ambulance is detected, it flashes a visible warning so nearby drivers give way without disrupting the rest of the traffic flow. As the ambulance moves through the city, the system predicts its path at every junction — if multiple roads are possible all are put on standby alert, if only one road ahead it gets a direct notification — creating a cascading alert chain that follows the ambulance automatically until it reaches its destination. Additionally the system learns from one week of traffic data combined with external factors like public holidays, weather conditions and local events to predict congestion up to 30 minutes in advance and pre-adjust signal timings before rush hour even begins. This makes the system fully proactive, turning a basic traffic light into a complete intelligent traffic management ecosystem.


## 1 addition: 
AMBULANCE DETECTED AT JUNCTION 1
              ↓
    How many roads ahead?
    ┌─────────────────────────────┐
    │ 3 roads → ALL 3 on ALERT   │
    │ 2 roads → BOTH on ALERT    │
    │ 1 road  → DIRECT NOTIFY ✅  │
    └─────────────────────────────┘
              ↓
    Ambulance enters ONE road (confirmed)
              ↓
    Cancel other alerts immediately
              ↓
    Check THAT road's next junction
    ┌─────────────────────────────┐
    │ 3 roads → ALL 3 on ALERT   │
    │ 2 roads → BOTH on ALERT    │
    │ 1 road  → DIRECT NOTIFY ✅  │
    └─────────────────────────────┘
              ↓
         Repeats automatically
         until ambulance stops

## 2 addition: 
AI Traffic Prediction — Based on 1 Week Data + External Factors() fesitival holiday

## arch look like ingen
CAMERA FEEDS
     ↓
YOLO DETECTION
     ↓
VEHICLE COUNT + TYPE + AMBULANCE
     ↓
     ├── 🚑 Emergency → Route prediction cascade
     │
     ├── 📊 Current count → Signal timing now
     │
     └── 🧠 AI Prediction → Signal timing next 30 mins
              ├── Time pattern (1 week data)
              ├── Holiday check
              ├── Weather API
              └── Special events



