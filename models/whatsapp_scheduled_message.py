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

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.state == 'pending' and rec.scheduled_at:
                try:
                    cron = self.env.ref('whatsapp_web_chats.ir_cron_send_scheduled_messages', raise_if_not_found=False)
                    if cron:
                        cron._trigger(at=rec.scheduled_at)
                except Exception as e:
                    _logger.warning("Failed to trigger scheduled message cron: %s", str(e))
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'scheduled_at' in vals or 'state' in vals:
            for rec in self:
                if rec.state == 'pending' and rec.scheduled_at:
                    try:
                        cron = self.env.ref('whatsapp_web_chats.ir_cron_send_scheduled_messages', raise_if_not_found=False)
                        if cron:
                            cron._trigger(at=rec.scheduled_at)
                    except Exception as e:
                        pass
        return res

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
                        message_type='whatsapp_message',
                        subtype_xmlid='mail.mt_comment',
                        author_id=msg.created_by_id.partner_id.id
                    )
                elif msg.message_type == 'custom' and msg.custom_body:
                    # Send custom message
                    msg.channel_id.wa_account_id.post_whatsapp_message(
                        msg.channel_id.id,
                        body=msg.custom_body,
                        message_type='whatsapp_message',
                        subtype_xmlid='mail.mt_comment',
                        author_id=msg.created_by_id.partner_id.id
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
                
        # Trigger the WhatsApp queue immediately so it doesn't wait for its own hourly cron
        if messages:
            try:
                self.env.ref('whatsapp.ir_cron_send_whatsapp_queue')._trigger()
            except Exception:
                pass
