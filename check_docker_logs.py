import odoo
import sys

def main():
    odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf'])
    registry = odoo.registry('demo1')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        wa_model = env['whatsapp.account']
        try:
            print("Testing get_whatsapp_web_channel_counts...")
            res = wa_model.get_whatsapp_web_channel_counts()
            print("Success:", res)
        except Exception as e:
            print("Failed:", e)

if __name__ == '__main__':
    main()
