import paramiko

HOST = '173.249.39.201'
USER = 'amakoni'
PASSWORD = 'Ashley@#$1234'
CONTAINER = 'odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae'

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        
        # 1. Get DB name
        cmd_db = f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} psql -U odoo -h db -d postgres -t -c \"SELECT datname FROM pg_database WHERE datistemplate = false AND datname != 'postgres' LIMIT 1;\""
        stdin, stdout, stderr = client.exec_command(cmd_db)
        db_name = stdout.read().decode('utf-8').strip()
        
        print(f"DB Name: {db_name}")
        
        # 2. Query whatsapp_message
        if db_name:
            query = "SELECT id, state, mobile_number, failure_type, failure_reason FROM whatsapp_message WHERE create_date >= CURRENT_DATE AND (mobile_number LIKE '%263771883091%' OR mobile_number LIKE '%0771883091%') ORDER BY id DESC LIMIT 10;"
            cmd_query = f"echo '{PASSWORD}' | sudo -S docker exec {CONTAINER} psql -U odoo -h db -d {db_name} -c \"{query}\""
            stdin, stdout, stderr = client.exec_command(cmd_query)
            print("Query Output:\n", stdout.read().decode('utf-8'))
            print("Query Stderr:\n", stderr.read().decode('utf-8'))
            
    finally:
        client.close()

if __name__ == '__main__':
    main()
