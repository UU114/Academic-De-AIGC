import paramiko
import sys
import os

def run_debug_test():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    remote_test_path = "/tmp/remote_debug_test.py"
    local_test_path = "scripts/remote_debug_test.py"
    
    print(f">>> Connecting to {server_ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server_ip, username=username, password=password)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    print(">>> Uploading debug script...")
    with ssh.open_sftp() as sftp:
        sftp.put(local_test_path, remote_test_path)
            
    print(">>> Executing debug script on server...")
    test_cmd = f"export PYTHONPATH=/var/www/academicguard/api && /var/www/academicguard/api/venv/bin/python3 {remote_test_path}"
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    print(f"--- STDOUT ---\n{result}")
    if error:
        print(f"--- STDERR ---\n{error}")
        
    ssh.close()

if __name__ == "__main__":
    run_debug_test()
