import paramiko
import sys

def main():
    host = '173.249.39.201'
    user = 'amakoni'
    password = 'Ashley@#$1234'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)
    
    cmd = "echo 'Ashley@#$1234' | sudo -S sh -c 'cd /home/bestbeginnings_s2_havano_pro_nyyrglzxjnfn/custom-addons/havano_schools_odoo && git pull origin main && docker restart odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn && docker exec odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn odoo -u havano_schools_odoo -d bestbeginnings_s2_havano_pro_nyyrglzxjnfn --stop-after-init'"
    print("Running upgrade... (this may take 5-10 minutes)")
    
    # Increase timeout to 15 minutes (900 seconds)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=900)
    
    # Stream the output
    for line in stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

    for line in stderr:
        sys.stderr.write(line)
        sys.stderr.flush()
        
    client.close()

if __name__ == '__main__':
    main()
