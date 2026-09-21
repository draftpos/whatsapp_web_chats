import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        
        script = """
import datetime
today = datetime.datetime.now().date()
msgs = env['whatsapp.message'].search([
    '|', ('mobile_number', 'ilike', '263771883091'), ('mobile_number', 'ilike', '0771883091'),
    ('create_date', '>=', str(today))
], order='id desc')
print(f"Found {len(msgs)} messages.")
for msg in msgs:
    fail_reason = getattr(msg, 'failure_reason', '')
    error_code = getattr(msg, 'failure_type', '')
    print(f"ID={msg.id} | State={msg.state} | Type={msg.message_type} | Template={msg.wa_template_id.name if msg.wa_template_id else 'None'} | Error={error_code} : {fail_reason}")
    print(f"   Body snippet: {str(msg.body)[:50] if msg.body else 'None'}")
    print(f"   Has Attachment: {bool(msg.mail_message_id.attachment_ids)}")
        """
        
        with open('c:\\odoo19\\addons\\whatsapp_web_chats\\check_shell.py', 'w') as f:
            f.write(script)
            
        sftp = client.open_sftp()
        sftp.put('c:\\odoo19\\addons\\whatsapp_web_chats\\check_shell.py', '/tmp/check_shell.py')
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_shell.py {CONTAINER}:/tmp/check_shell.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec -u root {CONTAINER} chown odoo:odoo /tmp/check_shell.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec -u odoo {CONTAINER} odoo shell -c /etc/odoo/odoo.conf -d demo1 --no-http < /tmp/check_shell.py"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("Stdout:", stdout.read().decode('utf-8'))
        print("Stderr:", stderr.read().decode('utf-8'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
