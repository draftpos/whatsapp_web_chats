import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
# Check the CRM menu action
menu = env.ref('crm.crm_menu_root', raise_if_not_found=False)
if menu:
    print(f"CRM Menu found: id={menu.id} | action={menu.action}")
    if menu.action:
        action = menu.action
        print(f"  Action type: {action._name} | id={action.id} | name={action.name}")
    else:
        print("  ERROR: Menu has no action linked!")
else:
    print("ERROR: crm.crm_menu_root not found in DB!")

# Check the preload actions - look for broken ones
broken = env['ir.actions.act_window'].search([('res_model', '!=', False)])
print(f"\\nChecking ir.actions.act_window for broken models...")
for act in broken[:20]:
    try:
        model_obj = env[act.res_model]
    except KeyError:
        print(f"  BROKEN action id={act.id} name={act.name} - model={act.res_model} NOT IN REGISTRY!")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_crm.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_crm.py {CONTAINER}:/tmp/check_crm.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/check_crm.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
