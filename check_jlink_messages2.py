import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

db_name = 'jlink_havano_pro_cpsmddqqvbceafpdpqoknnae'
container_name = f'odoo_{db_name}'

odoo_code = """
import time
from datetime import datetime, timedelta

print('\\n=== Checking Recent Messages (Last 10) ===')
msgs = env['whatsapp.message'].search([], order='id desc', limit=10)
for m in msgs:
    print(f'Msg {m.id} | Date: {m.create_date} | State: {m.state} | Type: {m.message_type if hasattr(m, "message_type") else "N/A"}')

print('\\n=== Checking Today Messages ===')
today = datetime.now().date()
today_msgs = env['whatsapp.message'].search([('create_date', '>=', str(today))])
print(f'Total messages created today: {len(today_msgs)}')

print('\\n=== Checking Discuss Channels (Chats) ===')
channels = env['discuss.channel'].search([('channel_type', '=', 'whatsapp')], order='id desc', limit=5)
for c in channels:
    print(f'Channel {c.id} | Name: {c.name} | Last Message: {c.message_ids[0].date if c.message_ids else "None"}')

"""

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_msg_2.py', 'w') as f:
        f.write(odoo_code)
    sftp.close()
    
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
    
    cmd = f"docker exec -i {container_name} odoo shell -c /etc/odoo/odoo.conf -d {db_name} --no-http < /tmp/check_msg_2.py"
    channel.send(cmd + "\n")
    time.sleep(15)
    
    out = wait_for_prompt(channel, timeout=20)
    
    channel.send("exit\n")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
