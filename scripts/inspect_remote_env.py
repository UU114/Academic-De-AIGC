import paramiko
import sys

def inspect_remote():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    print(">>> Locating .env files...")
    stdin, stdout, stderr = ssh.exec_command("find /var/www/academicguard -name '.env'")
    files = stdout.read().decode().splitlines()
    for f in files:
        print(f"\n--- Content of {f} ---")
        stdin, stdout, stderr = ssh.exec_command(f"sudo cat {f}", get_pty=True)
        stdin.write(password + "\n")
        stdin.flush()
        print(stdout.read().decode())

    print("\n>>> Checking running process environment...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep uvicorn")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == "__main__":
    inspect_remote()
