from odoo import models, api, fields
from datetime import datetime
import pytz

class WhatsappDashboard(models.AbstractModel):
    _name = 'whatsapp.dashboard'
    _description = 'WhatsApp Dashboard Statistics'

    @api.model
    def get_dashboard_stats(self, date_from=None, date_to=None, account_id=None):
        domain_msg = []
        if date_from:
            domain_msg.append(('create_date', '>=', date_from))
        if date_to:
            domain_msg.append(('create_date', '<=', date_to))
        if account_id:
            domain_msg.append(('wa_account_id', '=', int(account_id)))
            
        # Get active accounts for the filter dropdown
        accounts = self.env['whatsapp.account'].search_read([], ['id', 'name'])
        
        # New Messages (Inbound)
        inbound_domain = domain_msg + [('message_type', '=', 'inbound')]
        new_inbound = self.env['whatsapp.message'].search_count(inbound_domain)
        
        # All Outbound Messages
        outbound_domain = domain_msg + [('message_type', '=', 'outbound')]
        all_outbound = self.env['whatsapp.message'].search(outbound_domain)
        
        # Outbound message states
        total_sent = len(all_outbound)
        
        # Sent messages that are Read
        read_count = len(all_outbound.filtered(lambda m: m.state == 'read'))
        
        # Sent messages that are Delivered (but not read)
        delivered_count = len(all_outbound.filtered(lambda m: m.state == 'delivered'))
        
        # Sent messages that are neither Read nor Delivered (error, bounced, cancel, outgoing, sent)
        not_delivered_count = len(all_outbound.filtered(lambda m: m.state not in ['delivered', 'read']))
        
        # Unreplied Messages: Using the "Delivered but not read" as per user request + all delivered
        unreplied_count = delivered_count
        
        # Favorites
        fav_domain = [('wa_is_favourite', '=', True)]
        if account_id:
            fav_domain.append(('wa_account_id', '=', int(account_id)))
        total_favorites = self.env['discuss.channel'].search_count(fav_domain)
        
        # Total Contacts
        total_contacts = self.env['res.partner'].search_count([])
        
        return {
            'accounts': accounts,
            'new_inbound': new_inbound,
            'unreplied_count': unreplied_count,
            'total_favorites': total_favorites,
            'total_contacts': total_contacts,
            'total_sent': total_sent,
            'read_count': read_count,
            'delivered_count': delivered_count,
            'not_delivered_count': not_delivered_count,
        }
