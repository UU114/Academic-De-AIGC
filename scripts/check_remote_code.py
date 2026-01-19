import paramiko
import sys

def check_remote_code():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    remote_path = "/var/www/academicguard/api/src/core/suggester/llm_track.py"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    stdin, stdout, stderr = ssh.exec_command(f"grep -n 'dashscope' {remote_path}")
    print(f"Grep result for 'dashscope' in {remote_path}:")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command(f"cat {remote_path} | grep -A 20 'generate_suggestion'")
    print("generate_suggestion code block:")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    check_remote_code()
