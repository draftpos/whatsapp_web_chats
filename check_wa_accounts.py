import paramiko
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
    # create a python script inside the container to print whatsapp account info
    script = """
import sys
import odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
registry = odoo.registry('supportwhatsapp_s4_havano_pro_yvnmgevazsj')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    accounts = env['whatsapp.account'].search([])
    for acc in accounts:
        print(f"Account: {acc.name}, App ID: {acc.app_uid}, Phone: {acc.phone_uid}, Webhook: {acc.webhook_verify_token}")
"""
    cmd = f"echo 'Ashley@#$1234' | sudo -S docker exec -i odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj python3 -c \"{script}\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', 'ignore'))
    print(stderr.read().decode('utf-8', 'ignore'))
finally:
    client.close()
