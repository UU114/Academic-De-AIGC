import paramiko
import sys
import os

def update_remote_env():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    env_path = "/var/www/academicguard/api/.env"
    temp_remote_env = "/tmp/.env.tmp"
    temp_remote_test = "/tmp/test_llm_call.py"
    
    print(f">>> Connecting to {server_ip}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server_ip, username=username, password=password)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    print(">>> Updating remote .env...")
    # Using dashscope specific config as requested
    new_config_dict = {
        "LLM_PROVIDER": "dashscope",
        "LLM_MODEL": "qwen-plus-2025-12-01",
        "DASHSCOPE_API_KEY": "sk-4dac6cf7f81a447981bd28f843e2103d",
        "DASHSCOPE_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "DASHSCOPE_MODEL": "qwen-plus-2025-12-01"
    }
    
    # Read current .env
    stdin, stdout, stderr = ssh.exec_command(f"sudo cat {env_path}", get_pty=True)
    stdin.write(password + "\n")
    stdin.flush()
    content = stdout.read().decode()
    if "[sudo] password" in content:
        content = content.split("\n", 1)[1] if "\n" in content else ""
    
    lines = content.splitlines()
    new_lines = []
    found_keys = set()
    for line in lines:
        if "=" in line and not line.startswith("#"):
            k = line.split("=", 1)[0].strip()
            if k in new_config_dict:
                new_lines.append(f"{k}={new_config_dict[k]}")
                found_keys.add(k)
                continue
        new_lines.append(line)
    
    for k, v in new_config_dict.items():
        if k not in found_keys:
            new_lines.append(f"{k}={v}")
            
    with ssh.open_sftp() as sftp:
        with sftp.file(temp_remote_env, 'w') as f:
            f.write("\n".join(new_lines))
            
    ssh.exec_command(f"echo '{password}' | sudo -S cp {temp_remote_env} {env_path}")
    print(">>> Restarting service...")
    ssh.exec_command(f"echo '{password}' | sudo -S supervisorctl restart academicguard-api")
    
    # Updated test script with correct signature
    test_script_content = """
import asyncio
import os
import sys

# Add app to path
sys.path.append('/var/www/academicguard/api')

from src.core.suggester.llm_track import LLMTrack

async def test():
    print("Initializing LLMTrack...")
    track = LLMTrack(colloquialism_level=4)
    sentence = "The results are very important for the study."
    print(f"Testing with sentence: {sentence}")
    try:
        # Signature: sentence, issues, locked_terms
        res = await track.generate_suggestion(sentence, [], [])
        if res:
            print(f"SUCCESS! Rewritten: {res.rewritten}")
        else:
            print("FAILED: Received None from generate_suggestion")
    except Exception as e:
        print(f"FAILED with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
"""
    with ssh.open_sftp() as sftp:
        with sftp.file(temp_remote_test, 'w') as f:
            f.write(test_script_content)
            
    print(">>> Executing test script on server...")
    test_cmd = f"export PYTHONPATH=/var/www/academicguard/api && /var/www/academicguard/api/venv/bin/python3 {temp_remote_test}"
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    
    result = stdout.read().decode()
    error = stderr.read().decode()
    
    print(f"--- STDOUT ---\n{result}")
    if error:
        print(f"--- STDERR ---\n{error}")
        
    if "SUCCESS!" in result:
        print("\nVerified: LLM call working on server!")
    else:
        print("\nVerification FAILED.")

    ssh.close()

if __name__ == "__main__":
    update_remote_env()