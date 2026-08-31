import paramiko

def main():
    host = '173.249.39.201'
    user = 'amakoni'
    password = 'Ashley@#$1234'
    
    db_name = 'bestbeginnings_s2_havano_pro_nyyrglzxjnfn'
    container = 'odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)
    
    shell_cmd = """docker exec -i odoo_bestbeginnings_s2_havano_pro_nyyrglzxjnfn odoo shell -c /etc/odoo/odoo.conf -d bestbeginnings_s2_havano_pro_nyyrglzxjnfn --no-http << 'SHELL_EOF'
print("Recreating ALL Admin Rules with Multi-Company support...")

domain = "['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]"
group_admin = env.ref('havano_schools_odoo.group_havano_admin')

models_to_fix = [
    ('havano.class', 'Admin Rule for Classes'),
    ('havano.section', 'Admin Rule for Sections'),
    ('havano.subject', 'Admin Rule for Subjects'),
    ('havano.parent', 'Admin Rule for Parents'),
    ('havano.student.disciplinary', 'Admin Rule for Student Disciplinary'),
    ('havano.take.register', 'Admin Rule for Take Register'),
    ('havano.book.issue', 'Admin Rule for Book Issue'),
    ('havano.marksheet.line', 'Admin Rule for Marksheet Line')
]

for model_name, rule_name in models_to_fix:
    model_obj = env.ref('havano_schools_odoo.model_' + model_name.replace('.', '_'))
    rule = env['ir.rule'].search([('name', '=', rule_name)])
    if not rule:
        env['ir.rule'].create({
            'name': rule_name,
            'model_id': model_obj.id,
            'groups': [(4, group_admin.id)],
            'domain_force': domain,
        })
        print("Created " + rule_name)
    else:
        rule.write({'domain_force': domain})
        print("Updated " + rule_name)

env.cr.commit()
print("Successfully fixed all multi-company filtering for Admin!")
SHELL_EOF
"""

    sftp = client.open_sftp()
    with sftp.file('/home/amakoni/fix_all_admin_rules.sh', 'w') as f:
        f.write(shell_cmd)
    sftp.close()
    
    cmd = "echo 'Ashley@#$1234' | sudo -S bash /home/amakoni/fix_all_admin_rules.sh"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print("Stdout:\n", stdout.read().decode('utf-8', 'ignore'))
    print("Stderr:\n", stderr.read().decode('utf-8', 'ignore'))

    client.close()

if __name__ == '__main__':
    main()
