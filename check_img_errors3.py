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

msgs = env['whatsapp.message'].sudo().search([
    ('mobile_number', 'ilike', '771883091'),
    ('create_date', '>=', str(start)),
], order='id asc')

print(f"All messages today to 771883091: {len(msgs)}")
for m in msgs:
    try:
        err = getattr(m, 'failure_reason', '') or ''
        has_att = False
        att_type = ''
        if m.mail_message_id and m.mail_message_id.attachment_ids:
            has_att = True
            att_type = ', '.join([a.mimetype or a.name or '?' for a in m.mail_message_id.attachment_ids])
        print(f"  id={m.id} | state={m.state} | has_att={has_att} | att={att_type[:50]} | err={err[:100]}")
    except Exception as ex:
        print(f"  id={m.id} | ERROR reading: {ex}")
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
            if stripped:
                print(stripped)
    finally:
        client.close()

if __name__ == '__main__':
    main()
