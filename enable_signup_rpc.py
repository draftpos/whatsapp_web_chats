import xmlrpc.client

url = 'https://demo1.havano.pro'
db = 'demo1_havano_pro'
username = 'admin'
password = '123'

try:
    print(f"Connecting to {url}...")
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        # try demo1_havano_pro
        print("Failed with long db name, trying short db name...")
        db = 'demo1_havano_pro'
        uid = common.authenticate(db, username, password, {})
        
    if uid:
        print(f"Authenticated as uid: {uid}")
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        
        param_ids = models.execute_kw(db, uid, password,
            'ir.config_parameter', 'search',
            [[['key', '=', 'auth_signup.invitation_scope']]])
            
        if param_ids:
            print("Updating existing parameter...")
            models.execute_kw(db, uid, password,
                'ir.config_parameter', 'write',
                [param_ids, {'value': 'b2c'}])
        else:
            print("Creating new parameter...")
            models.execute_kw(db, uid, password,
                'ir.config_parameter', 'create',
                [{'key': 'auth_signup.invitation_scope', 'value': 'b2c'}])
                
        print("Success! Free sign up is enabled.")
    else:
        print("Authentication failed.")
        
except Exception as e:
    print(f"Error: {e}")
