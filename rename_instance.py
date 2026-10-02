import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    print("Connected successfully. Requesting sudo session...")
    
    channel = ssh.invoke_shell()
    
    def wait_for_prompt(chan, timeout=10):
        buffer = ""
        start_time = time.time()
        while True:
            if chan.recv_ready():
                data = chan.recv(4096).decode('utf-8')
                buffer += data
                sys.stdout.write(data)
                sys.stdout.flush()
                if "password for" in buffer.lower() or "#" in buffer or "$" in buffer:
                    return buffer
            if time.time() - start_time > timeout:
                return buffer
            time.sleep(0.5)

    wait_for_prompt(channel)
    channel.send("sudo -i\n")
    out = wait_for_prompt(channel)
    if "password for" in out.lower():
        channel.send(password + "\n")
        wait_for_prompt(channel)
        
    print("\nRunning rename commands...")
    
    bash_script = """
OLD="demo1_havano_pro_cpsmddqqvbceafpdpqoknnae"
NEW="jlink_havano_pro_cpsmddqqvbceafpdpqoknnae"
OLD_DOMAIN="demo1.havano.pro"
NEW_DOMAIN="jlink.havano.pro"

echo "Stopping containers..."
cd /home/$OLD
docker compose down

echo "Renaming directory..."
cd /home
mv $OLD $NEW
cd /home/$NEW

echo "Updating docker-compose.yml..."
sed -i "s/$OLD/$NEW/g" docker-compose.yml

echo "Starting Postgres..."
docker compose up -d db
sleep 10

echo "Renaming database in Postgres..."
docker exec psql_$NEW psql -U Showline -d postgres -c "ALTER DATABASE $OLD RENAME TO $NEW;"

echo "Starting Odoo web container..."
docker compose up -d web

echo "Updating Nginx configuration..."
if [ -f /etc/nginx/sites-available/$OLD_DOMAIN.conf ]; then
    mv /etc/nginx/sites-available/$OLD_DOMAIN.conf /etc/nginx/sites-available/$NEW_DOMAIN.conf
    rm -f /etc/nginx/sites-enabled/$OLD_DOMAIN.conf
    ln -s /etc/nginx/sites-available/$NEW_DOMAIN.conf /etc/nginx/sites-enabled/$NEW_DOMAIN.conf
elif [ -f /etc/nginx/sites-enabled/$OLD_DOMAIN.conf ]; then
    mv /etc/nginx/sites-enabled/$OLD_DOMAIN.conf /etc/nginx/sites-enabled/$NEW_DOMAIN.conf
fi

if [ -f /etc/nginx/sites-enabled/$NEW_DOMAIN.conf ]; then
    sed -i "s/$OLD_DOMAIN/$NEW_DOMAIN/g" /etc/nginx/sites-enabled/$NEW_DOMAIN.conf
    sed -i "s/demo1/jlink/g" /etc/nginx/sites-enabled/$NEW_DOMAIN.conf
fi

echo "Testing and Reloading Nginx..."
nginx -t
systemctl reload nginx
"""
    
    for line in bash_script.strip().split('\n'):
        if line.strip():
            channel.send(line + "\n")
            time.sleep(1)
            
    wait_for_prompt(channel, timeout=30)
    
    channel.send("exit\n")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
