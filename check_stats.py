import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
logs = env['whatsapp.school.balance.log'].search([], order='id desc', limit=200)
sent = 0
failed_phone = 0
failed_dup = 0
failed_other = 0

for log in logs:
    if log.status == 'sent':
        sent += 1
    elif 'Duplicate' in log.error_message:
        failed_dup += 1
    elif 'No parent found' in log.error_message:
        failed_phone += 1
    else:
        failed_other += 1

print(f"Out of last 200 logs: Sent={sent}, Failed_Phone={failed_phone}, Failed_Dup={failed_dup}, Failed_Other={failed_other}")
if failed_other > 0:
    for log in logs:
        if log.status != 'sent' and 'Duplicate' not in log.error_message and 'No parent found' not in log.error_message:
            print(f"Other Error: {log.error_message}")
            break
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_stats.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_stats.py {CONTAINER}:/tmp/check_stats.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/check_stats.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=180)
        out = stdout.read().decode('utf-8', 'ignore')
        for line in out.splitlines():
            s = line.strip()
            if s and 'WARNING' not in s[:10] and 'werkzeug' not in s:
                print(s)
    finally:
        client.close()

if __name__ == '__main__':
    main()
