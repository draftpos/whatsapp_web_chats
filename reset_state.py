import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')

shell_cmd = """docker exec -i odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn odoo shell -c /etc/odoo/odoo.conf -d bestbeginnings_s2_havano_pro_nyyrglzxjnfn --no-http << 'SHELL_EOF'
module = env['ir.module.module'].search([('name', '=', 'havano_schools_odoo')])
print('State before:', module.state)
env.cr.execute("UPDATE ir_module_module SET state='installed' WHERE name='havano_schools_odoo'")
env.cr.commit()
print('State after reset:', module.state)
SHELL_EOF
"""

sftp = client.open_sftp()
with sftp.file('/home/amakoni/reset_module_state.sh', 'w') as f:
    f.write(shell_cmd)
sftp.close()

cmd = "echo 'Ashley@#$1234' | sudo -S bash /home/amakoni/reset_module_state.sh"
stdin, stdout, stderr = client.exec_command(cmd)

print("Stdout:\n", stdout.read().decode('utf-8', 'ignore'))
print("Stderr:\n", stderr.read().decode('utf-8', 'ignore'))

client.close()
