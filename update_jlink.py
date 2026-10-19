import paramiko

host = "173.249.39.201"
user = "amakoni"
password = "Ashley@#$1234"
container_name = "odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae"
repo_dir = "/home/jlink_havano_pro_cpsmddqqvbceafpdpqoknnae/custom-addons/whatsapp_web_chats"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("Connecting to", host)
ssh.connect(host, username=user, password=password, timeout=10)

commands = [
    f"cd {repo_dir} && sudo -S git fetch --all",
    f"cd {repo_dir} && sudo -S git reset --hard origin/dev",
    f"sudo -S docker exec {container_name} odoo -c /etc/odoo/odoo.conf -d jlink_havano_pro_cpsmddqqvbceafpdpqoknnae -u whatsapp_web_chats --stop-after-init --no-http",
    f"sudo -S docker restart {container_name}"
]

for cmd in commands:
    print("Running:", cmd)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdin.write(password + '\n')
    stdin.flush()
    exit_status = stdout.channel.recv_exit_status()
    print("Output:", stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("Error:", err)

ssh.close()
print("Done!")
