from odoo import models, fields, api

class MailMessage(models.Model):
    _inherit = 'mail.message'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        
        for rec in records:
            if rec.model == 'wa.chatbot.session' and rec.res_id:
                try:
                    import logging
                    _logger = logging.getLogger(__name__)
                    
                    session = self.env['wa.chatbot.session'].sudo().browse(rec.res_id)
                    if session.exists():
                        account = session.chatbot_id.account_id
                        phone = session.phone
                        partner = session.partner_id
                        
                        _logger.error("DEBUG: Found session for phone %s, account %s", phone, account.id)
                        
                        Channel = self.env['discuss.channel'].sudo()
                        channel = Channel.search([
                            ('channel_type', '=', 'whatsapp'),
                            ('wa_account_id', '=', account.id),
                            ('whatsapp_number', '=', phone),
                        ], limit=1)
                        
                        _logger.error("DEBUG: Searched for channel, found: %s", channel.id if channel else False)
                        
                        if not channel and hasattr(Channel, '_get_whatsapp_channel'):
                            _logger.error("DEBUG: Calling _get_whatsapp_channel...")
                            channel = Channel._get_whatsapp_channel(
                                whatsapp_number=phone,
                                wa_account_id=account,
                                sender_name=partner.name if partner else phone,
                                create_if_not_found=True,
                                related_message=False,
                            )
                            _logger.error("DEBUG: Created/Found channel: %s", channel.id if channel else False)
                            
                        if channel:
                            body_html = rec.body or ''
                            # If the original author is an internal user, it's an outbound message from an agent.
                            # Otherwise (e.g. public user or no user), it's an inbound message from the customer.
                            is_internal_user = rec.author_id and any(u.has_group('base.group_user') for u in rec.author_id.user_ids)
                            if is_internal_user:
                                new_author_id = rec.author_id.id
                            else:
                                new_author_id = channel.whatsapp_partner_id.id if channel.whatsapp_partner_id else (partner.id if partner else False)

                            # Duplicate the message into the discuss.channel so operators can see it
                            rec.sudo().copy({
                                'model': 'discuss.channel',
                                'res_id': channel.id,
                                'message_type': 'comment',
                                'author_id': new_author_id,
                                'body': body_html,
                            })
                            _logger.error("DEBUG: Message copied successfully!")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error("DEBUG: Failed to mirror chatbot msg to discuss.channel: %s", e)

        return records
