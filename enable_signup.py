import paramiko
import time
import sys

def enable_signup():
    host = "161.97.114.200"
    user = "root"
    password = "Farai@#$1234"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to server...")
    try:
        # We know from fetch_logs the other IP was timing out, but the docker logs script had 173... wait
        # Ah! Earlier I used 173.249.39.201 with amakoni. Let me use that since it worked.
        ssh.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234', timeout=15)
        print("Connected!")
        
        # We need to run odoo shell in the container
        # Container name: odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae
        # DB name: demo1_havano_pro_pknuzuhckrvwadhoboithcke (or we can just guess from container name usually it's the db name)
        # Wait, what is the DB name?
        pass
    except Exception as e:
        print(e)

