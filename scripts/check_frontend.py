import paramiko

def check_frontend():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    print("=== Nginx Configuration ===")
    stdin, stdout, stderr = ssh.exec_command("ls /etc/nginx/sites-enabled/")
    sites = stdout.read().decode().strip().split()
    for site in sites:
        print(f"\n--- Site: {site} ---")
        stdin, stdout, stderr = ssh.exec_command(f"sudo cat /etc/nginx/sites-enabled/{site}", get_pty=True)
        stdin.write(password + "\n")
        stdin.flush()
        print(stdout.read().decode())

    print("\n=== Web Server Status ===")
    stdin, stdout, stderr = ssh.exec_command("sudo systemctl status nginx", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    print(stdout.read().decode())

    print("\n=== Local API Connectivity ===")
    stdin, stdout, stderr = ssh.exec_command("curl -I http://localhost:8000/health")
    print(stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    check_frontend()
