import paramiko
import time
import sys
import base64

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    
    nginx_conf = """upstream jlink.havano.pro {
    server 173.249.39.201:9057 weight=1 max_fails=5 fail_timeout=10s;
}

server {
    listen 80;
    server_name jlink.havano.pro;
    access_log /var/log/nginx/access_jlink.havano.pro.log combined;
    error_log /var/log/nginx/error_jlink.havano.pro.log;
    client_max_body_size 200m;
    keepalive_timeout 600;
    proxy_buffers 16 64k;
    proxy_buffer_size 128k;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;

    location / {
        proxy_pass http://jlink.havano.pro;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }

    location /websocket {
        proxy_pass http://127.0.0.1:9059;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }

    location ~* /web/static {
        proxy_cache_valid 200 120m;
        proxy_buffering on;
        expires 14d;
        proxy_pass http://jlink.havano.pro;
    }
}
"""
    b64_conf = base64.b64encode(nginx_conf.encode('utf-8')).decode('utf-8')
    
    cmd_script = f"""
echo "{b64_conf}" | base64 -d > /etc/nginx/sites-available/jlink.havano.pro.conf
nginx -t
systemctl reload nginx
sleep 2
certbot --nginx -d jlink.havano.pro --non-interactive --agree-tos -m amakoni@havano.pro --redirect
systemctl reload nginx
"""
    
    # We use exec_command to avoid TTY autocomplete issues entirely.
    stdin, stdout, stderr = ssh.exec_command('sudo -S bash')
    stdin.write(password + '\n')
    stdin.write(cmd_script)
    stdin.flush()
    stdin.channel.shutdown_write()
    
    print("OUTPUT:")
    print(stdout.read().decode())
    print("ERRORS:")
    print(stderr.read().decode())
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
