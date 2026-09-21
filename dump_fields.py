import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
fields = env['whatsapp.message'].fields_get()
with open('/tmp/fields.txt', 'w') as f:
    for fname in fields.keys():
        f.write(fname + '\\n')
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/dump_fields.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/dump_fields.py {CONTAINER}:/tmp/dump_fields.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/dump_fields.py | /usr/bin/odoo shell -d {DB} --no-http' && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} cat /tmp/fields.txt"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("STDOUT:", stdout.read().decode('utf-8', 'ignore'))
        print("STDERR:", stderr.read().decode('utf-8', 'ignore'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
