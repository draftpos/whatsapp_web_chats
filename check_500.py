import paramiko

def main():
    host = '173.249.39.201'
    user = 'amakoni'
    password = 'Ashley@#$1234'
    db = 'nadias_s4_havano_pro_qrmeqxutyzvhwwupoxju'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=30)
    
    script = f"""
echo '{password}' | sudo -S sh -c "
docker logs odoo_{db} | grep -i '500' -A 20 | tail -n 60
"
"""
    print('Executing remote commands...')
    stdin, stdout, stderr = client.exec_command(script, timeout=600)
    out = stdout.read().decode('utf-8', 'ignore').strip()
    err = stderr.read().decode('utf-8', 'ignore').strip()
    print("Output:\n" + out)
    print("Err:\n" + err)
    client.close()

if __name__ == '__main__':
    main()
