import os
import sys
import subprocess
import shutil
import getpass
try:
    import paramiko
except ImportError:
    print("Installing paramiko for SSH connections...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def run_local_command(command, cwd=None, shell=True):
    print(f"Running local: {command}")
    try:
        subprocess.check_call(command, cwd=cwd, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        sys.exit(1)

def build_frontend():
    print(">>> Building Frontend...")
    frontend_dir = os.path.join(os.getcwd(), 'frontend')
    if not os.path.exists(frontend_dir):
        print("Frontend directory not found!")
        sys.exit(1)
    
    # Check if node_modules exists
    if not os.path.exists(os.path.join(frontend_dir, 'node_modules')):
        print("Installing frontend dependencies...")
        run_local_command('npm install', cwd=frontend_dir)
        
    run_local_command('npm run build', cwd=frontend_dir)
    print("Frontend build complete.")

def upload_files(sftp, local_path, remote_path):
    """Recursively upload files"""
    if os.path.isfile(local_path):
        try:
            sftp.put(local_path, remote_path)
            print(f"Uploaded: {local_path} -> {remote_path}")
        except Exception as e:
            print(f"Failed to upload {local_path}: {e}")
    else:
        try:
            sftp.mkdir(remote_path)
            print(f"Created remote dir: {remote_path}")
        except IOError:
            pass # Directory might exist
        
        for item in os.listdir(local_path):
            if item.startswith('.') or item == '__pycache__' or item == 'node_modules' or item == 'venv':
                continue
            upload_files(sftp, os.path.join(local_path, item), remote_path + "/" + item)

def main():
    print("=== AcademicGuard Deployment Tool ===")
    
    # 1. Gather Info
    server_ip = input("Server IP: ").strip()
    username = input("Username (root recommended): ").strip()
    password = getpass.getpass("Password: ")
    
    # 2. Build Frontend
    if input("Build frontend? (y/n) [y]: ").lower() != 'n':
        build_frontend()
    
    # 3. Connect to Server
    print(f">>> Connecting to {server_ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server_ip, username=username, password=password)
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
        
    # 4. Prepare Remote Directory
    remote_base = "/tmp/academicguard_deploy"
    print(f">>> preparing remote directory {remote_base}...")
    ssh.exec_command(f"rm -rf {remote_base}")
    ssh.exec_command(f"mkdir -p {remote_base}")
    
    # 5. Upload Files
    print(">>> Uploading files...")
    # Upload manifest
    files_to_upload = [
        'src',
        'data',
        'alembic',
        'requirements.txt',
        'alembic.ini',
        '.env.example',
        'deploy_assets'
    ]
    
    # Check if frontend/dist exists
    if os.path.exists(os.path.join('frontend', 'dist')):
        files_to_upload.append(os.path.join('frontend', 'dist'))
    else:
        print("Warning: frontend/dist not found!")
    
    for item in files_to_upload:
        if os.path.exists(item):
            # Handle path correctly for upload_files recursion
            remote_item_path = remote_base + "/" + os.path.basename(item)
            upload_files(sftp, item, remote_item_path)
    
    # Make setup script executable
    ssh.exec_command(f"chmod +x {remote_base}/deploy_assets/setup_remote.sh")
    
    # 6. Execute Setup Script
    print(">>> Executing remote setup script (this may take a while)...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {remote_base} && ./deploy_assets/setup_remote.sh")
    
    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.strip())
        
    err = stderr.read().decode()
    if err:
        print(f"Errors:\n{err}")
        
    sftp.close()
    ssh.close()
    print("=== Deployment Finished ===")

if __name__ == "__main__":
    main()
