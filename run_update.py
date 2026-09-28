import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('173.249.39.201', username='amakoni', password='Hav@n0$upport', timeout=10)

shell = ssh.invoke_shell()
def read_output(delay=2.0):
    time.sleep(delay)
    if shell.recv_ready():
        return shell.recv(65535).decode('utf-8')
    return ""

shell.send("cd /home/supportwhatsapp_s4_havano_pro_yvnmgevazsj/custom-addons/whatsapp_web_chats && git fetch --all && git reset --hard origin/master\n")
print(read_output(3))

shell.send("docker exec -i odoo_supportwhatsapp_s4_havano_pro_yvnmgevazsj odoo shell -c /etc/odoo/odoo.conf -d supportwhatsapp_s4_havano_pro_yvnmgevazsj --no-http < /home/supportwhatsapp_s4_havano_pro_yvnmgevazsj/custom-addons/whatsapp_web_chats/update_msgs.py\n")
print(read_output(10))

ssh.close()
