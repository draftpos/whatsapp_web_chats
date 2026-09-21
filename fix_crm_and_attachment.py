import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

# Fix CRM menu + check attachment error in one shot
ODOO_SCRIPT = """
# 1. Fix CRM menu again (re-check after restart)
menu = env.ref('crm.crm_menu_root', raise_if_not_found=False)
if menu:
    print(f"CRM menu action: {menu.action}")
    if not menu.action:
        crm_action = env.ref('crm.crm_lead_all_leads', raise_if_not_found=False)
        if not crm_action:
            crm_action = env['ir.actions.act_window'].search([('res_model', '=', 'crm.lead')], limit=1)
        if crm_action:
            menu.write({'action': f'{crm_action._name},{crm_action.id}'})
            env.cr.commit()
            print(f"FIXED CRM menu -> action id={crm_action.id}")
        else:
            print("ERROR: Cannot find CRM action to link")
    else:
        print("CRM menu OK")

# 2. Check what send_attachment endpoint does
# The error is from /web/whatsapp/<int:channel_id>/attachment - find it
import os
for root, dirs, files in os.walk('/usr/lib/python3/dist-packages/odoo/addons/whatsapp'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                content = open(path).read()
                if 'send_attachment' in content or 'attachment' in content.lower() and 'route' in content.lower():
                    print(f"Found: {path}")
            except:
                pass
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/fix_all.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/fix_all.py {CONTAINER}:/tmp/fix_all.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"bash -c 'cat /tmp/fix_all.py | /usr/bin/odoo shell -d {DB} --no-http 2>&1'"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=180)
        out = stdout.read().decode('utf-8', 'ignore')
        for line in out.splitlines():
            s = line.strip()
            if s and 'WARNING' not in s and 'werkzeug' not in s:
                print(s)
    finally:
        client.close()

if __name__ == '__main__':
    main()
