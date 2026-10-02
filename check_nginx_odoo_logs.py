import paramiko
import time
import sys
from datetime import datetime

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

db_name = 'jlink_havano_pro_cpsmddqqvbceafpdpqoknnae'
container_name = f'odoo_{db_name}'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    channel = ssh.invoke_shell()
    
    def wait_for_prompt(chan, timeout=10):
        buffer = ""
        start_time = time.time()
        while True:
            if chan.recv_ready():
                data = chan.recv(4096).decode('utf-8', errors='replace')
                buffer += data
                sys.stdout.write(data)
                sys.stdout.flush()
                if "password for" in buffer.lower() or "#" in buffer or "$" in buffer:
                    return buffer
            if time.time() - start_time > timeout:
                return buffer
            time.sleep(0.5)

    wait_for_prompt(channel)
    channel.send("sudo -i\n")
    out = wait_for_prompt(channel)
    if "password for" in out.lower():
        channel.send(password + "\n")
        wait_for_prompt(channel)
        
    print("\nRunning check...")
    
    commands = [
        "echo '=== Docker Container Status ==='",
        f"docker ps | grep {db_name}",
        "echo '\\n=== Odoo Container Logs for Today (WhatsApp Webhook) ==='",
        f"docker logs --since 10h {container_name} 2>&1 | grep -i 'whatsapp\\|webhook'",
        "echo '\\n=== Nginx Access Logs for Today (Webhook) ==='",
        "grep 'whatsapp' /var/log/nginx/access.log | tail -n 10",
        "echo '\\n=== Nginx Error Logs ==='",
        "tail -n 10 /var/log/nginx/error.log"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(2)
        
    out = wait_for_prompt(channel, timeout=15)
    
    channel.send("exit\n")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
