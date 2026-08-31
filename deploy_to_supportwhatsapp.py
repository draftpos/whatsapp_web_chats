import os
import zipfile
import paramiko

LOCAL_ADDON_DIR = r'C:\odoo19\addons\whatsapp_web_chats'
ZIP_PATH = r'C:\odoo19\addons\whatsapp_web_chats\addon_wa.zip'

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'supportwhatsapp_s4_havano_pro_yvnmgevazsj'
CONTAINER = f'odoo_{DB}'
REMOTE_PATH = f'/home/{DB}/custom-addons'

print("Zipping addon...")
with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(LOCAL_ADDON_DIR):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
        for file in files:
            if file.endswith('.pyc') or file in ('addon_wa.zip', 'addon.zip'):
                continue
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, start=os.path.dirname(LOCAL_ADDON_DIR))
            zipf.write(file_path, arcname)

print(f"Connecting to {HOST}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(HOST, port=22, username=USER, password=PASSWORD, timeout=15)

    print("Uploading zip...")
    sftp = ssh.open_sftp()
    sftp.put(ZIP_PATH, '/tmp/addon_wa.zip')
    sftp.close()

    print("Unzipping on server...")
    cmd = f"echo '{PASSWORD}' | sudo -S bash -c 'mv /tmp/addon_wa.zip {REMOTE_PATH}/addon.zip && cd {REMOTE_PATH} && unzip -o addon.zip && rm addon.zip'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())

    print("Restarting Odoo container...")
    restart_cmd = f"echo '{PASSWORD}' | sudo -S docker restart {CONTAINER}"
    stdin, stdout, stderr = ssh.exec_command(restart_cmd)
    print("STDOUT:", stdout.read().decode())
    print("STDERR:", stderr.read().decode())

    print("Deployment successful!")
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
