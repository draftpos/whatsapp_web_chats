import ast

env = odoo.api.Environment(odoo.registry(db).cursor(), 1, {})
msgs = env['whatsapp.message'].search([('wa_template_id', '!=', False)])
count = 0
for m in msgs:
    if '[SaaS Template Sent:' in m.body or 'WhatsApp Template Sent:' in m.body:
        rendered = m.wa_template_id.body or ''
        if m.free_text_json:
            try:
                ft = ast.literal_eval(m.free_text_json) if isinstance(m.free_text_json, str) else m.free_text_json
                for i in range(1, 10):
                    val = ft.get(f'free_text_{i}')
                    if val:
                        rendered = rendered.replace(f'{{{{{i}}}}}', str(val))
            except:
                pass
        
        ui_body = f"<strong>WhatsApp Template Sent:</strong><br/><br/>{rendered.replace(chr(10), '<br/>')}"
        m.body = ui_body
        if m.mail_message_id:
            m.mail_message_id.body = ui_body
            m.mail_message_id.subtype_id = env.ref('mail.mt_comment').id
            m.mail_message_id.message_type = 'comment'
        count += 1

env.cr.commit()
print(f'Updated {count} existing messages to be regular chat messages instead of notifications.')
