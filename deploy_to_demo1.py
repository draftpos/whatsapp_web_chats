import os
import zipfile
import paramiko
import getpass
import argparse

LOCAL_ADDON_DIR = r'C:\odoo19\addons\whatsapp_web_chats'
ZIP_PATH = r'C:\odoo19\addons\whatsapp_web_chats\addon.zip'

def deploy(host, user, remote_path, restart_cmd):
    password = os.environ.get('SSH_PASS')
    if not password:
        password = getpass.getpass(f"Enter SSH password for {user}@{host}: ")
    password = password.strip()

    print("Zipping addon...")
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(LOCAL_ADDON_DIR):
            if '.git' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith('.pyc') or file == 'addon.zip' or file == 'deploy_to_demo1.py':
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=os.path.dirname(LOCAL_ADDON_DIR))
                zipf.write(file_path, arcname)

    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=22, username=user, password=password, timeout=15)
        
        print(f"Uploading zip file to /tmp/whatsapp_web_chats.zip...")
        sftp = ssh.open_sftp()
        sftp.put(ZIP_PATH, f"/tmp/whatsapp_web_chats.zip")
        sftp.close()

        print("Unzipping on server...")
        cmd = f"echo '{password}' | sudo -S mv /tmp/whatsapp_web_chats.zip {remote_path}/whatsapp_web_chats.zip && cd {remote_path} && echo '{password}' | sudo -S unzip -o whatsapp_web_chats.zip && echo '{password}' | sudo -S rm whatsapp_web_chats.zip"

        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

        print("Restarting Odoo container to apply updates...")
        restart_cmd_sudo = restart_cmd.replace("sudo ", f"echo '{password}' | sudo -S ")
        stdin, stdout, stderr = ssh.exec_command(restart_cmd_sudo)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("Deployment successful!")
    except Exception as e:
        print(f"Deployment failed: {e}")
    finally:
        ssh.close()
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="173.249.39.201", help="Target host IP or domain")
    parser.add_argument("--user", default="amakoni", help="SSH username")
    parser.add_argument("--remote-path", default="/home/demo1_havano_pro_cpsmddqqvbceafpdpqoknnae/custom-addons", help="Remote addons path")
    parser.add_argument("--restart-cmd", default="sudo docker restart odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae || sudo systemctl restart odoo", help="Command to restart Odoo")
    
    args = parser.parse_args()
    deploy(args.host, args.user, args.remote_path, args.restart_cmd)
