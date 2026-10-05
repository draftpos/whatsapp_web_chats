import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

python_script = """
import odoo

odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'jlink_havano_pro_cpsmddqqvbceafpdpqoknnae'])
registry = odoo.registry('jlink_havano_pro_cpsmddqqvbceafpdpqoknnae')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    admin_user = env['res.users'].search([('name', 'ilike', 'Administrator')], limit=1)
    if admin_user:
        unassigned_chats = env['discuss.channel'].search([
            ('channel_type', '=', 'whatsapp'),
            ('wa_agent_id', '=', False)
        ])
        if unassigned_chats:
            unassigned_chats.write({'wa_agent_id': admin_user.id})
            print(f"Successfully assigned {len(unassigned_chats)} existing chats to {admin_user.name}")
            cr.commit()
        else:
            print("No unassigned chats found.")
    else:
        print("Could not find Administrator user.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/mass_assign_chats.py', 'w') as f:
    f.write(python_script)
sftp.close()

# The sudo password is piped correctly this time
command = f"echo '{password}' | sudo -S -E docker exec -i odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae python3 - < /tmp/mass_assign_chats.py"
stdin, stdout, stderr = ssh.exec_command(command)
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
