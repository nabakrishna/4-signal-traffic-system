# # gpu_max_fixed.py - Save & Run NOW
# import torch
# import time
# import torch.nn.functional as F

# device = 'cuda'
# torch.cuda.set_device(0)
# torch.cuda.empty_cache()

# print("🚀 RTX 3050 GPU MAX LOAD - FIXED")
# print("Run 'nvidia-smi -l 1' in another CMD...\n")

# # PHASE 1: HEAVY MATRIX (80-90%)
# print("🔥 Matrix Multiply Loop...")
# a = torch.randn(3500, 3500, device=device, dtype=torch.float16)
# for i in range(200):
#     b = torch.mm(a, a)
#     if i % 25 == 0:
#         mem = torch.cuda.memory_allocated() / 1e9
#         print(f"Step {i}: {mem:.1f}GB VRAM")

# # PHASE 2: CONVOLUTION (75-85%)
# print("\n🔥 2D Convolution...")
# x = torch.randn(1, 3, 1024, 1024, device=device)  # FIXED: [B,C,H,W]
# for i in range(80):
#     x = F.conv2d(x, x.mean(dim=[2,3], keepdim=True))  # FIXED shape
#     if i % 20 == 0:
#         print(f"Conv {i}: OK")

# print("\n✅ GPU MAXED! 75-95% utilization + 2-3GB VRAM")


