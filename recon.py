import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

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
        
    print("\nRunning reconnaissance commands...")
    commands = [
        "ls -la /home/demo1_havano_pro_cpsmddqqvbceafpdpqoknnae",
        "cat /home/demo1_havano_pro_cpsmddqqvbceafpdpqoknnae/docker-compose.yml || echo 'No docker-compose.yml'",
        "ls -la /etc/nginx/sites-enabled/ || echo 'No nginx'",
        "docker inspect odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae | grep -i env -A 20"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(2)
        
    wait_for_prompt(channel, timeout=5)
    
    channel.send("exit\n")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
