import paramiko

def main():
    host = '173.249.39.201'
    user = 'amakoni'
    password = 'Ashley@#$1234'
    db = 'supportwhatsapp_s4_havano_pro_yvnmgevazsj'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=30)
    
    script = f"""
echo '{password}' | sudo -S sh -c "
docker exec -i odoo_{db} odoo shell -c /etc/odoo/odoo.conf -d {db} --no-http << 'SHELL_EOF'
mod = env['ir.module.module'].search([('name', '=', 'whatsapp_web_chats')])
if mod:
    mod.button_immediate_upgrade()
    print('Upgraded whatsapp_web_chats successfully!')
else:
    print('Module not found!')
SHELL_EOF
"
"""
    print('Executing remote commands...')
    stdin, stdout, stderr = client.exec_command(script, timeout=600)
    out = stdout.read().decode('utf-8', 'ignore').strip()
    err = stderr.read().decode('utf-8', 'ignore').strip()
    print("Output:\n" + out)
    print("Err:\n" + err)
    client.close()

if __name__ == '__main__':
    main()
