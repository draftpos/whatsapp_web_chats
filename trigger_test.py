import paramiko
import time

host = "173.249.39.201"
user = "amakoni"
password = "Ashley@#$1234"

odoo_code = """
account = env['whatsapp.account'].search([('saas_integration_active', '=', True)], limit=1)
target_phone = '+263771883091'
import time
target_name = f'Test User {int(time.time())}'

print('Account:', account.name)
if account.saas_welcome_template_id:
    env['whatsapp.saas.tenant']._send_whatsapp_message(account, target_phone, account.saas_welcome_template_id, [target_name])
    print('Triggered Welcome')

if account.saas_expiration_template_id:
    env['whatsapp.saas.tenant']._send_whatsapp_message(account, target_phone, account.saas_expiration_template_id, [target_name, '5'])
    print('Triggered Expiration')

if account.saas_daily_sales_template_id:
    stores = [
        {'name': 'Downtown Branch', 'sales': '$1,500.00', 'orders': '45', 'avg': '$450.00'},
        {'name': 'Uptown Branch', 'sales': '$850.50', 'orders': '30', 'avg': '$28.35'},
        {'name': 'Eastside Mall', 'sales': '$2,200.00', 'orders': '110', 'avg': '$20.00'},
        {'name': 'Airport Kiosk', 'sales': '$450.25', 'orders': '80', 'avg': '$5.62'},
        {'name': 'Westend Store', 'sales': '$3,100.00', 'orders': '62', 'avg': '$50.00'},
    ]
    for store in stores:
        env['whatsapp.saas.tenant']._send_whatsapp_message(
            account, target_phone, account.saas_daily_sales_template_id, 
            [target_name, '26 Sep 2026', store['sales'], store['name'], store['orders'], store['avg']]
        )
    print('Triggered Daily Sales for 5 stores')

env.cr.commit()
time.sleep(2)

from datetime import datetime, timedelta
cutoff = (datetime.utcnow() - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
msgs = env['whatsapp.message'].search([('mobile_number_formatted', 'like', '263771883091'), ('create_date', '>=', cutoff)], order='id desc', limit=5)

for m in msgs:
    print(f'--- Msg {m.id} ---')
    print(f'  Template: {m.wa_template_id.template_name if m.wa_template_id else "N/A"}')
    print(f'  Template Model: {m.wa_template_id.model_id.model if m.wa_template_id else "N/A"}')
    print(f'  Template Lang: {m.wa_template_id.lang_code if m.wa_template_id else "N/A"}')
    print(f'  free_text_json: {m.free_text_json}')
    print(f'  state: {m.state}')
    print(f'  failure_reason: {m.failure_reason}')
    print(f'  failure_type: {m.failure_type}')
"""

print("Connecting via SSH...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=30, banner_timeout=30)
    print("Connected successfully.")

    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_saas.py', 'w') as f:
        f.write(odoo_code)
    sftp.close()

    shell = ssh.invoke_shell()
    time.sleep(1)

    shell.send("sudo su\n")
    time.sleep(1)
    output = shell.recv(1024).decode()
    if "password" in output.lower():
        shell.send(password + "\n")
        time.sleep(2)

    shell.send("cd /home/supportwhatsapp_s4_havano_pro_yvnmgevazsj/custom-addons/whatsapp_web_chats && git fetch --all && git reset --hard origin/master\n")
    time.sleep(5)
    shell.send("docker exec odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj odoo -c /etc/odoo/odoo.conf -d supportwhatsapp_s4_havano_pro_yvnmgevazsj -u whatsapp_web_chats --stop-after-init --no-http\n")
    time.sleep(20)
    shell.send("docker restart odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj\n")
    time.sleep(15)

    shell.send("docker exec -i odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj odoo shell -c /etc/odoo/odoo.conf -d supportwhatsapp_s4_havano_pro_yvnmgevazsj --no-http < /tmp/test_saas.py\n")
    time.sleep(30)

    shell.send("docker logs --tail 100 odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj 2>&1 | grep -i 'whatsapp\|api\|error\|fail' \n")
    time.sleep(5)

    output = shell.recv(65536).decode('utf-8', errors='replace')
    print("Output from shell:")
    import sys
    sys.stdout.buffer.write(output.encode('utf-8'))
    print()

finally:
    ssh.close()
    print("Disconnected.")
