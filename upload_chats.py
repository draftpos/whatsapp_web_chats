import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        sftp.put(r'c:\odoo19\addons\whatsapp_web_chats\static\src\js\chats.js', '/tmp/chats.js')
        sftp.put(r'c:\odoo19\addons\whatsapp_web_chats\static\src\xml\chats_template.xml', '/tmp/chats_template.xml')
        sftp.put(r'c:\odoo19\addons\whatsapp_web_chats\models\whatsapp_account.py', '/tmp/whatsapp_account.py')
        sftp.close()

        script = "env['ir.module.module'].search([('name', '=', 'whatsapp_web_chats')]).button_immediate_upgrade()\nenv.cr.commit()\n"
        cmd = f"echo '{script}' > /tmp/upgrade_script.py && docker cp /tmp/upgrade_script.py {CONTAINER}:/tmp/upgrade_script.py && docker exec -u root {CONTAINER} odoo shell -c /etc/odoo/odoo.conf -d demo1 --no-http < /tmp/upgrade_script.py"
        stdin, stdout, stderr = client.exec_command(f"echo '{PASSWORD}' | sudo -S sh -c \"{cmd}\"", timeout=120)
        print("Upgrade Output:")
        print(stdout.read().decode('utf-8'))
        
    finally:
        client.close()

if __name__ == '__main__':
    main()
