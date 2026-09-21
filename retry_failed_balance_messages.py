import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

# This Python code is piped into `odoo-bin shell` which already has `env` available
ODOO_SCRIPT = f"""
import datetime

today = datetime.date.today()
start = datetime.datetime.combine(today, datetime.time.min)
end   = datetime.datetime.combine(today, datetime.time.max)

# Find failed/cancelled template messages from today
failed = env['whatsapp.message'].sudo().search([
    ('state', 'in', ['error', 'cancel']),
    ('wa_template_id', '!=', False),
    ('create_date', '>=', str(start)),
    ('create_date', '<=', str(end)),
])
print(f"Failed/cancelled template messages today: {{len(failed)}}")
for m in failed:
    print(f"  id={{m.id}}  to={{m.mobile_number}}  tmpl={{m.wa_template_id.template_name}}  state={{m.state}}  err={{getattr(m, 'failure_reason', '')}}")

# Also check all stuck outgoing ones
outgoing = env['whatsapp.message'].sudo().search([
    ('state', '=', 'outgoing'),
    ('wa_template_id', '!=', False),
])
print(f"Stuck outgoing template messages: {{len(outgoing)}}")

to_retry = failed | outgoing
if to_retry:
    print(f"Resetting {{len(to_retry)}} messages to outgoing...")
    to_retry.sudo().write({{'state': 'outgoing'}})
    env.cr.commit()
    try:
        cron = env.ref('whatsapp.ir_cron_send_whatsapp_queue', raise_if_not_found=False)
        if cron:
            cron.sudo()._trigger()
            env.cr.commit()
            print("Send cron triggered successfully.")
        else:
            print("whatsapp.ir_cron_send_whatsapp_queue not found.")
    except Exception as e:
        print(f"Cron trigger error: {{e}}")
else:
    print("No messages to retry.")

print("DONE.")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

        # Write the odoo shell script to /tmp on the host
        sftp = client.open_sftp()
        with sftp.file('/tmp/retry_wa_shell.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()
        print("Script uploaded.")

        # Copy into container then pipe into /usr/bin/odoo shell
        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/retry_wa_shell.py {CONTAINER}:/tmp/retry_wa_shell.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/retry_wa_shell.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
        )
        print("Running odoo shell script on demo1...")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=180)
        out = stdout.read().decode('utf-8', 'ignore')
        err = stderr.read().decode('utf-8', 'ignore')

        # Filter out Odoo startup noise, just show our print() lines
        for line in out.splitlines():
            stripped = line.strip()
            if stripped:
                print(stripped)
        if err.strip() and '[sudo]' not in err:
            print("STDERR:", err[:500])

    finally:
        client.close()

if __name__ == '__main__':
    main()
