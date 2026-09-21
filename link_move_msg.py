import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
move = env['account.move'].sudo().search([], limit=1)
if not move:
    partner = env.user.partner_id
    move = env['account.move'].sudo().create({
        'partner_id': partner.id,
        'move_type': 'out_invoice',
    })
    print("Created dummy move:", move.id)
else:
    print("Found existing move:", move.id)

msgs = env['whatsapp.message'].sudo().browse([7015, 7014, 7013])
for msg in msgs:
    mail_msg = move.message_post(
        body=f'[WhatsApp Template Sent: {msg.wa_template_id.template_name}]',
        message_type='comment',
        subtype_xmlid='mail.mt_note'
    )
    msg.write({
        'mail_message_id': mail_msg.id,
        'state': 'outgoing',
        'failure_type': False,
        'failure_reason': False
    })
    print(f"Msg {msg.id}: Linked to move mail_msg {mail_msg.id} on model {mail_msg.model}")

env.cr.commit()
print("Committed successfully.")

env.ref('whatsapp.ir_cron_send_whatsapp_queue')._trigger()
print("Triggered cron.")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/link_move_msg.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/link_move_msg.py {CONTAINER}:/tmp/link_move_msg.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/link_move_msg.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
