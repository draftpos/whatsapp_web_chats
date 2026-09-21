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
        sftp = client.open_sftp()
        sftp.put('c:\\odoo19\\addons\\whatsapp_web_chats\\check_demo1_failures.py', '/tmp/check_demo1_failures.py')
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_demo1_failures.py {CONTAINER}:/tmp/check_demo1_failures.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec -u root {CONTAINER} chown odoo:odoo /tmp/check_demo1_failures.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec -u odoo {CONTAINER} python3 /tmp/check_demo1_failures.py"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("Stdout:", stdout.read().decode('utf-8'))
        print("Stderr:", stderr.read().decode('utf-8'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
