import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

LOCAL_FILE = r'c:\odoo19\addons\whatsapp_web_chats\models\whatsapp_account.py'
REMOTE_TMP = '/tmp/whatsapp_account.py'
CONTAINER_PATH = '/mnt/extra-addons/whatsapp_web_chats/models/whatsapp_account.py'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        sftp.put(LOCAL_FILE, REMOTE_TMP)
        sftp.close()
        print("Uploaded whatsapp_account.py")

        cmds = [
            f"echo '{PASSWORD}' | sudo -S docker cp {REMOTE_TMP} {CONTAINER}:{CONTAINER_PATH}",
            f"echo '{PASSWORD}' | sudo -S docker exec -u root {CONTAINER} chown odoo:odoo {CONTAINER_PATH}",
            f"echo '{PASSWORD}' | sudo -S docker restart {CONTAINER}",
        ]
        for cmd in cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
            out = stdout.read().decode('utf-8', 'ignore').strip()
            err = stderr.read().decode('utf-8', 'ignore').strip()
            if out:
                print("OUT:", out)

        print("Container restarted. Logger fix applied.")
    finally:
        client.close()

if __name__ == '__main__':
    main()
