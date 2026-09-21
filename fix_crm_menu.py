import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
# Find the correct CRM action (crm.crm_lead_all_leads or crm.crm_lead_opportunities)
crm_action = env.ref('crm.crm_lead_all_leads', raise_if_not_found=False)
if not crm_action:
    crm_action = env.ref('crm.crm_lead_opportunities', raise_if_not_found=False)
if not crm_action:
    # Search for any crm act_window
    crm_action = env['ir.actions.act_window'].search([('res_model', '=', 'crm.lead')], limit=1)

if crm_action:
    print(f"Found CRM action: id={crm_action.id} name={crm_action.name}")
    menu = env.ref('crm.crm_menu_root')
    menu.write({'action': f'{crm_action._name},{crm_action.id}'})
    env.cr.commit()
    print(f"Fixed! crm_menu_root now points to action id={crm_action.id}")
else:
    print("ERROR: Could not find any CRM action to link. CRM module may be broken.")
    # List all crm-related actions
    acts = env['ir.actions.act_window'].search([('res_model', 'ilike', 'crm')])
    for a in acts:
        print(f"  act_window: id={a.id} | name={a.name} | model={a.res_model}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/fix_crm.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/fix_crm.py {CONTAINER}:/tmp/fix_crm.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/fix_crm.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
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
