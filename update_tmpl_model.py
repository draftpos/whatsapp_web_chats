import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
try:
    msg = env['whatsapp.message'].sudo().browse(7015)
    tmpl = msg.wa_template_id
    partner_model = env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
    
    print("Old Model:", tmpl.model_id.model)
    tmpl.write({'model_id': partner_model.id})
    print("New Model:", tmpl.model_id.model)
    
    msgs = env['whatsapp.message'].sudo().browse([7015, 7014, 7013])
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
        with sftp.file('/tmp/update_tmpl_model.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/update_tmpl_model.py {CONTAINER}:/tmp/update_tmpl_model.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/update_tmpl_model.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
