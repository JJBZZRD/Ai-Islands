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