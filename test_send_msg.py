import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
import logging
import traceback

with open('/tmp/test_out.txt', 'w') as f:
    msg = env['whatsapp.message'].sudo().browse(7015)
    f.write(f"Before: state={msg.state} ft={getattr(msg, 'failure_type', '')}\\n")
    msg.write({'state': 'outgoing', 'failure_type': False, 'failure_reason': False})
    
    # Try sending directly bypassing cron
    try:
        msg._send_message(with_commit=False)
        f.write(f"After send: state={msg.state} ft={getattr(msg, 'failure_type', '')}\\n")
    except Exception as e:
        f.write(f"Exception:\\n{traceback.format_exc()}\\n")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/test_send.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/test_send.py {CONTAINER}:/tmp/test_send.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/test_send.py | /usr/bin/odoo shell -d {DB} --no-http' && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} cat /tmp/test_out.txt"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("STDOUT:", stdout.read().decode('utf-8', 'ignore'))
        print("STDERR:", stderr.read().decode('utf-8', 'ignore'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
