import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

db_name = 'jlink_havano_pro_cpsmddqqvbceafpdpqoknnae'
container_name = f'odoo_{db_name}'

print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    channel = ssh.invoke_shell()

    def wait_for_prompt(chan, timeout=20):
        buffer = ""
        start_time = time.time()
        while True:
            if chan.recv_ready():
                data = chan.recv(4096).decode('utf-8', errors='replace')
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

    print("\n=== Checking CRM module in jlink ===")
    
    python_script = """
crm_mod = env['ir.module.module'].search([('name', '=', 'crm')])
print(f'\\n--- CRM Module State: {crm_mod.state} ---')

if crm_mod.state == 'installed':
    crm_group = env.ref('sales_team.group_sale_salesman_all_leads', raise_if_not_found=False)
    
    if not crm_group:
        print("Error: CRM group 'sales_team.group_sale_salesman_all_leads' not found!")
    else:
        print('\\n--- Checking users ---')
        users = env['res.users'].search([('active', '=', True)])
        print(f'Found {len(users)} active users.')
        
        for u in users:
            is_admin = u.has_group('base.group_erp_manager')
            is_internal = u.has_group('base.group_user')
            
            if is_internal or is_admin:
                has_crm = u.has_group('sales_team.group_sale_salesman_all_leads')
                print(f"User: {u.login} (Admin: {is_admin}, Internal: {is_internal}) - Has CRM Access: {has_crm}")
                
                if not has_crm:
                    print(f"Granting CRM access to user {u.login} using SQL...")
                    env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (u.id, crm_group.id))
                    
        env.cr.commit()
        print('\\nFinished checking and updating.')
"""
    
    # Save script to container and run it
    channel.send(f"cat << 'EOF' > /tmp/check_crm.py\n{python_script}\nEOF\n")
    time.sleep(1)
    channel.send(f"docker cp /tmp/check_crm.py {container_name}:/tmp/check_crm.py\n")
    time.sleep(1)
    channel.send(f"docker exec -i {container_name} odoo shell -c /etc/odoo/odoo.conf -d {db_name} --no-http < /tmp/check_crm.py\n")
    
    time.sleep(15)
    wait_for_prompt(channel, timeout=30)

    channel.send("exit\n")
    print("\nDone!")

except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
