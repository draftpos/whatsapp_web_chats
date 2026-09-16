import paramiko

def run():
    host = "173.249.39.201"
    user = "amakoni"
    password = "Ashley@#$1234"
    container = "odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae"
    db = "demo1_havano_pro_cpsmddqqvbceafpdpqoknnae"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {host}...")
    try:
        ssh.connect(host, username=user, password=password, timeout=15)
        
        # 1. Pull the latest code in the container
        print("Pulling latest code from Github...")
        cmd_pull = f"sudo -S docker exec {container} bash -c 'cd /mnt/extra-addons/whatsapp_web_chats && git pull'"
        stdin, stdout, stderr = ssh.exec_command(cmd_pull)
        stdin.write(password + '\n')
        stdin.flush()
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 2. Clear Asset Bundles
        print("Clearing Odoo Asset Bundles...")
        clear_cmd = (
            f"sudo -S docker exec {container} python3 -c \""
            "import psycopg2; "
            f"conn = psycopg2.connect(dbname='{db}', user='odoo', password='odoo', host='db'); "
            "cur = conn.cursor(); "
            "cur.execute(\\\"DELETE FROM ir_attachment WHERE name LIKE '%web.assets%'\\\"); "
            "conn.commit(); "
            "conn.close()\""
        )
        stdin, stdout, stderr = ssh.exec_command(clear_cmd)
        stdin.write(password + '\n')
        stdin.flush()
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. Restart Odoo container
        print("Restarting Odoo...")
        stdin, stdout, stderr = ssh.exec_command(f"sudo -S docker restart {container}")
        stdin.write(password + '\n')
        stdin.flush()
        print(stdout.read().decode())
        
        print("\nSUCCESS! Please hard-refresh your browser (Ctrl+Shift+R) and try uploading the video again!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    run()
