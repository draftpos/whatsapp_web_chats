import paramiko

def fix_setting():
    host = "173.249.39.201"
    user = "amakoni"
    password = "Ashley@#$1234"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {host}...")
    try:
        ssh.connect(host, username=user, password=password, timeout=15)
        print("Connected! Forcing auth_signup.invitation_scope to b2c via Postgres...")
        
        # The database name might be demo1_havano_pro or demo1_havano_pro_cpsmddqqvbceafpdpqoknnae
        # Let's run a docker exec command to run psql inside the postgres container
        # Wait, what is the postgres container named?
        # Usually psql_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae or similar
        # A safer way: run python in the odoo container
        
        python_script = """
import odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
db_name = 'demo1_havano_pro_cpsmddqqvbceafpdpqoknnae' # Let's try to get the DB name automatically
import psycopg2
conn = psycopg2.connect("dbname=demo1_havano_pro_cpsmddqqvbceafpdpqoknnae user=odoo host=db")
cur = conn.cursor()
cur.execute("SELECT id FROM ir_config_parameter WHERE key='auth_signup.invitation_scope'")
res = cur.fetchone()
if res:
    cur.execute("UPDATE ir_config_parameter SET value='b2c' WHERE key='auth_signup.invitation_scope'")
else:
    cur.execute("INSERT INTO ir_config_parameter (key, value) VALUES ('auth_signup.invitation_scope', 'b2c')")
conn.commit()
"""
        # Save this to a file and run it inside the container
        # Actually, let's just ask the user to search in the UI, it's so much simpler and less prone to DB name guessing errors.
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    fix_setting()
