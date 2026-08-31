import paramiko

def main():
    host = '173.249.39.201'
    user = 'amakoni'
    password = 'Ashley@#$1234'
    
    db = 'bestbeginnings_s2_havano_pro_nyyrglzxjnfn'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to server...")
    client.connect(host, username=user, password=password, timeout=15)
    
    print("Installing module...")
    # Use -i to install instead of -u
    cmd = f"echo '{password}' | sudo -S docker exec odoo_{db} odoo -i havano_schools_odoo -d {db} --stop-after-init"
    
    stdin, stdout, stderr = client.exec_command(cmd)
    
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    print("Err:\n" + stderr.read().decode('utf-8', 'ignore'))
    client.close()
    print('Done.')

if __name__ == '__main__':
    main()
