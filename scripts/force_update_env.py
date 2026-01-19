import paramiko
import sys

def force_update_env():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    env_path = "/var/www/academicguard/api/.env"
    temp_path = "/tmp/.env.final"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    # Define EXACT content for .env
    env_content = f"""
APP_NAME=AcademicGuard
DEBUG=false
SYSTEM_MODE=debug

LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus-2025-12-01

DASHSCOPE_API_KEY=sk-4dac6cf7f81a447981bd28f843e2103d
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-plus-2025-12-01

JWT_SECRET_KEY=auF1ZkhWg8b6m_SiJjcaMdIyb1390Z1xLhWIzR1NiCM
ADMIN_SECRET_KEY=your_admin_secret_key_here
INTERNAL_SERVICE_SECRET=gpW1h0nud5boEbu1u6uX0kyGfuV_lPMgzyTTuzBVCV0

DATABASE_URL=sqlite+aiosqlite:///{env_path.replace('.env', 'academicguard.db')}

DEFAULT_COLLOQUIALISM_LEVEL=4
DEFAULT_TARGET_LANG=en
SEMANTIC_SIMILARITY_THRESHOLD=0.80
"""
    
    with ssh.open_sftp() as sftp:
        with sftp.file(temp_path, 'w') as f:
            f.write(env_content.strip())
            
    ssh.exec_command(f"echo '{password}' | sudo -S cp {temp_path} {env_path}")
    ssh.exec_command(f"echo '{password}' | sudo -S supervisorctl restart academicguard-api")
    print("Remote .env forced update and service restarted.")
    ssh.close()

if __name__ == "__main__":
    force_update_env()
