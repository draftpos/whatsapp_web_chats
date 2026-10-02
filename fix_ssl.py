import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    
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
        
    bash_script = """
cat << 'EOF' > /etc/nginx/sites-available/jlink.havano.pro.conf
upstream jlink.havano.pro {
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
EOF

nginx -t
systemctl reload nginx
sleep 2

certbot --nginx -d jlink.havano.pro --non-interactive --agree-tos -m amakoni@havano.pro --redirect
systemctl reload nginx
"""
    
    for line in bash_script.strip().split('\n'):
        if line.strip():
            channel.send(line + "\n")
            time.sleep(0.5)
            
    wait_for_prompt(channel, timeout=40)
    
    channel.send("exit\n")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
