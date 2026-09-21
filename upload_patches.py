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
        sftp.put('c:\\odoo19\\addons\\whatsapp_web_chats\\models\\whatsapp_account.py', '/tmp/whatsapp_account.py')
        sftp.put('c:\\odoo19\\addons\\whatsapp_web_chats\\wizard\\send_school_balances_wizard.py', '/tmp/send_school_balances_wizard.py')
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/whatsapp_account.py {CONTAINER}:/mnt/extra-addons/whatsapp_web_chats/models/whatsapp_account.py && "
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/send_school_balances_wizard.py {CONTAINER}:/mnt/extra-addons/whatsapp_web_chats/wizard/send_school_balances_wizard.py"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("Stdout:", stdout.read().decode('utf-8'))
        print("Stderr:", stderr.read().decode('utf-8'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
