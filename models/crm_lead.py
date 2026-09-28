from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    wa_chat_channel_id = fields.Many2one(
        'discuss.channel', 
        string='WhatsApp Chat Channel', 
        compute='_compute_wa_chat_channel_id',
        store=False
    )

    project_category = fields.Selection([
        ('fitted_kitchens', 'Fitted Kitchens'),
        ('construction', 'Construction')
    ], string='Project Category')

    def _compute_wa_chat_channel_id(self):
        for lead in self:
            channel = False
            if lead.phone or lead.mobile:
                phone = lead.phone or lead.mobile
                # Format phone logic similar to JS formatWhatsAppNumber
                clean_phone = ''.join(filter(str.isdigit, phone))
                if clean_phone.startswith('0'):
                    clean_phone = '263' + clean_phone[1:] # standard default in module
                    
                domain = [
                    ('channel_type', '=', 'whatsapp'), 
                    ('name', 'ilike', clean_phone)
                ]
                if lead.partner_id:
                    domain = ['|', ('whatsapp_partner_id', '=', lead.partner_id.id)] + domain
                
                channel = self.env['discuss.channel'].search(domain, limit=1)
                
            lead.wa_chat_channel_id = channel.id if channel else False
