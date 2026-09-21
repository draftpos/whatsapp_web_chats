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

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c "
            f"\"grep -rn 'Failed to send attachment' /usr/lib/python3/dist-packages/odoo/addons/\""
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
        out = stdout.read().decode('utf-8', 'ignore').strip()
        print(out if out else "No matches found")
    finally:
        client.close()

if __name__ == '__main__':
    main()
