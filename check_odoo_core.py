import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        # Grep for 'template' or 'failure_type' in the standard whatsapp_message.py
        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} "
            f"grep -n -C 5 \"failure_type'?: 'template'\" /usr/lib/python3/dist-packages/odoo/addons/whatsapp/models/whatsapp_message.py"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', 'ignore')
        print(out)
    finally:
        client.close()

if __name__ == '__main__':
    main()
