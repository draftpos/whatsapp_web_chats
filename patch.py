import re

with open(r'c:\odoo19\addons\whatsapp_web_chats\models\whatsapp_account.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace _send_bot_reply to not use interactive
new_send_bot = """    def _send_bot_reply(self, channel, body_text):
        try:
            # Post the message in the discuss channel
            mail_msg = channel.sudo().message_post(
                body=body_text,
                message_type='whatsapp_message',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.ref('base.partner_root').id,
            )
            
            # Send via whatsapp api natively
            phone = channel.whatsapp_number or (channel.whatsapp_partner_id and channel.whatsapp_partner_id.phone)
            if phone:
                wa_msg = self.env['whatsapp.message'].sudo().create({
                    'mobile_number': phone,
                    'wa_account_id': channel.wa_account_id.id,
                    'mail_message_id': mail_msg.id,
                    'state': 'outgoing',
                    'message_type': 'outbound',
                    'body': body_text,
                })
                wa_msg._send(force_send_by_cron=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Failed to send bot reply: %s", e)

    @api.model
    def delete_whatsapp_chat"""

c = re.sub(r'    def _send_bot_reply\(self, channel, body_text.*?(?=    @api\.model\n    def delete_whatsapp_chat)', new_send_bot, c, flags=re.DOTALL)

# Remove interactive payloads from calls
c = re.sub(r'interactive_payload=interactive_payload\)', ')', c)
c = re.sub(r', interactive_payload=interactive_payload', '', c)
c = re.sub(r'interactive_payload\s*=\s*\{[^\}]+\}\s+', '', c, flags=re.DOTALL)

# Wait, the interactive_payload dict has nested braces! Regex won't easily replace it, but I can just leave it as an unused variable.

with open(r'c:\odoo19\addons\whatsapp_web_chats\models\whatsapp_account.py', 'w', encoding='utf-8') as f:
    f.write(c)
