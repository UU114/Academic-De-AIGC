import paramiko

def check_logs():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    print("=== Nginx Access Logs (Last 20) ===")
    stdin, stdout, stderr = ssh.exec_command("sudo tail -n 20 /var/log/nginx/access.log", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    print(stdout.read().decode())

    print("\n=== Nginx Error Logs (Last 20) ===")
    stdin, stdout, stderr = ssh.exec_command("sudo tail -n 20 /var/log/nginx/error.log", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    print(stdout.read().decode())
    
    print("\n=== All Enabled Nginx Sites ===")
    stdin, stdout, stderr = ssh.exec_command("ls -l /etc/nginx/sites-enabled/")
    print(stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    check_logs()
