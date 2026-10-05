import paramiko
import time

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password)

channel = ssh.invoke_shell()
channel.send("sudo -i\n")
time.sleep(1)
channel.send(password + "\n")
time.sleep(1)
channel.send("docker exec odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae odoo shell -c /etc/odoo/odoo.conf -d jlink_havano_pro_cpsmddqqvbceafpdpqoknnae --no-http << 'EOF'\n")
channel.send("view = env['ir.ui.view'].search([('key', '=', 'crm.crm_lead_view_form')], limit=1)\n")
channel.send("if view:\n")
channel.send("    print('===START===')\n")
channel.send("    print(view.get_combined_arch())\n")
channel.send("    print('===END===')\n")
channel.send("EOF\n")
time.sleep(5)

out = channel.recv(99999).decode('utf-8')
with open('crm_view_arch.xml', 'w', encoding='utf-8') as f:
    f.write(out)

print("Saved to crm_view_arch.xml")
ssh.close()
