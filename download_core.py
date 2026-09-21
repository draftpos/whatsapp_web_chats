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
        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp {CONTAINER}:/mnt/extra-addons/whatsapp/models/whatsapp_message.py /tmp/core_whatsapp_message2.py"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        stdout.read()
        
        sftp = client.open_sftp()
        sftp.get('/tmp/core_whatsapp_message2.py', 'c:\\odoo19\\addons\\whatsapp_web_chats\\core_whatsapp_message2.py')
        sftp.close()
        print("Downloaded.")
    finally:
        client.close()

if __name__ == '__main__':
    main()
