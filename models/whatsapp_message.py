from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.mail_message_id:
                # Find the copied discuss.channel message
                copied_msg = self.env['mail.message'].sudo().search([
                    ('model', '=', 'discuss.channel'),
                    ('message_type', '=', 'whatsapp_message'),
                    ('body', '=', rec.mail_message_id.body),
                    ('res_id', '!=', False)
                ], order='id desc', limit=1)
                
                if copied_msg:
                    new_author_id = copied_msg.author_id.id
                    if rec.message_type == 'inbound':
                        # Customer message (should be left)
                        session = self.env['wa.chatbot.session'].sudo().search([('id', '=', rec.chatbot_session_id.id)], limit=1) if hasattr(rec, 'chatbot_session_id') else False
                        if session and session.partner_id:
                            new_author_id = session.partner_id.id
                        else:
                            # Try to find the partner from the whatsapp_number
                            channel = self.env['discuss.channel'].sudo().browse(copied_msg.res_id)
                            if channel.whatsapp_partner_id:
                                new_author_id = channel.whatsapp_partner_id.id
                            else:
                                new_author_id = False # System message
                    elif rec.message_type == 'outbound':
                        # Outbound message (should be right). Use the company's partner or the user who sent it.
                        if rec.is_bot_message:
                            new_author_id = self.env.ref('base.partner_root').id
                        else:
                            new_author_id = rec.create_uid.partner_id.id if rec.create_uid else self.env.ref('base.partner_root').id
                            
                    if copied_msg.author_id.id != new_author_id:
                        copied_msg.sudo().write({'author_id': new_author_id})

        return records
