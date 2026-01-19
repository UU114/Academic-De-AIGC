import paramiko
import sys
import os
import time

def deploy_docker():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    staging_base = "/tmp/academicguard_docker"
    final_base = "/var/www/academicguard/docker-deploy"
    
    print(f">>> Connecting to {server_ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    # 1. Install Docker and Host PostgreSQL
    print(">>> Installing Docker, Docker Compose, and Host PostgreSQL...")
    install_cmd = f"""
    echo '{password}' | sudo -S apt-get update
    echo '{password}' | sudo -S apt-get install -y docker.io docker-compose postgresql postgresql-contrib
    echo '{password}' | sudo -S systemctl enable docker
    echo '{password}' | sudo -S systemctl start docker
    """
    ssh.exec_command(install_cmd)
    time.sleep(2)
    
    # 2. Stop old supervisor service
    print(">>> Stopping legacy supervisor service...")
    ssh.exec_command(f"echo '{password}' | sudo -S supervisorctl stop academicguard-api || true")
    
    # 3. Upload files to staging
    print(">>> Uploading files to staging...")
    ssh.exec_command(f"rm -rf {staging_base} && mkdir -p {staging_base}")
    
    def upload_recursive(sftp, local, remote):
        if os.path.isfile(local):
            sftp.put(local, remote)
        else:
            try: sftp.mkdir(remote)
            except: pass
            for item in os.listdir(local):
                if item in ['.git', 'node_modules', 'venv', '__pycache__', 'dist', 'gemini-test-2026-01-12-19-45-00']: continue
                if item.startswith('test-2026'): continue
                upload_recursive(sftp, os.path.join(local, item), remote + "/" + item)

    with ssh.open_sftp() as sftp:
        for item in ['src', 'data', 'alembic', 'requirements.txt', 'alembic.ini', 'docker-compose.yml', 'Dockerfile', '.env.example']:
            if os.path.exists(item):
                print(f"Uploading {item}...")
                upload_recursive(sftp, item, staging_base + "/" + item)
        
        if os.path.exists('frontend/dist'):
            print("Uploading frontend/dist...")
            upload_recursive(sftp, 'frontend/dist', staging_base + "/dist")

    # 4. Move to final location and start
    print(">>> Moving to final location and starting Docker containers...")
    setup_cmd = f"""
    echo '{password}' | sudo -S mkdir -p {final_base}
    echo '{password}' | sudo -S rm -rf {final_base}/*
    echo '{password}' | sudo -S cp -r {staging_base}/* {final_base}/
    cd {final_base}
    if sudo docker compose version >/dev/null 2>&1; then
        DOCKER_CMD="sudo docker compose"
    else
        DOCKER_CMD="sudo docker-compose"
    fi
    echo '{password}' | $DOCKER_CMD up --build -d
    """
    stdin, stdout, stderr = ssh.exec_command(setup_cmd, get_pty=True)
    
    # Wait and stream output
    while True:
        if stdout.channel.recv_ready():
            output = stdout.channel.recv(1024).decode('utf-8', 'ignore')
            print(output, end="")
        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)
    
    # Run migrations inside container
    print("\n>>> Running database migrations inside container...")
    migration_cmd = f"""
    cd {final_base}
    if sudo docker compose version >/dev/null 2>&1; then
        DOCKER_CMD="sudo docker compose"
    else
        DOCKER_CMD="sudo docker-compose"
    fi
    echo '{password}' | $DOCKER_CMD exec -T api alembic upgrade head
    """
    ssh.exec_command(migration_cmd)
    
    # 5. Update Nginx to point to Docker
    print("\n>>> Updating Nginx configuration...")
    nginx_update = f"""
    echo '{password}' | sudo -S sed -i 's|root /var/www/academicguard/dist;|root {final_base}/dist;|' /etc/nginx/sites-available/academicguard
    echo '{password}' | sudo -S systemctl restart nginx
    """
    ssh.exec_command(nginx_update)
    
    print("=== Docker Deployment Complete ===")
    ssh.close()

if __name__ == "__main__":
    deploy_docker()