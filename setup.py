"""import os
import subprocess
import sys
import venv
import shutil

def find_python_executable(version="3.10"):
    # Try to find the Python executable for the specified version
    possible_names = [f"python{version}", f"python{version.replace('.', '')}", "python"]
    for name in possible_names:
        path = shutil.which(name)
        if path:
            return path
    raise EnvironmentError(f"Python {version} executable not found.")

def create_virtual_environment(env_name="venv", python_executable=None):
    if python_executable is None:
        python_executable = find_python_executable()
    print(f"Creating virtual environment: {env_name} using {python_executable}")
    venv.create(env_name, with_pip=True)
    activate_script = os.path.join(env_name, "Scripts", "activate") if os.name == 'nt' else os.path.join(env_name, "bin", "activate")
    return activate_script

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in process.stdout:
        print(line.decode().strip())
    for line in process.stderr:
        print(line.decode().strip())
    process.wait()
    return process.returncode

def install_requirements(activate_script):
    print("Installing general dependencies from requirements.txt...")
    command = f"{activate_script} && pip install -r backend/requirements.txt"
    if run_command(command) != 0:
        print("Failed to install general dependencies.")
        sys.exit(1)

def install_pytorch_with_cuda(activate_script):
    print("Installing base version of PyTorch to check for CUDA availability...")
    command = f"{activate_script} && pip install torch"
    if run_command(command) != 0:
        print("Failed to install base version of PyTorch.")
        sys.exit(1)

    command = f"{activate_script} && python -c 'import torch; print(torch.cuda.is_available())'"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    cuda_available = result.stdout.strip() == 'True'

    if cuda_available:
        print("CUDA is available. Installing PyTorch with CUDA support...")
        command = f"{activate_script} && pip install torch==2.2.2+cu121 torchvision==0.17.2+cu121 torchaudio==2.2.2+cu121 -f https://download.pytorch.org/whl/torch_stable.html"
    else:
        print("CUDA is not available. Installing CPU-only version of PyTorch...")
        command = f"{activate_script} && pip install torch torchvision torchaudio"

    if run_command(command) != 0:
        print("Failed to install the appropriate version of PyTorch.")
        sys.exit(1)

if __name__ == "__main__":
    env_name = "venv"
    if len(sys.argv) > 1:
        python_executable = sys.argv[1]
    else:
        try:
            python_executable = find_python_executable("3.10")
        except EnvironmentError as e:
            print(e)
            sys.exit(1)
    activate_script = create_virtual_environment(env_name, python_executable)
    install_requirements(activate_script)
    install_pytorch_with_cuda(activate_script)"""
    
import os
import subprocess
import sys
import venv

def create_virtual_environment(env_name="venv"):
    print(f"Creating virtual environment: {env_name}")
    venv.create(env_name, with_pip=True)
    activate_script = os.path.join(env_name, "Scripts", "activate") if os.name == 'nt' else os.path.join(env_name, "bin", "activate")
    return activate_script

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in process.stdout:
        print(line.decode().strip())
    for line in process.stderr:
        print(line.decode().strip())
    process.wait()
    return process.returncode

def install_requirements(activate_script):
    print("Installing general dependencies from requirements.txt...")
    command = f"{activate_script} && pip install -r requirements.txt"
    if run_command(command) != 0:
        print("Failed to install general dependencies.")
        sys.exit(1)

def install_pytorch_with_cuda(activate_script):
    print("Checking for CUDA availability...")
    command = f"{activate_script} && pip install torch==2.2.2+cu121 torchvision==0.17.2+cu121 torchaudio==2.2.2+cu121 -f https://download.pytorch.org/whl/torch_stable.html"
    if run_command(command) != 0:
        print("Failed to install PyTorch with CUDA support.")
        sys.exit(1)

if __name__ == "__main__":
    env_name = "venv"
    activate_script = create_virtual_environment(env_name)
    install_requirements(activate_script)
    install_pytorch_with_cuda(activate_script)

