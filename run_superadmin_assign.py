import paramiko
import time

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

python_script = """
import sys
import odoo

odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'jlink_havano_pro_cpsmddqqvbceafpdpqoknnae'])
registry = odoo.registry('jlink_havano_pro_cpsmddqqvbceafpdpqoknnae')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    group = env.ref('whatsapp_web_chats.group_whatsapp_superadmin', raise_if_not_found=False)
    
    if group:
        admin_user = env['res.users'].search([('name', 'ilike', 'Administrator')], limit=1)
        if admin_user:
            admin_user.write({'groups_id': [(4, group.id)]})
            print(f"Successfully added 'Super Administrator' role to {admin_user.name}")
        else:
            print("Could not find user named 'Administrator'")
    else:
        print("Super admin group not found. Did the module update successfully?")
"""

# Save script to server
sftp = ssh.open_sftp()
with sftp.file('/tmp/assign_super_admin.py', 'w') as f:
    f.write(python_script)
sftp.close()

# Run it
command = f"echo '{password}' | sudo -S docker exec -i odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae python3 - < /tmp/assign_super_admin.py"
stdin, stdout, stderr = ssh.exec_command(command)
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
