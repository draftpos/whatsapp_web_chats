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

        # Get only real errors (not the DEBUG lines wrongly logged as ERROR)
        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c "
            f"\"tail -n 300 /var/log/odoo/odoo.log | grep -v 'DEBUG unread' | grep -E '(ERROR|WARNING|Traceback|KeyError|attachment|preload|crm)' | tail -60\""
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        print(out if out else "No relevant errors found in last 300 lines.")

        # Also check the whatsapp attachment upload route in our custom module
        cmd2 = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c "
            f"\"grep -r 'send_attachment\\|attachment\\|upload' /mnt/extra-addons/whatsapp_web_chats/controllers/ 2>/dev/null | head -30\""
        )
        stdin, stdout, stderr = client.exec_command(cmd2, timeout=15)
        print("\n=== Custom attachment controller ===")
        print(stdout.read().decode('utf-8', 'ignore')[:2000] or "No controller found")

    finally:
        client.close()

if __name__ == '__main__':
    main()
