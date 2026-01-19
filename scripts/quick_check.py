import paramiko

def quick_check():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server_ip, username=username, password=password)
        
        print("Checking /var/www content...")
        stdin, stdout, stderr = ssh.exec_command("ls -la /var/www")
        print(stdout.read().decode())

        print("Checking /var/www/academicguard content...")
        stdin, stdout, stderr = ssh.exec_command("ls -la /var/www/academicguard")
        print(stdout.read().decode())

        # Try to find where docker-compose.yml is
        print("Finding docker-compose.yml...")
        stdin, stdout, stderr = ssh.exec_command("find /var/www -name 'docker-compose.yml'")
        compose_path = stdout.read().decode().strip()
        print(f"Found at: {compose_path}")

        if compose_path:
            work_dir = compose_path.replace("/docker-compose.yml", "")
            cmd = f"cd {work_dir} && sudo docker compose up -d"
            print(f"Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
            stdin.write(password + "\n")
            stdin.flush()
            print(stdout.read().decode())
            
            # Check who is using port 6379
            print("\n--- Port 6379 occupation ---")
            stdin, stdout, stderr = ssh.exec_command("sudo netstat -tulpn | grep :6379", get_pty=True)
            stdin.write(password + "\n")
            stdin.flush()
            print(stdout.read().decode())

            # Check api logs
            print("\n--- API Logs ---")
            stdin, stdout, stderr = ssh.exec_command(f"cd {work_dir} && sudo docker compose logs --tail 20 api", get_pty=True)
            stdin.write(password + "\n")
            stdin.flush()
            print(stdout.read().decode())

        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    quick_check()