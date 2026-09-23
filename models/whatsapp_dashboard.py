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
        
        def get_unique_daily_chats(messages):
            unique_chats = set()
            for msg in messages:
                if msg.create_date and msg.mail_message_id.res_id:
                    unique_chats.add((msg.create_date.date(), msg.mail_message_id.res_id))
            return len(unique_chats)

        # All Inbound Messages
        inbound_domain = domain_msg + [('message_type', '=', 'inbound')]
        all_inbound = self.env['whatsapp.message'].search(inbound_domain)
        new_inbound = get_unique_daily_chats(all_inbound)
        inbound_channel_ids = set(all_inbound.mapped('mail_message_id.res_id'))
        
        # All Outbound Messages
        outbound_domain = domain_msg + [('message_type', '=', 'outbound')]
        all_outbound = self.env['whatsapp.message'].search(outbound_domain)
        outbound_channel_ids = set(all_outbound.mapped('mail_message_id.res_id'))
        
        # Outbound message states (now counting unique daily chats)
        total_sent = get_unique_daily_chats(all_outbound)
        
        # Sent messages that are Read
        read_count = get_unique_daily_chats(all_outbound.filtered(lambda m: m.state == 'read'))
        
        # Sent messages that are Delivered (but not read)
        delivered_count = get_unique_daily_chats(all_outbound.filtered(lambda m: m.state == 'delivered'))
        
        # Sent messages that are neither Read nor Delivered (error, bounced, cancel, outgoing, sent)
        not_delivered_count = get_unique_daily_chats(all_outbound.filtered(lambda m: m.state not in ['delivered', 'read']))
        
        # Unreplied Messages: Using the "Delivered but not read" as per user request + all delivered
        unreplied_count = delivered_count
        
        # Favorites
        fav_domain = [('wa_is_favourite', '=', True)]
        if account_id:
            fav_domain.append(('wa_account_id', '=', int(account_id)))
        total_favorites = self.env['discuss.channel'].search_count(fav_domain)
        
        # Template Analytics
        templates_sent = all_outbound.filtered(lambda m: m.wa_template_id)
        templates_sent_count = get_unique_daily_chats(templates_sent)
        
        template_channel_ids = set(templates_sent.mapped('mail_message_id.res_id'))
        templates_delivered = templates_sent.filtered(lambda m: m.state == 'delivered')
        templates_delivered_channels = set(templates_delivered.mapped('mail_message_id.res_id'))
        
        templates_replied_channels = template_channel_ids.intersection(inbound_channel_ids)
        templates_replied_count = len(templates_replied_channels)
        
        templates_delivered_not_replied_channels = templates_delivered_channels - inbound_channel_ids
        templates_delivered_not_replied_count = len(templates_delivered_not_replied_channels)
        
        # General chat engagement
        # Total Contacts (WhatsApp Channels)
        total_contacts_domain = [('channel_type', '=', 'whatsapp')]
        if account_id:
            total_contacts_domain.append(('wa_account_id', '=', int(account_id)))
        total_contacts = self.env['discuss.channel'].search_count(total_contacts_domain)
        
        # Chats Activity (already computed above)
        
        total_chats_active = len(inbound_channel_ids.union(outbound_channel_ids))
        replied_chats_count = len(inbound_channel_ids.intersection(outbound_channel_ids))
        not_replied_chats_count = total_chats_active - replied_chats_count
        
        # Timeseries data for graphs
        def get_timeseries_data(messages):
            from collections import defaultdict
            daily_counts = defaultdict(set)
            for msg in messages:
                if msg.create_date and msg.mail_message_id.res_id:
                    day_str = msg.create_date.date().strftime('%Y-%m-%d')
                    daily_counts[day_str].add(msg.mail_message_id.res_id)
            return [{'date': d, 'count': len(channels)} for d, channels in daily_counts.items()]
            
        timeseries = {
            'inbound': get_timeseries_data(all_inbound),
            'outbound': get_timeseries_data(all_outbound)
        }
        
        # Media Counts (Images, Videos, Documents)
        inbound_attachments = all_inbound.mapped('mail_message_id.attachment_ids')
        outbound_attachments = all_outbound.mapped('mail_message_id.attachment_ids')
        
        def count_media(attachments):
            images = len(attachments.filtered(lambda a: a.mimetype and a.mimetype.startswith('image/')))
            videos = len(attachments.filtered(lambda a: a.mimetype and a.mimetype.startswith('video/')))
            documents = len(attachments) - images - videos
            return {'images': images, 'videos': videos, 'documents': documents}
            
        inbound_media = count_media(inbound_attachments)
        outbound_media = count_media(outbound_attachments)

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
            'timeseries': timeseries,
            'inbound_media': inbound_media,
            'outbound_media': outbound_media,
            'total_chats_active': total_chats_active,
            'replied_chats_count': replied_chats_count,
            'not_replied_chats_count': not_replied_chats_count,
            'templates_sent': templates_sent_count,
            'templates_replied': templates_replied_count,
            'templates_delivered_not_replied': templates_delivered_not_replied_count,
        }
