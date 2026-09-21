import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
tmpl = env['whatsapp.template'].sudo().search([('template_name', '=', 'school_balance_update')], limit=1)
if tmpl:
    print(f"Template '{tmpl.template_name}':")
    for var in tmpl.variable_ids:
        print(f" - {var.name}: type={var.field_type} field={var.field_name} line={var.line_type}")
else:
    print("Template school_balance_update not found")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_tmpl.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_tmpl.py {CONTAINER}:/tmp/check_tmpl.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/check_tmpl.py | /usr/bin/odoo shell -d {DB} --no-http'"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("STDOUT:", stdout.read().decode('utf-8', 'ignore'))
        print("STDERR:", stderr.read().decode('utf-8', 'ignore'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
