import paramiko
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('173.249.39.201', username='amakoni', password='Ashley@#$1234')
    cmd = "echo 'Ashley@#$1234' | sudo -S tail -n 100 /var/log/nginx/access.log | grep -i whatsapp"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read()
    err = stderr.read()
    sys.stdout.buffer.write(out)
    sys.stderr.buffer.write(err)
finally:
    client.close()
