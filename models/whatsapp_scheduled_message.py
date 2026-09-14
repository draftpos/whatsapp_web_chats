from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class WhatsAppScheduledMessage(models.Model):
    _name = 'whatsapp.scheduled.message'
    _description = 'WhatsApp Scheduled Message'
    _order = 'scheduled_at asc'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    channel_id = fields.Many2one('discuss.channel', string='Channel', required=True, ondelete='cascade')
    scheduled_at = fields.Datetime(string='Scheduled At', required=True)
    
    message_type = fields.Selection([
        ('quick_reply', 'Quick Reply'),
        ('custom', 'Custom Message'),
        ('template', 'Template'),
    ], string='Message Type', required=True)
    
    quick_reply_id = fields.Many2one('whatsapp.quick.reply', string='Quick Reply')
    custom_body = fields.Text(string='Custom Body')
    template_id = fields.Many2one('whatsapp.template', string='Template')
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed')
    ], string='State', default='pending', required=True)
    
    is_auto_followup = fields.Boolean(string='Is Auto Follow-up', default=False)
    current_rule_id = fields.Many2one('whatsapp.followup.rule', string='Current Rule')
    created_by_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    @api.model
    def _cron_send_scheduled_messages(self):
        now = fields.Datetime.now()
        messages = self.search([
            ('state', '=', 'pending'),
            ('scheduled_at', '<=', now)
        ])
        
        for msg in messages:
            try:
                if msg.message_type == 'template' and msg.template_id:
                    # Send template
                    msg.channel_id.wa_account_id.send_whatsapp_template(msg.channel_id.id, msg.template_id.id)
                elif msg.message_type == 'quick_reply' and msg.quick_reply_id:
                    # Send quick reply
                    msg.channel_id.wa_account_id.post_whatsapp_message(
                        msg.channel_id.id,
                        body=msg.quick_reply_id.body,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment'
                    )
                elif msg.message_type == 'custom' and msg.custom_body:
                    # Send custom message
                    msg.channel_id.wa_account_id.post_whatsapp_message(
                        msg.channel_id.id,
                        body=msg.custom_body,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment'
                    )
                
                msg.write({'state': 'sent'})
                
                # If this was an auto-followup, queue the next rule in the sequence
                if msg.is_auto_followup and msg.current_rule_id:
                    next_rule = self.env['whatsapp.followup.rule'].search([
                        ('account_id', '=', msg.current_rule_id.account_id.id),
                        ('sequence', '>', msg.current_rule_id.sequence)
                    ], order='sequence asc', limit=1)
                    
                    if next_rule:
                        self.create({
                            'channel_id': msg.channel_id.id,
                            'scheduled_at': next_rule.get_scheduled_datetime(fields.Datetime.now()),
                            'message_type': 'template',
                            'template_id': next_rule.template_id.id,
                            'is_auto_followup': True,
                            'current_rule_id': next_rule.id,
                            'state': 'pending',
                        })
                        
            except Exception as e:
                _logger.error(f"Failed to send scheduled message {msg.id}: {str(e)}")
                msg.write({'state': 'failed'})
