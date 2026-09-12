import paramiko
import time
import sys

def deploy_and_restart():
    host = "173.249.39.201"
    user = "amakoni"
    password = "Ashley@#$1234"
    remote_base = "/mnt/extra-addons/whatsapp_web_chats" # Assuming this is where it's mapped based on typical setup or we can find it
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to server...")
    try:
        ssh.connect(host, username=user, password=password, timeout=15)
        print("Connected!")
        
        commands = [
            f"cd {remote_base} && git pull origin master",
            "cd /home/demo1_havano_pro_pknuzuhckrvwadhoboithcke && docker compose restart"
        ]
        
        for cmd in commands:
            print(f"Executing: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            print("STDOUT:", stdout.read().decode())
            err = stderr.read().decode()
            if err:
                print("STDERR:", err)
            print(f"Exit status: {exit_status}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing connection...")
        ssh.close()

if __name__ == '__main__':
    deploy_and_restart()
