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
        sftp.put(r'c:\odoo19\addons\whatsapp_web_chats\check_docker_logs.py', '/tmp/test_counts.py')
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/test_counts.py {CONTAINER}:/tmp/test_counts.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} python3 /tmp/test_counts.py"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
        output = stdout.read().decode('utf-8')
        err_output = stderr.read().decode('utf-8')
        print(output)
        if err_output:
            print("STDERR:")
            print(err_output)
    finally:
        client.close()

if __name__ == '__main__':
    main()
