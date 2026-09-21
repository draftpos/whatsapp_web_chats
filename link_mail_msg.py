import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
try:
    msgs = env['whatsapp.message'].sudo().browse([7015, 7014, 7013])
    partner = env.user.partner_id
    
    for msg in msgs:
        if not msg.mail_message_id:
            mail_msg = partner.message_post(
                body=f'[WhatsApp Template Sent: {msg.wa_template_id.template_name}]',
                message_type='comment',
                subtype_xmlid='mail.mt_note'
            )
            msg.write({'mail_message_id': mail_msg.id})
            print(f"Msg {msg.id}: Linked to new mail_msg {mail_msg.id} on model {mail_msg.model}")
        else:
            print(f"Msg {msg.id} already has mail_message_id.")

    msgs.write({'state': 'outgoing', 'failure_type': False, 'failure_reason': False})
    
    env.ref('whatsapp.ir_cron_send_whatsapp_queue')._trigger()
    print("Triggered cron.")
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
        with sftp.file('/tmp/link_mail_msg.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/link_mail_msg.py {CONTAINER}:/tmp/link_mail_msg.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/link_mail_msg.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
