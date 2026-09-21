import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

        # Get last 200 lines, filter for real errors only
        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c "
            f"\"tail -n 200 /var/log/odoo/odoo.log | grep -v 'DEBUG unread' | grep -v 'get_whatsapp_web_channels'\""
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        print(out if out else "No recent log lines found")
    finally:
        client.close()

if __name__ == '__main__':
    main()
