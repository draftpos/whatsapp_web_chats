import paramiko

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

python_script = """
view = env['ir.ui.view'].search([('key', '=', 'crm.crm_lead_view_form')], limit=1)
if view:
    print('===START===')
    print(view.get_combined_arch())
    print('===END===')
"""

command = f"echo '{password}' | sudo -S docker exec -i odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae odoo shell -c /etc/odoo/odoo.conf -d jlink_havano_pro_cpsmddqqvbceafpdpqoknnae --no-http << 'EOF'\n{python_script}\nEOF\n"

stdin, stdout, stderr = ssh.exec_command(command)

out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')

with open('crm_view_arch.xml', 'w', encoding='utf-8') as f:
    f.write(out)
    if err:
        f.write("\n\n--- ERRORS ---\n" + err)
        
print("Saved to crm_view_arch.xml")
ssh.close()
