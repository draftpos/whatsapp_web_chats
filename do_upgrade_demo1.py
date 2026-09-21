import paramiko
import sys

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"/usr/bin/odoo -d {DB} -u whatsapp_web_chats --stop-after-init --no-http"
        )
        print("Running upgrade command on demo1...")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
        
        # Stream the output so we can see it in real-time or just wait
        for line in stdout:
            print(line, end='')
        for line in stderr:
            print(line, end='')

        print("\nUpgrade complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    main()
