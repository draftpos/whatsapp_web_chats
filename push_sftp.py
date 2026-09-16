import paramiko
import os
import sys

def run():
    host = "173.249.39.201"
    user = "amakoni"
    password = "Ashley@#$1234"
    container = "odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae"

    local_base = r"C:\odoo19\addons\whatsapp_web_chats"
    
    files = [
        (r"static\src\xml\chats_template.xml", "static/src/xml/chats_template.xml"),
    ]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {host}...")
    try:
        ssh.connect(host, username=user, password=password, timeout=15)
        sftp = ssh.open_sftp()
        print("Connected via SFTP!")

        for local_name, remote_name in files:
            local_path = os.path.join(local_base, local_name)
            tmp_path = "/tmp/" + os.path.basename(remote_name)
            
            if not os.path.exists(local_path):
                print("MISSING local file:", local_path)
                continue

            sftp.put(local_path, tmp_path)
            print("Uploaded to /tmp:", tmp_path)
            
            remote_dest = f"/mnt/extra-addons/whatsapp_web_chats/{remote_name}"
            cmd = f"sudo -S docker cp /tmp/{os.path.basename(remote_name)} {container}:{remote_dest}"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdin.write(password + '\n')
            stdin.flush()
            print(f"Copied {remote_name} into container!")
            
            # Remove tmp file on host
            ssh.exec_command(f"rm {tmp_path}")

        sftp.close()
        
        # Clear Assets
        print("Clearing Odoo Asset Bundles...")
        clear_cmd = (
            f"sudo -S docker exec {container} python3 -c \""
            "import psycopg2; "
            "conn = psycopg2.connect(dbname='demo1_havano_pro_cpsmddqqvbceafpdpqoknnae', user='odoo', password='odoo', host='db'); "
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

        print("Restarting Odoo...")
        stdin, stdout, stderr = ssh.exec_command(f"sudo -S docker restart {container}")
        stdin.write(password + '\n')
        stdin.flush()
        print(stdout.read().decode())
        
        print("\nSUCCESS!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    run()
