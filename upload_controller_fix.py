import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

FILES = [
    (r'c:\odoo19\addons\whatsapp_web_chats\controllers\main.py',
     '/tmp/wa_main.py',
     '/mnt/extra-addons/whatsapp_web_chats/controllers/main.py'),
]

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        for local, tmp, container_path in FILES:
            sftp.put(local, tmp)
            print(f"Uploaded {local}")
        sftp.close()

        cmds = []
        for local, tmp, container_path in FILES:
            cmds.append(f"echo '{PASSWORD}' | sudo -S docker cp {tmp} {CONTAINER}:{container_path}")
            cmds.append(f"echo '{PASSWORD}' | sudo -S docker exec -u root {CONTAINER} chown odoo:odoo {container_path}")
        cmds.append(f"echo '{PASSWORD}' | sudo -S docker restart {CONTAINER}")

        for cmd in cmds:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
            out = stdout.read().decode('utf-8', 'ignore').strip()
            if out:
                print("OUT:", out)

        print("Done! Container restarting.")
    finally:
        client.close()

if __name__ == '__main__':
    main()
