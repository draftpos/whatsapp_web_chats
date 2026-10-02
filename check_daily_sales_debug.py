import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

db_name = 'jlink_havano_pro_cpsmddqqvbceafpdpqoknnae'
container_name = f'odoo_{db_name}'

odoo_code = """
from datetime import datetime
from pytz import timezone

print('=== 1. Checking WhatsApp Account SaaS Config ===')
accounts = env['whatsapp.account'].search([('saas_integration_active', '=', True)])
print(f'Accounts with SaaS active: {len(accounts)}')
for acc in accounts:
    print(f'  Account: {acc.name}')
    print(f'  saas_integration_active: {acc.saas_integration_active}')
    print(f'  saas_daily_sales_template_id: {acc.saas_daily_sales_template_id.template_name if acc.saas_daily_sales_template_id else "NOT SET"}')
    print(f'  saas_welcome_template_id: {acc.saas_welcome_template_id.template_name if acc.saas_welcome_template_id else "NOT SET"}')
    print(f'  saas_app_url: {acc.saas_app_url}')

print()
print('=== 2. Checking Tenants ===')
tenants = env['whatsapp.saas.tenant'].search([])
print(f'Total tenants: {len(tenants)}')
for t in tenants[:5]:
    print(f'  Tenant: {t.tenant_name} | Phone: {t.tenant_phone} | scheduled_time: {t.scheduled_time} | last_sales_sent_date: {t.last_sales_sent_date}')

print()
print('=== 3. Checking Current Server Time vs Scheduled Times ===')
tz = timezone(env.user.tz or 'UTC')
now = datetime.now(tz)
current_float = now.hour + now.minute / 60.0
current_date = now.date()
print(f'User TZ: {env.user.tz}')
print(f'Current time: {now.strftime("%H:%M")} ({current_float:.2f})')
print(f'Current date: {current_date}')

# Simulate query to see what would be selected
if accounts:
    acc = accounts[0]
    tenants_to_send = env['whatsapp.saas.tenant'].search([
        ('account_id', '=', acc.id),
        ('scheduled_time', '<=', current_float),
        '|', ('last_sales_sent_date', '!=', current_date), ('last_sales_sent_date', '=', False)
    ])
    print(f'Tenants that WOULD receive daily sales NOW: {len(tenants_to_send)}')
    for t in tenants_to_send:
        print(f'  -> {t.tenant_name} scheduled_time: {t.scheduled_time}')

print()
print('=== 4. Checking if havanoposdesk.tenant model exists ===')
has_local_saas = 'havanoposdesk.tenant' in env
print(f'has_local_saas model: {has_local_saas}')
if has_local_saas:
    local_tenants = env['havanoposdesk.tenant'].sudo().search([])
    print(f'Local tenants count: {len(local_tenants)}')

print()
print('=== 5. Checking Cron Job Status ===')
cron = env['ir.cron'].sudo().search([('model_id.model', '=', 'whatsapp.saas.tenant')], limit=1)
if cron:
    print(f'Cron: {cron.name}')
    print(f'Active: {cron.active}')
    print(f'Interval: {cron.interval_number} {cron.interval_type}')
    print(f'Next call: {cron.nextcall}')
else:
    print('NO CRON FOUND!')
"""

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)

    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_daily_sales.py', 'w') as f:
        f.write(odoo_code)
    sftp.close()

    channel = ssh.invoke_shell()

    def wait_for_prompt(chan, timeout=15):
        buffer = ""
        start_time = time.time()
        while True:
            if chan.recv_ready():
                data = chan.recv(4096).decode('utf-8', errors='replace')
                buffer += data
                sys.stdout.write(data)
                sys.stdout.flush()
                if "password for" in buffer.lower() or "#" in buffer or "$" in buffer:
                    return buffer
            if time.time() - start_time > timeout:
                return buffer
            time.sleep(0.5)

    wait_for_prompt(channel)
    channel.send("sudo -i\n")
    out = wait_for_prompt(channel)
    if "password for" in out.lower():
        channel.send(password + "\n")
        wait_for_prompt(channel)

    cmd = f"docker exec -i {container_name} odoo shell -c /etc/odoo/odoo.conf -d {db_name} --no-http < /tmp/check_daily_sales.py"
    channel.send(cmd + "\n")
    time.sleep(20)

    out = wait_for_prompt(channel, timeout=20)
    channel.send("exit\n")

except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
