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

        # Find the odoo log file path
        cmd1 = f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /etc/odoo/odoo.conf | grep logfile'"
        stdin, stdout, stderr = client.exec_command(cmd1, timeout=15)
        logfile_line = stdout.read().decode().strip()
        print("Log config:", logfile_line)

        # Try to get recent errors from the log file
        # common log locations
        for logpath in ['/var/log/odoo/odoo.log', '/var/log/odoo.log', '/tmp/odoo.log']:
            cmd = f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'tail -n 100 {logpath} 2>/dev/null | grep -E \"(ERROR|attachment|preload|crm|KeyError|Traceback)\"'"
            stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
            out = stdout.read().decode('utf-8', 'ignore').strip()
            if out:
                print(f"\n=== Logs from {logpath} ===")
                print(out[:3000])
                break

        # Also check the whatsapp attachment upload controller
        cmd2 = f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'grep -r \"send_attachment\\|upload_attachment\\|Failed to send\" /usr/lib/python3/dist-packages/odoo/addons/whatsapp/ 2>/dev/null | head -20'"
        stdin, stdout, stderr = client.exec_command(cmd2, timeout=15)
        print("\n=== WhatsApp attachment controller ===")
        print(stdout.read().decode('utf-8', 'ignore')[:2000])

    finally:
        client.close()

if __name__ == '__main__':
    main()
