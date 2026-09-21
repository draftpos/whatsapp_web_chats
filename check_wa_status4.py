import paramiko
import sys

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
import datetime

today = datetime.date.today()

# Check whatsapp_account_balance_log or similar
# Let's find the model name first.
# account._create_balance_log is defined in whatsapp_account.py:
# it creates 'whatsapp.balance.log' probably?
# Let's check the logs for today.

logs = env['whatsapp.balance.log'].sudo().search([
    ('create_date', '>=', str(today)),
    ('status', '=', 'failed')
])
print(f"Total failed logs today: {len(logs)}")
for log in logs:
    print(f"  Parent: {log.parent_name} | Phone: {log.parent_phone} | Err: {log.error_message}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_wa_status.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_wa_status.py {CONTAINER}:/tmp/check_wa_status.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/check_wa_status.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=180)
        out = stdout.read().decode('utf-8', 'ignore')

        for line in out.splitlines():
            stripped = line.strip()
            if stripped:
                print(stripped)
    finally:
        client.close()

if __name__ == '__main__':
    main()
