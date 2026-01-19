import paramiko

def fix_nginx():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    print("Getting API container info...")
    stdin, stdout, stderr = ssh.exec_command("sudo docker inspect academicguard-api", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    import json
    data = json.loads(stdout.read().decode().split('\n', 1)[1]) # Skip password prompt
    container_ip = data[0]['NetworkSettings']['Networks'][list(data[0]['NetworkSettings']['Networks'].keys())[0]]['IPAddress']
    print(f"Container IP: {container_ip}")

    # Use 172.17.0.1 or similar if 127.0.0.1 is failing
    new_proxy = f"http://{container_ip}:8000"
    print(f"Suggesting proxy_pass to: {new_proxy}")

    # Alternatively, use host.docker.internal equivalent or just the bridge gateway
    stdin, stdout, stderr = ssh.exec_command("ip addr show docker0 | grep -Po 'inet \\K[\\d.]+'")
    gateway_ip = stdout.read().decode().strip()
    print(f"Docker Gateway IP: {gateway_ip}")

    # Let's try to update nginx config to use gateway_ip:8000 which is mapped to the container
    config_path = "/etc/nginx/sites-available/academicguard"
    print(f"Updating {config_path}...")
    
    # Reading current config
    stdin, stdout, stderr = ssh.exec_command(f"sudo cat {config_path}", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    current_config = stdout.read().decode()
    
    # Replace 127.0.0.1:8000 with gateway_ip:8000
    new_config = current_config.replace("127.0.0.1:8000", f"{gateway_ip}:8000")
    
    # Write back
    temp_file = "/tmp/nginx_ag_fixed"
    sftp = ssh.open_sftp()
    with sftp.file(temp_file, 'w') as f:
        f.write(new_config)
    
    ssh.exec_command(f"sudo cp {temp_file} {config_path}", get_pty=True)
    ssh.exec_command("sudo nginx -t && sudo systemctl restart nginx", get_pty=True)
    print("Nginx configuration updated and restarted.")

    ssh.close()

if __name__ == "__main__":
    fix_nginx()
