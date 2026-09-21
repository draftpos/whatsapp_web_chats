import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
try:
    from odoo.addons.whatsapp.tools.whatsapp_exception import WhatsAppError
    
    msg = env['whatsapp.message'].sudo().browse(7015)
    msg.write({'state': 'outgoing', 'failure_type': False, 'failure_reason': False})
    print(f"Triggering _send_message() for msg {msg.id}...")
    
    # Actually, _send_message suppresses WhatsAppError and writes to failure_type!
    # Let's see what it wrote.
    msg._send_message(with_commit=False)
    
    print(f"After send: state={msg.state}, failure_type={msg.failure_type}, failure_reason={msg.failure_reason}")
    
    # If it's a template error, let's trace it manually by duplicating the core logic!
    if msg.failure_type == 'template':
        print("Tracing template failure...")
        template = msg.wa_template_id
        print("Status:", template.status)
        print("Quality:", template.quality)
        print("Msg Model:", msg.mail_message_id.model)
        print("Tmpl Model:", template.model)
        
        RecordModel = env[msg.mail_message_id.model].with_user(msg.env.user)
        from_record = RecordModel.browse(msg.mail_message_id.res_id)
        
        try:
            send_vals, attachment = template._get_send_template_vals(
                record=from_record,
                whatsapp_message=msg,
            )
            print("send_vals successfully generated:", send_vals)
        except Exception as e:
            import traceback
            print("Failed to generate send_vals:")
            print(traceback.format_exc())
            
except Exception as e:
    import traceback
    print("Error:", traceback.format_exc())
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/trace_error.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/trace_error.py {CONTAINER}:/tmp/trace_error.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/trace_error.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
