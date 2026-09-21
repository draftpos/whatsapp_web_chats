import paramiko
import sys

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

LOCAL_FILE = r'c:\odoo19\addons\whatsapp_web_chats\wizard\send_school_balances_wizard.py'
REMOTE_TMP = '/tmp/send_school_balances_wizard.py'
CONTAINER_PATH = '/mnt/extra-addons/whatsapp_web_chats/wizard/send_school_balances_wizard.py'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        
        # Upload file
        sftp = client.open_sftp()
        sftp.put(LOCAL_FILE, REMOTE_TMP)
        sftp.close()
        print("File uploaded to /tmp")

        # Copy into container and restart
        cmds = [
            f"echo '{PASSWORD}' | sudo -S docker cp {REMOTE_TMP} {CONTAINER}:{CONTAINER_PATH}",
            f"echo '{PASSWORD}' | sudo -S docker exec -u root {CONTAINER} chown odoo:odoo {CONTAINER_PATH}",
            f"echo '{PASSWORD}' | sudo -S docker restart {CONTAINER}",
        ]
        for cmd in cmds:
            print(f"Running: {cmd[:80]}...")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
            out = stdout.read().decode('utf-8', 'ignore')
            err = stderr.read().decode('utf-8', 'ignore')
            if out.strip():
                print("OUT:", out.strip())
            if err.strip() and 'password' not in err.lower():
                print("ERR:", err.strip())

        print("Done! Container restarting...")
    finally:
        client.close()

if __name__ == '__main__':
    main()
