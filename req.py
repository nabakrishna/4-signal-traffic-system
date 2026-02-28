# from ultralytics import YOLO

# # This will automatically download the yolo26l.pt file to your current directory
# model = YOLO("yolo26l.pt")


import torch
print(f"Is CUDA available? {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")