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

        # Search for sendAttachment in core Odoo WhatsApp JS
        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c "
            f"\"grep -r 'send_attachment\\|sendAttachment\\|Failed to send attachment' /usr/lib/python3/dist-packages/odoo/ 2>/dev/null | grep -v '.pyc' | head -20\""
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        print("Core Odoo attachment references:\n", out[:3000] if out else "None found")

        # Also grep mnt/extra-addons for any overrides
        cmd2 = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c "
            f"\"grep -r 'send_attachment\\|sendAttachment' /mnt/extra-addons/ 2>/dev/null | grep -v '.pyc' | head -20\""
        )
        stdin, stdout, stderr = client.exec_command(cmd2, timeout=20)
        out2 = stdout.read().decode('utf-8', 'ignore').strip()
        print("\nCustom addon attachment references:\n", out2[:3000] if out2 else "None found")

    finally:
        client.close()

if __name__ == '__main__':
    main()
