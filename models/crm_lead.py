from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    _order = 'wa_last_message_date desc, priority desc, id desc'

    wa_last_message_date = fields.Datetime(string="Last WA Message Date", index=True)

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
        base_domain = [
            ('channel_type', '=', 'whatsapp'),
            '|', ('tenant_id', '=', False), ('tenant_id', '=', self.env.company.id)
        ]
        if not self.env.is_admin() and hasattr(self.env.user, 'whatsapp_account_ids'):
            base_domain += [('wa_account_id', 'in', self.env.user.whatsapp_account_ids.ids)]
            
        search_domains = []
        lead_data = []
        
        for lead in self:
            phone = lead.phone if 'phone' in lead._fields else False
            mobile = lead.mobile if 'mobile' in lead._fields else False
            clean_phone = False
            
            if phone or mobile:
                phone_to_use = phone or mobile
                clean_phone = ''.join(filter(str.isdigit, phone_to_use))
                if clean_phone.startswith('0'):
                    clean_phone = '263' + clean_phone[1:]
                    
            lead_data.append({
                'lead': lead,
                'clean_phone': clean_phone,
                'partner_id': lead.partner_id.id if lead.partner_id else False
            })
            
            if clean_phone:
                number_domain = ['|', ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone]), ('whatsapp_partner_id.phone', 'ilike', clean_phone)]
                if lead.partner_id:
                    search_domains.append(['|', ('whatsapp_partner_id', '=', lead.partner_id.id)] + number_domain)
                else:
                    search_domains.append(number_domain)
                    
        combined_lead_domain = []
        if search_domains:
            for _ in range(len(search_domains) - 1):
                combined_lead_domain.append('|')
            for d in search_domains:
                combined_lead_domain.extend(d)
                
        all_channels = self.env['discuss.channel']
        if combined_lead_domain:
            final_domain = base_domain + combined_lead_domain
            all_channels = self.env['discuss.channel'].sudo().search(final_domain)
            
        for data in lead_data:
            lead = data['lead']
            clean_phone = data['clean_phone']
            partner_id = data['partner_id']
            
            if not clean_phone:
                lead.wa_chat_channel_id = False
                continue
                
            matched_channel = False
            for ch in all_channels:
                if partner_id and ch.whatsapp_partner_id.id == partner_id:
                    matched_channel = ch
                    break
                if clean_phone and ch.whatsapp_number in [clean_phone, '+' + clean_phone]:
                    matched_channel = ch
                    break
                if clean_phone and ch.whatsapp_partner_id and ch.whatsapp_partner_id.phone:
                    ch_clean = ''.join(filter(str.isdigit, ch.whatsapp_partner_id.phone))
                    if ch_clean and (clean_phone in ch_clean or ch_clean in clean_phone):
                        matched_channel = ch
                        break
                        
            lead.wa_chat_channel_id = matched_channel.id if matched_channel else False

    def action_open_whatsapp_chat(self):
        self.ensure_one()
        channel_id = self.wa_chat_channel_id.id if self.wa_chat_channel_id else False
        
        if not channel_id:
            phone = self.phone if 'phone' in self._fields else False
            mobile = self.mobile if 'mobile' in self._fields else False
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

    def _find_whatsapp_channel(self, create_if_missing=False):
        """Find the WhatsApp channel for this lead. Optionally create one if missing."""
        self.ensure_one()
        phone = self.phone if 'phone' in self._fields else False
        mobile = self.mobile if 'mobile' in self._fields else False
        phone_to_use = phone or mobile

        channel_id = False

        if phone_to_use:
            clean_phone = ''.join(filter(str.isdigit, phone_to_use))
            if clean_phone.startswith('0'):
                clean_phone = '263' + clean_phone[1:]

            base_domain = [
                ('channel_type', '=', 'whatsapp'),
                '|', ('tenant_id', '=', False), ('tenant_id', '=', self.env.company.id)
            ]

            number_domain = [
                '|',
                ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone]),
                ('whatsapp_partner_id.phone', 'ilike', clean_phone)
            ]
            if self.partner_id:
                search_domain = base_domain + ['|', ('whatsapp_partner_id', '=', self.partner_id.id)] + number_domain
            else:
                search_domain = base_domain + number_domain

            existing = self.env['discuss.channel'].sudo().search(search_domain, order='id desc', limit=1)
            if existing:
                channel_id = existing.id
            elif create_if_missing:
                account_domain = []
                if not self.env.is_admin() and hasattr(self.env.user, 'whatsapp_account_ids'):
                    account_domain = [('id', 'in', self.env.user.whatsapp_account_ids.ids)]
                wa_account = self.env['whatsapp.account'].sudo().search(account_domain, limit=1)
                new_ch = self.env['discuss.channel'].sudo().create({
                    'name': clean_phone,
                    'channel_type': 'whatsapp',
                    'whatsapp_number': clean_phone,
                    'whatsapp_partner_id': self.partner_id.id if self.partner_id else False,
                    'wa_account_id': wa_account.id if wa_account else False,
                })
                channel_id = new_ch.id

        if channel_id:
            channel = self.env['discuss.channel'].sudo().browse(channel_id)
            if self.env.user.partner_id.id not in channel.channel_member_ids.mapped('partner_id.id'):
                channel.sudo().add_members(self.env.user.partner_id.ids)

        return channel_id

    def get_whatsapp_channel_id_for_widget(self, create_if_missing=False):
        """Called by the JS CrmWhatsappChatWidget to get the channel ID for this lead."""
        self.ensure_one()
        return self._find_whatsapp_channel(create_if_missing=create_if_missing)


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
                partner = self.env['res.partner'].with_context(skip_duplicate_check=True).create(partner_vals)
                vals['partner_id'] = partner.id
                
        records = super().create(vals_list)
        
        lead_tag = self.env['wa.chat.tag'].sudo().search([('name', '=ilike', 'lead%')], limit=1)
        for record in records:
            if self.env.context.get('force_create_partner_from_whatsapp') and record.wa_chat_channel_id and record.partner_id:
                if not record.wa_chat_channel_id.whatsapp_partner_id:
                    record.wa_chat_channel_id.whatsapp_partner_id = record.partner_id.id
            
            if record.wa_chat_channel_id and lead_tag:
                if lead_tag.id not in record.wa_chat_channel_id.wa_tag_ids.ids:
                    record.wa_chat_channel_id.sudo().write({'wa_tag_ids': [(4, lead_tag.id)]})
                    
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'phone' in vals or 'mobile' in vals or 'partner_id' in vals:
            lead_tag = self.env['wa.chat.tag'].sudo().search([('name', '=ilike', 'lead%')], limit=1)
            if lead_tag:
                for record in self:
                    if record.wa_chat_channel_id:
                        if lead_tag.id not in record.wa_chat_channel_id.wa_tag_ids.ids:
                            record.wa_chat_channel_id.sudo().write({'wa_tag_ids': [(4, lead_tag.id)]})
        return res
