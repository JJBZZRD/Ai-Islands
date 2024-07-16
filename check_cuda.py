import torch
import platform
import psutil
import GPUtil

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

def check_system_info():
    print(f"System: {platform.system()}")
    print(f"Node Name: {platform.node()}")
    print(f"Release: {platform.release()}")
    print(f"Version: {platform.version()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"CPU Count: {psutil.cpu_count(logical=True)}")
    print(f"Total RAM: {psutil.virtual_memory().total / (1024 ** 3):.2f} GB")
    
    # Add current memory usage
    current_memory = psutil.virtual_memory()
    print(f"Current Memory Usage: {current_memory.percent}%")
    print(f"Used Memory: {current_memory.used / (1024 ** 3):.2f} GB")
    print(f"Available Memory: {current_memory.available / (1024 ** 3):.2f} GB")
    
    gpus = GPUtil.getGPUs()
    if gpus:
        for gpu in gpus:
            print(f"GPU {gpu.id}: {gpu.name}")
            print(f"  GPU Driver: {gpu.driver}")
            print(f"  GPU Memory Total: {gpu.memoryTotal:.2f} MB")
            print(f"  GPU Memory Free: {gpu.memoryFree:.2f} MB")
            print(f"  GPU Memory Used: {gpu.memoryUsed:.2f} MB")
            print(f"  GPU Load: {gpu.load * 100:.1f}%")
            print(f"  GPU Temperature: {gpu.temperature} °C")
    else:
        print("No GPU found or CUDA is not available.")

if __name__ == "__main__":
    check_system_info()
    check_cuda()
    
    