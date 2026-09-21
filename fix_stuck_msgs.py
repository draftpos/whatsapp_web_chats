import paramiko
import json

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
import json

msgs = env['whatsapp.message'].sudo().browse([7015, 7014, 7013])
for msg in msgs:
    if msg.free_text_json:
        try:
            data = json.loads(msg.free_text_json)
        except Exception:
            data = msg.free_text_json
        
        if isinstance(data, dict):
            # Fix empty values
            for k in ['free_text_1', 'free_text_2', 'free_text_3', 'free_text_4', 'free_text_5']:
                if not data.get(k):
                    data[k] = 'Unavailable'
            
            msg.write({
                'free_text_json': data,
                'state': 'outgoing',
                'failure_type': False,
                'failure_reason': False
            })
            print(f"Fixed msg {msg.id}: {data}")

# Trigger cron
env.ref('whatsapp.ir_cron_send_whatsapp_queue')._trigger()
print("Triggered cron.")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/fix_stuck_msgs.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/fix_stuck_msgs.py {CONTAINER}:/tmp/fix_stuck_msgs.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/fix_stuck_msgs.py | /usr/bin/odoo shell -d {DB} --no-http'"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("STDOUT:", stdout.read().decode('utf-8', 'ignore'))
        print("STDERR:", stderr.read().decode('utf-8', 'ignore'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
