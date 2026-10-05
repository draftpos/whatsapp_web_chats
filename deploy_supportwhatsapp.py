import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

db_name = 'supportwhatsapp_s4_havano_pro_yvnmgevazsj'
container_name = f'odoo_{db_name}'
dir_path = f'/home/{db_name}/custom-addons/whatsapp_web_chats'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    channel = ssh.invoke_shell()

    def wait_for_prompt(chan, timeout=20):
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

    print("\n=== Pulling latest code from git ===")
    channel.send(f"cd {dir_path} && git fetch --all && git reset --hard origin/dev\n")
    time.sleep(10)
    wait_for_prompt(channel, timeout=15)

    print("\n=== Updating Odoo Module ===")
    channel.send(f"docker exec {container_name} odoo -c /etc/odoo/odoo.conf -d {db_name} -u whatsapp_web_chats --stop-after-init --no-http\n")
    time.sleep(30)
    wait_for_prompt(channel, timeout=120)

    print("\n=== Restarting container ===")
    channel.send(f"docker restart {container_name}\n")
    time.sleep(20)
    wait_for_prompt(channel, timeout=25)

    channel.send("exit\n")
    print("\nDone!")

except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
