from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

class WhatsAppFollowupRule(models.Model):
    _name = 'whatsapp.followup.rule'
    _description = 'WhatsApp Auto Follow-up Rule'
    _order = 'sequence, id'

    account_id = fields.Many2one('whatsapp.account', string='WhatsApp Account', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    delay_condition = fields.Selection([
        ('23_hours', 'No reply within 23 hours'),
        ('24_hours', 'No reply within 24 hours'),
        ('custom_hours', 'Custom (Hours)'),
        ('custom_days', 'Custom (Days)'),
    ], string='Condition', required=True, default='23_hours')
    delay_value = fields.Integer(string='Delay Value', default=1, help='Used for Custom Hours or Days')
    template_id = fields.Many2one('whatsapp.template', string='Template to Send', required=True, domain="[('status', '=', 'approved')]")
    
    def get_scheduled_datetime(self, from_datetime):
        if self.delay_condition == '23_hours':
            return from_datetime + relativedelta(hours=23)
        elif self.delay_condition == '24_hours':
            return from_datetime + relativedelta(hours=24)
        elif self.delay_condition == 'custom_hours':
            return from_datetime + relativedelta(hours=self.delay_value)
        elif self.delay_condition == 'custom_days':
            return from_datetime + relativedelta(days=self.delay_value)
        return from_datetime + relativedelta(hours=23)
