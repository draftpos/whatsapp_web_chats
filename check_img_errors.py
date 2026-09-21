import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
import datetime

today = datetime.date.today()
start = datetime.datetime.combine(today, datetime.time.min)

# Check all messages today that have attachments and failed/errored
msgs = env['whatsapp.message'].sudo().search([
    ('create_date', '>=', str(start)),
    ('state', 'in', ['error', 'cancel', 'outgoing']),
], order='id desc')

print(f"Failed/pending messages today: {len(msgs)}")
for m in msgs:
    err = getattr(m, 'failure_reason', '') or ''
    att = bool(m.mail_message_id.attachment_ids) if m.mail_message_id else False
    body_snippet = str(m.body)[:40].replace('\\n', ' ') if m.body else ''
    print(f"  id={m.id} | to={m.mobile_number} | state={m.state} | has_att={att} | err={err[:80]} | body={body_snippet}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_errors.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_errors.py {CONTAINER}:/tmp/check_errors.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/check_errors.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=180)
        out = stdout.read().decode('utf-8', 'ignore')

        for line in out.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('//') and 'odoo' not in stripped.lower()[:5]:
                print(stripped)
    finally:
        client.close()

if __name__ == '__main__':
    main()
