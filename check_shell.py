
import datetime
today = datetime.datetime.now().date()
# We don't know the DB name, but it's the only DB in this container, probably 'demo1.havano.pro' or 'odoo'
import odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
db_name = odoo.tools.config['db_name']
if not db_name or db_name == 'False':
    import psycopg2
    conn = psycopg2.connect(host='db', user='odoo', password=odoo.tools.config['db_password'], dbname='postgres')
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    dbs = [r[0] for r in cur.fetchall() if r[0] != 'postgres']
    db_name = dbs[0]

registry = odoo.registry(db_name)
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    msgs = env['whatsapp.message'].search([
        '|', ('mobile_number', 'ilike', '263771883091'), ('mobile_number', 'ilike', '0771883091'),
        ('create_date', '>=', str(today))
    ], order='id desc', limit=10)
    print(f"DB: {db_name} | Found {len(msgs)} messages.")
    for msg in msgs:
        fail_reason = getattr(msg, 'failure_reason', '')
        error_code = getattr(msg, 'failure_type', '')
        print(f"ID={msg.id} | State={msg.state} | Type={msg.message_type} | Error={error_code} : {fail_reason}")
        