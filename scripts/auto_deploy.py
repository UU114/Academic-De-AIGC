import os
import sys
import time
try:
    import paramiko
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def upload_files(sftp, local_path, remote_path):
    """Recursively upload files"""
    if os.path.isfile(local_path):
        try:
            # Check if remote file exists and size is different?
            # For simplicity, just overwrite.
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
            if item.startswith('.') and item != '.env.example': # Skip hidden files except .env.example
                continue
            if item == '__pycache__' or item == 'node_modules' or item == 'venv':
                continue
            if item.endswith('.pyc') or item.endswith('.pyo'):
                continue
                
            upload_files(sftp, os.path.join(local_path, item), remote_path + "/" + item)

def main():
    print("=== Auto Deployment ===")
    
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    print(f">>> Connecting to {server_ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server_ip, username=username, password=password)
        sftp = ssh.open_sftp()
        print("Connected successfully.")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
        
    # 4. Prepare Remote Directory
    remote_base = "/tmp/academicguard_deploy"
    print(f">>> Preparing remote directory {remote_base}...")
    # Clean up previous deploy files to ensure fresh start
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
            remote_item_path = remote_base + "/" + os.path.basename(item)
            upload_files(sftp, item, remote_item_path)
    
    # Make setup script executable
    ssh.exec_command(f"chmod +x {remote_base}/deploy_assets/setup_remote.sh")
    
    # 6. Execute Setup Script
    print(">>> Executing remote setup script (this may take a while)...")
    # Note: Using sudo might be needed if user deaigc doesn't have permissions, 
    # but the script assumes passwordless sudo or root logic?
    # The original script assumes user can run apt/systemctl. 
    # 'deaigc' user might need sudo. 
    # We will try running it. If it fails due to permission, we might need to handle sudo password.
    # The setup_remote.sh does NOT use sudo explicitly, so it assumes running as root OR user has rights.
    # But usually restarting services requires sudo.
    # Let's check setup_remote.sh content again.
    # It has `apt-get install`, `systemctl enable`. These need root.
    # If logged in as 'deaigc', we probably need sudo.
    
    # I will modify the command to use sudo -S and pass password via stdin if needed?
    # Or just run it and see.
    
    # Actually, let's look at setup_remote.sh again.
    # "if [ -f /etc/debian_version ]; then apt-get update ..."
    # This will fail if not root.
    
    # I'll prepend sudo to the execution command and provide password via stdin.
    command = f"cd {remote_base} && echo '{password}' | sudo -S ./deploy_assets/setup_remote.sh"
    
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    
    # Stream output
    while True:
        if stdout.channel.recv_ready():
            output = stdout.channel.recv(1024).decode('utf-8', 'ignore')
            sys.stdout.write(output)
            sys.stdout.flush()
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)
        
    err = stderr.read().decode()
    if err:
        print(f"Stderr:\n{err}")
        
    exit_status = stdout.channel.recv_exit_status()
    print(f"Exit status: {exit_status}")
    
    sftp.close()
    ssh.close()
    
    if exit_status == 0:
        print("=== Deployment Finished Successfully ===")
    else:
        print("=== Deployment Failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
