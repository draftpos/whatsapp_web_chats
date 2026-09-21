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
        # Get fresh logs since restart
        cmd = f"echo '{PASSWORD}' | sudo -S docker logs {CONTAINER} --tail 150 2>&1 | grep -E '(ERROR|Traceback|KeyError|AttributeError|File \"|failed|attachment|preload|crm)' | tail -60"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', 'ignore')
        print(out)
    finally:
        client.close()

if __name__ == '__main__':
    main()
