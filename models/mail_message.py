from odoo import models, api

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        
        for rec in records:
            if rec.model == 'wa.chatbot.session' and rec.res_id:
                try:
                    session = self.env['wa.chatbot.session'].sudo().browse(rec.res_id)
                    if session.exists():
                        WaMessage = self.env['whatsapp.message'].sudo()
                        if hasattr(WaMessage, '_find_or_create_discuss_channel'):
                            # Find or create the standard discuss.channel
                            channel = WaMessage._find_or_create_discuss_channel(
                                session.phone,
                                session.partner_id or False,
                                session.chatbot_id.account_id
                            )
                            if channel:
                                # Duplicate the message into the discuss.channel so operators can see it
                                # Use message_type 'whatsapp_message' so it's formatted correctly in Odoo
                                rec.sudo().copy({
                                    'model': 'discuss.channel',
                                    'res_id': channel.id,
                                    'message_type': 'whatsapp_message',
                                })
                except Exception:
                    # Fail silently if chatbot module is not installed or errors occur
                    pass

        return records
