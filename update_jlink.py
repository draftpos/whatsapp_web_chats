import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

db_name = 'jlink_havano_pro_cpsmddqqvbceafpdpqoknnae'
dir_path = f'/home/{db_name}/custom-addons/whatsapp_web_chats'
container_name = f'odoo_{db_name}'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    print("Connected successfully. Requesting sudo session...")
    
    channel = ssh.invoke_shell()
    
    def wait_for_prompt(chan, timeout=10):
        buffer = ""
        start_time = time.time()
        while True:
            if chan.recv_ready():
                data = chan.recv(4096).decode('utf-8')
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
        
    print("\nExecuting update commands...")
    commands = [
        f"cd {dir_path}",
        "git fetch --all",
        "git reset --hard origin/dev",
        f"docker exec {container_name} odoo -c /etc/odoo/odoo.conf -d {db_name} -u whatsapp_web_chats --stop-after-init --no-http",
    ]
    
    for cmd in commands:
        print(f"\nRunning: {cmd}")
        channel.send(cmd + "\n")
        time.sleep(3)
        
    print("\nWaiting for docker update to finish (30 seconds)...")
    time.sleep(30)
    
    print(f"\nRestarting container {container_name}")
    channel.send(f"docker restart {container_name}\n")
    time.sleep(5)
    
    channel.send("exit\n")
    print("\nDone.")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
