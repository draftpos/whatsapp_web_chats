import paramiko
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
    
    # write python script to file on server
    script = """import sys
import odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
registry = odoo.registry('supportwhatsapp_s4_havano_pro_yvnmgevazsj')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    accounts = env['whatsapp.account'].search([])
    for acc in accounts:
        print('Account:', acc.name)
        print('App ID:', acc.app_uid)
        print('Phone UID:', acc.phone_uid)
        print('Webhook Verify Token:', acc.webhook_verify_token)
        print('---')
"""
    
    stdin, stdout, stderr = client.exec_command("cat > /tmp/check_wa.py << 'EOF'\n" + script + "\nEOF")
    stdout.channel.recv_exit_status()
    
    cmd = "echo 'Ashley@#$1234' | sudo -S docker cp /tmp/check_wa.py odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj:/tmp/check_wa.py && echo 'Ashley@#$1234' | sudo -S docker exec odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj python3 /tmp/check_wa.py"
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', 'ignore'))
    print(stderr.read().decode('utf-8', 'ignore'))
finally:
    client.close()
