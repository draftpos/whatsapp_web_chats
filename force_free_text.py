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
    
    # Force all variables to be free_text!
    for var in tmpl.variable_ids:
        var.write({
            'field_type': 'free_text',
            'field_name': False
        })
        print(f"Set var {var.name} to free_text.")
    
    # Also ensure model is res.partner just in case
    partner_model = env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
    tmpl.write({'model_id': partner_model.id})
    print("Template Model:", tmpl.model_id.model)
    
    msgs = env['whatsapp.message'].sudo().browse([7015, 7014, 7013])
    msgs.write({'state': 'outgoing', 'failure_type': False, 'failure_reason': False})
    
    env.ref('whatsapp.ir_cron_send_whatsapp_queue')._trigger()
    print("Fixed variables and triggered cron.")
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
        with sftp.file('/tmp/force_free_text.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/force_free_text.py {CONTAINER}:/tmp/force_free_text.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/force_free_text.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
