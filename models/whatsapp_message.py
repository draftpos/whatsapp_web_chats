from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    wa_reaction = fields.Char(string='WhatsApp Reaction', help='Emoji reaction from the user')
    wa_reaction_me = fields.Char(string='My Reaction', help='Emoji reaction sent by me')
    wa_is_starred = fields.Boolean(string='Starred (Local)')
    wa_is_pinned = fields.Boolean(string='Pinned (Local)')


    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.company_id and rec.wa_account_id and rec.wa_account_id.company_id:
                rec.company_id = rec.wa_account_id.company_id.id
            if rec.mail_message_id:
                # Find the copied discuss.channel message
                copied_msg = self.env['mail.message'].sudo().search([
                    ('model', '=', 'discuss.channel'),
                    ('message_type', 'in', ('whatsapp_message', 'comment')),
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

    @api.model
    def _send_cron(self):
        """ Send all outgoing messages. 
        Overridden to add FOR UPDATE SKIP LOCKED to prevent database locking issues 
        and duplicate message sending when multiple cron threads run.
        """
        # Lock outgoing messages to prevent concurrent crons from picking the same messages
        self.env.cr.execute("""
            SELECT id FROM whatsapp_message 
            WHERE state = 'outgoing'
            ORDER BY wa_template_id DESC 
            LIMIT 500
            FOR UPDATE SKIP LOCKED
        """)
        locked_ids = [row[0] for row in self.env.cr.fetchall()]
        
        if not locked_ids:
            return

        records = self.browse(locked_ids)
        # Call the core _send_message logic
        records._send_message(with_commit=not self.env.registry.in_test_mode())
        
        if len(records) == 500:
            self.env.ref('whatsapp.ir_cron_send_whatsapp_queue')._trigger()
