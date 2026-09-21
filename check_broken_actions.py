import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
# Test what _preload_action_ids actually returns
# This is the endpoint that fails with 'Could not preload action IDs'
try:
    result = env['ir.actions.act_window']._get_bindings('crm.crm_menu_root')
    print(f"Bindings OK: {result}")
except Exception as e:
    print(f"Bindings ERROR: {e}")

# Check if there are any broken ir.actions entries that reference missing models
broken = []
for act in env['ir.actions.act_window'].search([]):
    try:
        if act.res_model and act.res_model not in env:
            broken.append(f"act_window id={act.id} name={act.name} model={act.res_model}")
    except:
        pass

for act in env['ir.actions.server'].search([]):
    try:
        if act.model_id and act.model_id.model not in env:
            broken.append(f"act_server id={act.id} name={act.name} model={act.model_id.model}")
    except:
        pass

if broken:
    print(f"Found {len(broken)} broken actions:")
    for b in broken[:20]:
        print(f"  {b}")
else:
    print("No broken action references found!")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_actions.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_actions.py {CONTAINER}:/tmp/check_actions.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/check_actions.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
