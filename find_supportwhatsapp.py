import paramiko
import time
import sys

hostname = '173.249.39.201'
username = 'amakoni'
password = 'Ashley@#$1234'

# Target the supportwhatsapp instance
# We need to find the exact container/db name first
print(f"Connecting to {hostname}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname, username=username, password=password)
    channel = ssh.invoke_shell()

    def wait_for_prompt(chan, timeout=15):
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

    print("\n=== Finding supportwhatsapp containers ===")
    channel.send("docker ps | grep supportwhatsapp\n")
    time.sleep(3)
    out = wait_for_prompt(channel, timeout=10)

    channel.send("exit\n")

except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
