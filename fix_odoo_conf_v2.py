import paramiko
import time

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

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
                data = chan.recv(4096).decode('utf-8')
                buffer += data
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
        
    commands = [
        "sed -i 's/demo1/jlink/g' /home/jlink_havano_pro_cpsmddqqvbceafpdpqoknnae/config/odoo.conf",
        "docker restart odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae",
        "cat /home/jlink_havano_pro_cpsmddqqvbceafpdpqoknnae/config/odoo.conf"
    ]
    
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(2)
        
    out = wait_for_prompt(channel, timeout=10)
    print("OUTPUT:")
    print(out)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
