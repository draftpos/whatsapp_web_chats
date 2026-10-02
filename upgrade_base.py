import paramiko
import time

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
                data = chan.recv(4096).decode('utf-8', errors='ignore')
                buffer += data
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
        
    shell_script = """
import logging
_logger = logging.getLogger(__name__)

menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('web_icon', '!=', False)])
for menu in menus:
    try:
        if menu.web_icon and len(menu.web_icon.split(',')) == 2:
            data = menu._compute_web_icon_data(menu.web_icon)
            if data:
                menu.web_icon_data = data
                print(f"Fixed {menu.name}")
            else:
                print(f"Could not compute data for {menu.name}")
    except Exception as e:
        print(f"Error on {menu.name}: {e}")
env.cr.commit()
"""
    
    channel.send("docker exec -i odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae odoo shell -c /etc/odoo/odoo.conf -d jlink_havano_pro_cpsmddqqvbceafpdpqoknnae --no-http\n")
    time.sleep(5)
    
    channel.send(shell_script + "\n")
    time.sleep(2)
    
    channel.send("exit()\n")
    time.sleep(2)
    
    out = wait_for_prompt(channel, timeout=30)
    print("OUTPUT:")
    print(out.replace('\r', ''))
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
