import paramiko
import sys

def check_remote_status():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    print(f"Connecting to {server_ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server_ip, username=username, password=password)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    commands = [
        ("Remote Directory", "ls -R /var/www/academicguard"),
        ("Docker Compose Status", "cd /var/www/academicguard && sudo docker-compose ps"),
        ("Docker Compose Logs", "cd /var/www/academicguard && sudo docker-compose logs --tail 50"),
        ("Docker Containers (All)", "sudo docker ps -a")
    ]

    for title, cmd in commands:
        print(f"\n=== {title} ===")
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        stdin.write(password + "\n")
        stdin.flush()
        out = stdout.read().decode()
        # Remove the first line if it's the password prompt
        lines = out.splitlines()
        if lines and "password for" in lines[0]:
            out = "\n".join(lines[1:])
        print(out.strip())

    # Try to check if API is responding locally on the server
    print("\n=== API Local Response Check ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/")
    http_code = stdout.read().decode().strip()
    print(f"HTTP Code from localhost:8000: {http_code}")

    ssh.close()

if __name__ == "__main__":
    check_remote_status()
