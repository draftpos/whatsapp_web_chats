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
        sftp.put(r'c:\odoo19\addons\whatsapp_web_chats\check_demo1_failures.py', '/tmp/check_demo1_failures.py')
        sftp.close()
        cmd_cp_files = f"docker cp /tmp/chats.js {CONTAINER}:/odoo/odoo_dev19/custom/whatsapp_web_chats/static/src/js/chats.js && docker cp /tmp/chats_template.xml {CONTAINER}:/odoo/odoo_dev19/custom/whatsapp_web_chats/static/src/xml/chats_template.xml && docker cp /tmp/whatsapp_account.py {CONTAINER}:/odoo/odoo_dev19/custom/whatsapp_web_chats/models/whatsapp_account.py"
        client.exec_command(f"echo '{PASSWORD}' | sudo -S sh -c '{cmd_cp_files}'", timeout=120)
        
        cmd = f"docker cp /tmp/check_demo1_failures.py {CONTAINER}:/tmp/check_demo1_failures.py && docker exec -u root {CONTAINER} odoo shell -c /etc/odoo/odoo.conf -d demo1 --no-http < /tmp/check_demo1_failures.py"
        stdin, stdout, stderr = client.exec_command(f"echo '{PASSWORD}' | sudo -S sh -c '{cmd}'", timeout=120)
        print("DB Script Output:")
        print(stdout.read().decode('utf-8'))
        
        cmd = f"docker restart {CONTAINER}"
        client.exec_command(f"echo '{PASSWORD}' | sudo -S sh -c '{cmd}'", timeout=120)
    finally:
        client.close()

if __name__ == '__main__':
    main()
