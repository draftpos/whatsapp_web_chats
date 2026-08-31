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
        password = "Ashley@#$1234"
    password = password.strip()

    print("Zipping addon...")
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(LOCAL_ADDON_DIR):
            if '.git' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith('.pyc') or file == 'addon.zip':
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=os.path.dirname(LOCAL_ADDON_DIR))
                zipf.write(file_path, arcname)

    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, port=22, username=user, password=password, timeout=15)
        
        print(f"Uploading zip file to /tmp/addon_wa.zip...")
        sftp = ssh.open_sftp()
        sftp.put(ZIP_PATH, f"/tmp/addon_wa.zip")
        sftp.close()

        print("Unzipping on server...")
        cmd = f"echo '{password}' | sudo -S bash -c 'mv /tmp/addon_wa.zip {remote_path}/addon.zip && cd {remote_path} && unzip -o addon.zip && rm addon.zip'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())

        print("Updating module in Odoo...")
        update_cmd = "echo 'Ashley@#$1234' | sudo -S docker exec odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn odoo -c /etc/odoo/odoo.conf -d bestbeginnings_s2_havano_pro_nyyrglzxjnfn -u whatsapp_web_chats --stop-after-init --http-port=8079"
        stdin, stdout, stderr = ssh.exec_command(update_cmd)
        print("Update OUT:", stdout.read().decode())
        print("Update ERR:", stderr.read().decode())

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
    parser.add_argument("--remote-path", default="/home/bestbeginnings_s2_havano_pro_nyyrglzxjnfn/custom-addons", help="Remote addons path")
    parser.add_argument("--restart-cmd", default="sudo docker restart odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn", help="Command to restart Odoo")
    
    args = parser.parse_args()
    deploy(args.host, args.user, args.remote_path, args.restart_cmd)
