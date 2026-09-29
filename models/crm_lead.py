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

    @api.onchange('project_category')
    def _onchange_project_category(self):
        if self.project_category:
            category_names = dict(self._fields['project_category'].selection)
            self.name = category_names.get(self.project_category, self.project_category)

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
                    '|', ('tenant_id', '=', False), ('tenant_id', '=', self.env.company.id)
                ]
                if not self.env.is_admin() and hasattr(self.env.user, 'whatsapp_account_ids'):
                    domain += [('wa_account_id', 'in', self.env.user.whatsapp_account_ids.ids)]
                    
                number_domain = ['|', ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone]), ('whatsapp_partner_id.phone', 'ilike', clean_phone)]
                if lead.partner_id:
                    domain += ['|', ('whatsapp_partner_id', '=', lead.partner_id.id)] + number_domain
                else:
                    domain += number_domain
                
                channel = self.env['discuss.channel'].sudo().search(domain, limit=1)
                
            lead.wa_chat_channel_id = channel.id if channel else False

    def action_open_whatsapp_chat(self):
        self.ensure_one()
        channel_id = self.wa_chat_channel_id.id if self.wa_chat_channel_id else False
        
        if not channel_id:
            phone = self.phone if hasattr(self, 'phone') else False
            mobile = self.mobile if hasattr(self, 'mobile') else False
            phone_to_use = phone or mobile
            
            if phone_to_use:
                clean_phone = ''.join(filter(str.isdigit, phone_to_use))
                if clean_phone.startswith('0'):
                    clean_phone = '263' + clean_phone[1:]
                    
                domain = [
                    ('channel_type', '=', 'whatsapp'),
                    '|', ('tenant_id', '=', False), ('tenant_id', '=', self.env.company.id)
                ]
                if not self.env.is_admin() and hasattr(self.env.user, 'whatsapp_account_ids'):
                    domain += [('wa_account_id', 'in', self.env.user.whatsapp_account_ids.ids)]
                    
                number_domain = ['|', ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone]), ('whatsapp_partner_id.phone', 'ilike', clean_phone)]
                if self.partner_id:
                    domain += ['|', ('whatsapp_partner_id', '=', self.partner_id.id)] + number_domain
                else:
                    domain += number_domain
                    
                existing = self.env['discuss.channel'].sudo().search(domain, limit=1)
                if existing:
                    channel_id = existing.id
                else:
                    account_domain = []
                    if not self.env.is_admin() and hasattr(self.env.user, 'whatsapp_account_ids'):
                        account_domain = [('id', 'in', self.env.user.whatsapp_account_ids.ids)]
                    wa_account = self.env['whatsapp.account'].sudo().search(account_domain, limit=1)
                    
                    new_channel = self.env['discuss.channel'].sudo().create({
                        'name': clean_phone,
                        'channel_type': 'whatsapp',
                        'whatsapp_number': clean_phone,
                        'whatsapp_partner_id': self.partner_id.id if self.partner_id else False,
                        'wa_account_id': wa_account.id if wa_account else False,
                    })
                    channel_id = new_channel.id

        if not channel_id:
            from odoo.exceptions import UserError
            raise UserError("Cannot start WhatsApp chat: The lead does not have a valid phone number.")

        # Ensure the current user is a member of the channel so they can view it
        channel = self.env['discuss.channel'].sudo().browse(channel_id)
        if self.env.user.partner_id.id not in channel.channel_member_ids.mapped('partner_id.id'):
            channel.sudo().add_members(self.env.user.partner_id.ids)

        return {
            'type': 'ir.actions.client',
            'tag': 'whatsapp_web_chats.chats_client_action',
            'name': 'WhatsApp Chat',
            'context': {
                'hide_sidebar': True,
                'default_channel_id': channel_id
            }
        }


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get('force_create_partner_from_whatsapp') and not vals.get('partner_id'):
                partner_name = vals.get('contact_name') or vals.get('partner_name') or vals.get('name') or 'WhatsApp Contact'
                partner_vals = {
                    'name': partner_name,
                    'phone': vals.get('phone'),
                    'email': vals.get('email_from'),
                }
                partner = self.env['res.partner'].create(partner_vals)
                vals['partner_id'] = partner.id
                
        records = super().create(vals_list)
        
        for record in records:
            if self.env.context.get('force_create_partner_from_whatsapp') and record.wa_chat_channel_id and record.partner_id:
                if not record.wa_chat_channel_id.whatsapp_partner_id:
                    record.wa_chat_channel_id.whatsapp_partner_id = record.partner_id.id
                    
        return records
