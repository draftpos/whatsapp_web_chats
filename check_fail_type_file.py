import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
DB = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

ODOO_SCRIPT = """
msgs = env['whatsapp.message'].sudo().browse([7015, 7014, 7013])
with open('/tmp/fail_out.txt', 'w') as f:
    for msg in msgs:
        ft = getattr(msg, 'failure_type', 'N/A')
        fr = getattr(msg, 'failure_reason', 'N/A')
        f.write(f"ID: {msg.id} | FT: {ft} | FR: {fr}\\n")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        sftp = client.open_sftp()
        with sftp.file('/tmp/check_fail_type.py', 'w') as f:
            f.write(ODOO_SCRIPT)
        sftp.close()

        cmd = (
            f"echo '{PASSWORD}' | sudo -S docker cp /tmp/check_fail_type.py {CONTAINER}:/tmp/check_fail_type.py && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} bash -c 'cat /tmp/check_fail_type.py | /usr/bin/odoo shell -d {DB} --no-http' && "
            f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} cat /tmp/fail_out.txt"
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        print("STDOUT:", stdout.read().decode('utf-8', 'ignore'))
        print("STDERR:", stderr.read().decode('utf-8', 'ignore'))
    finally:
        client.close()

if __name__ == '__main__':
    main()
