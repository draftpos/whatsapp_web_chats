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
    print(f"Msg {msg.id} free_text_json type: {type(msg.free_text_json)}")
    print(f"Msg {msg.id} free_text_json value: {msg.free_text_json}")
    
    # If it's a string, convert it to dict and save!
    if isinstance(msg.free_text_json, str):
        try:
            parsed = json.loads(msg.free_text_json)
            # Actually, Odoo's Json field expects a dict, but if it was saved as string
            # we should write a dict.
            msg.write({'free_text_json': parsed})
            print(f"Parsed to dict and saved for {msg.id}.")
        except Exception as e:
            print(f"Failed to parse for {msg.id}: {e}")
    else:
        # even if it is already a dict, let's just make sure it's valid
        print("Already a dict.")
env.cr.commit()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_json.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_json.py {CONTAINER}:/tmp/check_json.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/check_json.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', 'ignore')
        for line in out.splitlines():
            if line.strip():
                print(line.strip())
    finally:
        client.close()

if __name__ == '__main__':
    main()
