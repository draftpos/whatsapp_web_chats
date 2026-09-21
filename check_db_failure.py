import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        cmd = f"echo '{PASSWORD}' | sudo -S docker exec odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae psql -U odoo -d demo1_havano_pro_cpsmddqqvbceafpdpqoknnae -c 'SELECT id, state, failure_type, failure_reason FROM whatsapp_message WHERE id IN (7015, 7014, 7013);'"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode('utf-8', 'ignore')
        print(out)
    finally:
        client.close()

if __name__ == '__main__':
    main()
