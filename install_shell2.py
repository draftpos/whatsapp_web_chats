import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')

shell_cmd = """docker exec -i odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn odoo shell -c /etc/odoo/odoo.conf -d bestbeginnings_s2_havano_pro_nyyrglzxjnfn --no-http << 'SHELL_EOF'
module = env['ir.module.module'].search([('name', '=', 'havano_schools_odoo')])
print('State before:', module.state)
if module.state != 'installed':
    module.button_immediate_install()
print('State after:', module.state)
env.cr.commit()
SHELL_EOF
"""

sftp = client.open_sftp()
with sftp.file('/home/amakoni/install_module_script.sh', 'w') as f:
    f.write(shell_cmd)
sftp.close()

cmd = "echo 'Ashley@#$1234' | sudo -S bash /home/amakoni/install_module_script.sh"
stdin, stdout, stderr = client.exec_command(cmd)

print("Stdout:\n", stdout.read().decode('utf-8', 'ignore'))
print("Stderr:\n", stderr.read().decode('utf-8', 'ignore'))

client.close()
