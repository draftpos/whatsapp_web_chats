import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

db_name = 'supportwhatsapp_s4_havano_pro_yvnmgevazsj'
container_name = f'odoo_{db_name}'

odoo_code = """
from datetime import datetime
from pytz import timezone

print('=== 1. WhatsApp Account SaaS Config ===')
accounts = env['whatsapp.account'].search([('saas_integration_active', '=', True)])
print(f'Accounts with SaaS active: {len(accounts)}')
for acc in accounts:
    print(f'  Account: {acc.name}')
    print(f'  saas_daily_sales_template_id: {acc.saas_daily_sales_template_id.template_name if acc.saas_daily_sales_template_id else "NOT SET <<<"}')
    print(f'  saas_welcome_template_id: {acc.saas_welcome_template_id.template_name if acc.saas_welcome_template_id else "NOT SET <<<"}')
    print(f'  saas_app_url: {acc.saas_app_url or "NOT SET <<<"}')

print()
print('=== 2. Tenants (first 5) ===')
tenants = env['whatsapp.saas.tenant'].search([])
print(f'Total tenants: {len(tenants)}')
for t in tenants[:5]:
    print(f'  {t.tenant_name} | Phone: {t.tenant_phone} | scheduled_time: {t.scheduled_time} | last_sales_sent_date: {t.last_sales_sent_date}')

print()
print('=== 3. Current Server Time vs Scheduled Times ===')
tz_name = env.user.tz or 'UTC'
tz = timezone(tz_name)
now = datetime.now(tz)
current_float = now.hour + now.minute / 60.0
current_date = now.date()
print(f'User TZ: {tz_name}')
print(f'Current local time: {now.strftime("%H:%M")} ({current_float:.2f})')
print(f'Current date: {current_date}')

if accounts:
    acc = accounts[0]
    tenants_to_send = env['whatsapp.saas.tenant'].search([
        ('account_id', '=', acc.id),
        ('scheduled_time', '<=', current_float),
        '|', ('last_sales_sent_date', '!=', current_date), ('last_sales_sent_date', '=', False)
    ])
    print(f'Tenants that WOULD get daily sales RIGHT NOW: {len(tenants_to_send)}')
    for t in tenants_to_send:
        print(f'  -> {t.tenant_name} | scheduled_time: {t.scheduled_time}')

print()
print('=== 4. Local havanoposdesk model check ===')
has_local_saas = 'havanoposdesk.tenant' in env
print(f'havanoposdesk.tenant model exists: {has_local_saas}')
if has_local_saas:
    local_tenants = env['havanoposdesk.tenant'].sudo().search([])
    print(f'Local tenants count: {len(local_tenants)}')
    has_stores = 'havanoposdesk.store' in env
    print(f'havanoposdesk.store model exists: {has_stores}')

print()
print('=== 5. Cron Job Status ===')
cron = env['ir.cron'].sudo().search([('code', 'like', '_cron_sync_and_send_saas_data')], limit=1)
if cron:
    print(f'Cron: {cron.name}')
    print(f'Active: {cron.active}')
    print(f'Interval: {cron.interval_number} {cron.interval_type}')
    print(f'Next call: {cron.nextcall}')
else:
    print('NO CRON FOUND <<<')

print()
print('=== 6. Recent Odoo logs (last 5 errors from daily_sales) ===')
import subprocess
result = subprocess.run(
    ['docker', 'logs', '--tail', '200', 'odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj'],
    capture_output=True, text=True
)
for line in (result.stdout + result.stderr).splitlines():
    if 'daily_sales' in line.lower() or 'saas' in line.lower() or ('error' in line.lower() and 'whatsapp' in line.lower()):
        print(line)
"""

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)

    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_daily_sales_sw.py', 'w') as f:
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

    cmd = f"docker exec -i {container_name} odoo shell -c /etc/odoo/odoo.conf -d {db_name} --no-http < /tmp/check_daily_sales_sw.py"
    channel.send(cmd + "\n")
    time.sleep(20)

    out = wait_for_prompt(channel, timeout=25)
    channel.send("exit\n")

except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
