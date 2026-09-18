# Run this script using odoo-bin shell on the server
# Command:
# sudo docker exec -i odoo_demo1_havano_pro_cpsmddqqvbceafpdpqoknnae odoo-bin shell -d demo1_havano_pro_cpsmddqqvbceafpdpqoknnae < fix_messages.py

# In odoo shell, 'env' is already available!
admin_partner = env.ref('base.partner_admin')

print("Searching for group link messages...")
messages = env['mail.message'].search([('body', 'ilike', '%chat.whatsapp.com%')])
count = 0

for msg in messages:
    if msg.author_id.id != admin_partner.id:
        msg.write({'author_id': admin_partner.id})
        count += 1
        
print(f"Updated {count} mail messages to appear as sent by Admin.")

wa_messages = env['whatsapp.message'].search([('mail_message_id', 'in', messages.ids)])
wa_count = 0
for wa in wa_messages:
    if wa.state != 'sent' and wa.state != 'delivered' and wa.state != 'read':
        wa.write({'state': 'sent'})
        wa_count += 1

print(f"Updated {wa_count} whatsapp messages to 'sent' state.")
env.cr.commit()
print("Done!")
