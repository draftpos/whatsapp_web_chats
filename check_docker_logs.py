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
        # Fetch logs, looking for whatsapp error logs
        cmd = f"echo '{PASSWORD}' | sudo -S docker logs {CONTAINER} --tail 2000 | grep -iE 'whatsapp|error|traceback' | tail -n 100"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', 'ignore')
        print(out)
    finally:
        client.close()

if __name__ == '__main__':
    main()
