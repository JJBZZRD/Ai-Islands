import torch

def check_cuda():
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    if cuda_available:
        cuda_version = torch.version.cuda
        cudnn_version = torch.backends.cudnn.version()
        print(f"CUDA version: {cuda_version}")
        print(f"cuDNN version: {cudnn_version}")
    else:
        print("CUDA is not available. Please check your CUDA installation.")

if __name__ == "__main__":
    check_cuda()
