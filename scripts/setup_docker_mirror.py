import paramiko
import sys

def setup_docker_mirror():
    server_ip = "82.156.7.13"
    username = "deaigc"
    password = "Dq3h8*69."
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=username, password=password)
    
    mirror_config = """{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://mirror.baidubce.com",
    "https://dockerproxy.com",
    "https://docker.udayun.com",
    "https://docker.anyhub.us.kg"
  ]
}"""
    
    # Use a safe way to write the file
    print(">>> Configuring Docker registry mirrors...")
    ssh.exec_command(f"echo '{mirror_config}' > /tmp/daemon.json")
    ssh.exec_command(f"echo '{password}' | sudo -S cp /tmp/daemon.json /etc/docker/daemon.json")
    ssh.exec_command(f"echo '{password}' | sudo -S systemctl restart docker")
    
    print(">>> Docker restarted with mirrors.")
    ssh.close()

if __name__ == "__main__":
    setup_docker_mirror()
