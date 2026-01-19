import paramiko

def debug_frontend():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    print("=== 1. Checking Nginx Service Status ===")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active nginx")
    print(f"Nginx active: {stdout.read().decode().strip()}")

    print("\n=== 2. Checking Port 80 Listening ===")
    stdin, stdout, stderr = ssh.exec_command("sudo netstat -tulpn | grep :80", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    print(stdout.read().decode())

    print("\n=== 3. Checking Static Files Path ===")
    path = "/var/www/academicguard/docker-deploy/dist"
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {path}")
    print(f"Path: {path}")
    print(stdout.read().decode())

    print("\n=== 4. Testing Localhost:80 ===")
    stdin, stdout, stderr = ssh.exec_command("curl -I http://localhost/")
    print(stdout.read().decode())

    print("\n=== 5. Checking Firewall (ufw) ===")
    stdin, stdout, stderr = ssh.exec_command("sudo ufw status", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    print(stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    debug_frontend()
