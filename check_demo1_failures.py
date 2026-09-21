import os
import sys

def main():
    import odoo
    odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
    registry = odoo.registry('demo1')
    
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        print("Checking messages for 263771883091 or 0771883091 created today...")
        
        import datetime
        today = datetime.datetime.now().date()
        
        msgs = env['whatsapp.message'].search([
            '|', ('mobile_number', 'ilike', '263771883091'), ('mobile_number', 'ilike', '0771883091'),
            ('create_date', '>=', str(today))
        ], order='id desc')
        
        print(f"Found {len(msgs)} messages.")
        for msg in msgs:
            fail_reason = getattr(msg, 'failure_reason', '')
            error_code = getattr(msg, 'failure_type', '')
            print(f"ID={msg.id} | State={msg.state} | Type={msg.message_type} | Template={msg.wa_template_id.name if msg.wa_template_id else 'None'} | Error={error_code} : {fail_reason}")
            print(f"   Body snippet: {str(msg.body)[:50] if msg.body else 'None'}")
            print(f"   Has Attachment: {bool(msg.mail_message_id.attachment_ids)}")

if __name__ == '__main__':
    main()
