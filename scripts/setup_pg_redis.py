import paramiko
import sys
import time

def setup_pg_and_redis():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    print(">>> Installing PostgreSQL and checking Redis...")
    # Install PG and ensure Redis is started
    cmd = f"echo '{password}' | sudo -S apt-get update && sudo -S apt-get install -y postgresql postgresql-contrib redis-server"
    ssh.exec_command(cmd)
    time.sleep(5)
    
    print(">>> Creating PostgreSQL database and user...")
    # Create user and db if not exists
    pg_cmds = [
        "sudo -u postgres psql -c \"CREATE USER academicguard WITH PASSWORD 'AG_Pass_2026';\"",
        "sudo -u postgres psql -c \"CREATE DATABASE academicguard OWNER academicguard;\"",
        "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE academicguard TO academicguard;\""
    ]
    for pg_cmd in pg_cmds:
        ssh.exec_command(f"echo '{password}' | sudo -S {pg_cmd}")
    
    print(">>> Updating .env configuration...")
    env_path = "/var/www/academicguard/api/.env"
    temp_path = "/tmp/.env.pg"
    
    # Define updated lines
    updates = {
        "DATABASE_URL": "postgresql+asyncpg://academicguard:AG_Pass_2026@localhost/academicguard",
        "REDIS_URL": "redis://localhost:6379/0"
    }
    
    # Read current env
    stdin, stdout, stderr = ssh.exec_command(f"sudo cat {env_path}", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    content = stdout.read().decode()
    if "[sudo] password" in content:
        content = content.split("\n", 1)[1] if "\n" in content else ""
        
    lines = content.splitlines()
    new_lines = []
    found = set()
    for line in lines:
        if "=" in line and not line.startswith("#"):
            k = line.split("=", 1)[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}")
                found.add(k)
                continue
        new_lines.append(line)
    
    for k, v in updates.items():
        if k not in found:
            new_lines.append(f"{k}={v}")
            
    with ssh.open_sftp() as sftp:
        with sftp.file(temp_path, 'w') as f:
            f.write("\n".join(new_lines))
            
    ssh.exec_command(f"echo '{password}' | sudo -S cp {temp_path} {env_path}")
    
    print(">>> Running migrations on PostgreSQL...")
    # Need to make sure asyncpg is installed in venv (it should be from requirements.txt)
    migrate_cmd = "cd /var/www/academicguard/api && export PYTHONPATH=. && ./venv/bin/alembic upgrade head"
    stdin, stdout, stderr = ssh.exec_command(migrate_cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    print(">>> Restarting service...")
    ssh.exec_command(f"echo '{password}' | sudo -S supervisorctl restart academicguard-api")
    
    print("=== PostgreSQL and Redis Setup Complete ===")
    ssh.close()

if __name__ == "__main__":
    setup_pg_and_redis()
