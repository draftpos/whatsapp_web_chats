from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    wa_chat_channel_id = fields.Many2one(
        'discuss.channel', 
        string='WhatsApp Chat Channel', 
        compute='_compute_wa_chat_channel_id',
        store=False
    )

    wa_unread_messages_count = fields.Integer(
        string='New WA Messages',
        compute='_compute_wa_unread_messages_count',
        store=False
    )

    project_category = fields.Selection([
        ('fitted_kitchens', 'Fitted Kitchens'),
        ('construction', 'Construction')
    ], string='Project Category')

    def _compute_wa_unread_messages_count(self):
        for lead in self:
            count = 0
            if lead.wa_chat_channel_id:
                channel = lead.wa_chat_channel_id
                count = getattr(channel, 'message_needaction_counter', 0)
                if count == 0:
                    count = getattr(channel, 'message_unread_counter', 0)
                
                # If native Odoo counters are 0, check the custom global unread flag
                if count == 0 and getattr(channel, 'wa_is_unread_global', False):
                    # Attempt to get actual unread count since last seen
                    # or default to 1 so the badge appears
                    count = 1
            lead.wa_unread_messages_count = count

    def _compute_wa_chat_channel_id(self):
        for lead in self:
            channel = False
            phone = lead.phone if hasattr(lead, 'phone') else False
            mobile = lead.mobile if hasattr(lead, 'mobile') else False
            
            if phone or mobile:
                phone_to_use = phone or mobile
                # Format phone logic similar to JS formatWhatsAppNumber
                clean_phone = ''.join(filter(str.isdigit, phone_to_use))
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

    def action_open_whatsapp_chat(self):
        self.ensure_one()
        return {
            'name': 'WhatsApp Chat',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('whatsapp_web_chats.crm_lead_whatsapp_chat_dialog').id,
            'target': 'new',
        }

