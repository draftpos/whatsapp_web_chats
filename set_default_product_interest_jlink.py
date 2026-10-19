import paramiko

host = "173.249.39.201"
user = "amakoni"
password = "Ashley@#$1234"
container_name = "odoo_jlink_havano_pro_cpsmddqqvbceafpdpqoknnae"
db = "jlink_havano_pro_cpsmddqqvbceafpdpqoknnae"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f"Connecting to {user}@{host}...")
ssh.connect(host, username=user, password=password, timeout=20)
print("Connected!")

script = """
# 1. Determine comodel and find 'Other'
lead_field = env['crm.lead']._fields.get('crm_product_id')
rel_model = lead_field.comodel_name if lead_field else 'product.template'
print(f"crm_product_id comodel: {rel_model}")

other_rec = env[rel_model].search([('name', 'ilike', 'Other')], limit=1)
if not other_rec:
    # Try searching for Other without strict case or check all records
    records = env[rel_model].search([])
    print("Available product interests:")
    for r in records:
        print(f"  ID: {r.id}, Name: {r.display_name}")
    other_rec = env[rel_model].search([('name', '=', 'Other')], limit=1)
    if not other_rec and records:
        for r in records:
            if 'other' in (r.name or '').lower():
                other_rec = r
                break

if not other_rec:
    print("ERROR: Could not find 'Other' product interest record!")
else:
    print(f"Found 'Other' record: ID={other_rec.id}, Name={other_rec.display_name}")

    # 2. Set 'Other' as the default for FUTURE leads in ir.default
    field_id = env['ir.model.fields'].search([('model', '=', 'crm.lead'), ('name', '=', 'crm_product_id')], limit=1)
    if field_id:
        existing_default = env['ir.default'].search([('field_id', '=', field_id.id)])
        if existing_default:
            existing_default.write({'json_value': str(other_rec.id)})
            print(f"Updated ir.default for crm.lead.crm_product_id to {other_rec.id}")
        else:
            env['ir.default'].set('crm.lead', 'crm_product_id', other_rec.id)
            print(f"Created ir.default for crm.lead.crm_product_id with value {other_rec.id}")
    else:
        print("Warning: crm_product_id field record not found in ir.model.fields")

    # 3. Update ALL existing leads
    all_leads = env['crm.lead'].search([])
    leads_to_update = env['crm.lead'].search(['|', ('crm_product_id', '=', False), ('crm_product_id', '!=', other_rec.id)])
    print(f"Total leads: {len(all_leads)} | Leads needing update: {len(leads_to_update)}")
    
    leads_to_update.write({'crm_product_id': other_rec.id})
    env.cr.commit()
    print(f"Successfully updated {len(leads_to_update)} leads to 'Other'!")

    # 4. Verify sample
    sample = env['crm.lead'].search([], order='id desc', limit=5)
    print("\\nSample of 5 recent leads:")
    for l in sample:
        prod_name = l.crm_product_id.display_name if l.crm_product_id else 'None'
        print(f"ID: {l.id} | Name: {l.name} | Product Interest: {prod_name}")
"""

cmd = f"sudo -S docker exec -i {container_name} odoo shell -c /etc/odoo/odoo.conf -d {db} --http-port=8099"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdin.write(password + '\n')
stdin.flush()
stdin.write(script)
stdin.flush()
stdin.close()

out = stdout.read().decode('utf-8', errors='replace')
print("Output:\n", out.encode('ascii', errors='replace').decode('ascii'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print("Stderr:\n", err[-500:].encode('ascii', errors='replace').decode('ascii'))

ssh.close()
