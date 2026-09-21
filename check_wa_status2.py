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
start = datetime.datetime.combine(today, datetime.time.min)
end   = datetime.datetime.combine(today, datetime.time.max)

msgs = env['whatsapp.message'].sudo().search([
    ('mobile_number', 'ilike', '771883091'),
    ('create_date', '>=', str(start)),
    ('create_date', '<=', str(end)),
])
print(f"Total messages today for this number: {len(msgs)}")
for m in msgs:
    err = getattr(m, 'failure_reason', '')
    att = bool(m.mail_message_id.attachment_ids) if m.mail_message_id else False
    body_snippet = str(m.body)[:30].replace('\\n', ' ') if m.body else ''
    tmpl = m.wa_template_id.name if getattr(m, 'wa_template_id', False) else 'None'
    print(f"  id={m.id} to={m.mobile_number} state={m.state} tmpl={tmpl} att={att} body={body_snippet} err={err}")
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
