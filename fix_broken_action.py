import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
# Delete the broken action that references the non-existent spreadsheet.revision model
broken_act = env['ir.actions.act_window'].sudo().browse(1031)
if broken_act.exists():
    name = broken_act.name
    model = broken_act.res_model
    broken_act.sudo().unlink()
    env.cr.commit()
    print(f"Deleted broken action id=1031 name={name} model={model}")
else:
    print("Action 1031 not found (already deleted?)")

# Also check if the send_attachment endpoint model exists
# The error is at web.assets_web.min.js:26161 - this is core whatsapp send_attachment
# Let's check the whatsapp.channel model has what it needs
try:
    wa_ch = env['whatsapp.channel'].search([], limit=1)
    print(f"whatsapp.channel OK, found {env['whatsapp.channel'].search_count([])} channels")
    # Check if attachment field exists on the model
    fields = env['whatsapp.channel'].fields_get()
    print(f"whatsapp.channel has {len(fields)} fields")
except Exception as e:
    print(f"whatsapp.channel ERROR: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/fix_actions.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/fix_actions.py {CONTAINER}:/tmp/fix_actions.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/fix_actions.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
