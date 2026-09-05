from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class WAChatbotSession(models.Model):
    _name = 'wa.chatbot.session'
    _inherit = 'wa.chatbot.session'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        # Prevent creating bot sessions if the account bot is disabled
        filtered_vals = []
        for vals in vals_list:
            account_id = vals.get('account_id')
            if not account_id and 'chatbot_id' in vals:
                # Try to get account from chatbot
                chatbot = self.env['wa.chatbot'].sudo().browse(vals['chatbot_id'])
                if hasattr(chatbot, 'account_id'):
                    account_id = chatbot.account_id.id
            
            if account_id:
                account = self.env['whatsapp.account'].sudo().browse(account_id)
                if account.exists() and hasattr(account, 'wa_bot_active') and not account.wa_bot_active:
                    _logger.info("Blocked creation of wa.chatbot.session because wa_bot_active is False")
                    continue
            filtered_vals.append(vals)
            
        if not filtered_vals:
            return self.env['wa.chatbot.session']
            
        return super().create(filtered_vals)

class WhatsAppAccount(models.Model):
    _inherit = 'whatsapp.account'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    image_1920 = fields.Image(string="Profile Picture", max_width=1920, max_height=1920)
    wa_bot_active = fields.Boolean(string="Automated Bot Responses", default=True)
    wa_department_routing_active = fields.Boolean(string="Auto Response for Departments", default=True)

    @api.model
    def toggle_account_bot(self, wa_account_id, active):
        account = self.browse(int(wa_account_id))
        if account.exists():
            account.sudo().wa_bot_active = bool(active)
            if not active and 'wa.chatbot.session' in self.env:
                try:
                    sessions = self.env['wa.chatbot.session'].sudo().search([])
                    if sessions and 'account_id' in sessions[0]._fields:
                        sessions.filtered(lambda s: s.account_id.id == account.id).unlink()
                    else:
                        sessions.unlink() # fallback if account_id isn't the relation
                except Exception as e:
                    pass
            return True
        return False

    @api.model
    def mark_whatsapp_web_messages_read(self, channel_id):
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if channel.exists():
            channel.channel_seen()
            return True
        return False

    @api.model
    def get_whatsapp_web_channels(self, wa_account_id=None):
        domain = [('channel_type', '=', 'whatsapp'), '|', ('whatsapp_partner_id', '!=', False), ('whatsapp_number', '!=', False)]
        #if wa_account_id:
        #    domain.append(('wa_account_id', '=', int(wa_account_id)))
        
        channels = self.env['discuss.channel'].sudo().search(domain)
        
        res = []
        for c in channels:
            last_message = self.env['mail.message'].sudo().search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', c.id)
            ], order='date desc', limit=1)
            
            sort_date_obj = last_message.date if last_message else c.write_date
            sort_date = sort_date_obj.strftime('%Y-%m-%dT%H:%M:%SZ') if sort_date_obj else ''
            
            import re
            last_msg_body = ''
            last_msg_time = ''
            if last_message:
                raw = re.sub(r'<[^>]+>', '', last_message.body or '').strip()
                last_msg_body = raw[:60] + ('...' if len(raw) > 60 else '')
                last_msg_time = last_message.date.strftime('%Y-%m-%dT%H:%M:%SZ') if last_message.date else ''
            
            member = self.env['discuss.channel.member'].sudo().search([
                ('channel_id', '=', c.id),
                ('partner_id', '=', self.env.user.partner_id.id)
            ], limit=1)
            unread_count = member.message_unread_counter if member else 0
            
            import re
            def clean_name(n):
                if not n: return n
                # Strip any trailing parenthetical e.g. "(School)", "(Havano Support)", etc.
                return re.sub(r'\s*\([^)]+\)\s*$', '', n, flags=re.IGNORECASE).strip()
                
            res.append({
                'id': c.id,
                'name': clean_name(c.name),
                'channel_type': c.channel_type,
                'whatsapp_partner_id': [c.whatsapp_partner_id.id, clean_name(c.whatsapp_partner_id.name)] if c.whatsapp_partner_id else False,
                'wa_account_id': [c.wa_account_id.id, c.wa_account_id.name] if c.wa_account_id else False,
                'message_needaction_counter': unread_count,
                'write_date': sort_date,
                'whatsapp_number': c.whatsapp_number,
                'last_message_preview': last_msg_body,
                'last_message_time': last_msg_time,
                'wa_bot_state': c.wa_bot_state,
                'wa_department': c.wa_department,
                'wa_agent_id': [c.wa_agent_id.id, c.wa_agent_id.name] if c.wa_agent_id else False,
                'wa_is_done': c.wa_is_done,
                'wa_is_unread_global': c.wa_is_unread_global,
                'wa_is_favourite': c.wa_is_favourite,
                'wa_is_urgent': c.wa_is_urgent,
                'wa_tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in c.wa_tag_ids],
            })
            
        res.sort(key=lambda x: x['write_date'], reverse=True)
        show_labels = self.env['ir.config_parameter'].sudo().get_param('whatsapp_web_chats.wa_show_labels', 'True') == 'True'
        return {
            'channels': res,
            'show_labels': show_labels
        }

    @api.model
    def get_all_chat_tags(self):
        tags = self.env['wa.chat.tag'].sudo().search([])
        return [{'id': t.id, 'name': t.name, 'color': t.color} for t in tags]

    @api.model
    def update_chat_tags(self, channel_id, tag_ids):
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if channel.exists():
            channel.sudo().write({'wa_tag_ids': [(6, 0, tag_ids)]})
            return True
        return False

    @api.model
    def set_whatsapp_chat_state(self, channel_id, field, value):
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if channel.exists() and field in ['wa_is_done', 'wa_is_unread_global', 'wa_is_favourite', 'wa_is_urgent']:
            channel.sudo().write({field: bool(value)})
            # If marked as done, remove unread flag
            if field == 'wa_is_done' and value:
                channel.sudo().write({'wa_is_unread_global': False})
                self.mark_whatsapp_web_messages_read(channel_id)
            return {'success': True}
        return {'success': False, 'error': 'Invalid channel or field'}
        
    @api.model
    def get_whatsapp_web_messages(self, channel_id):
        import re
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        messages = self.env['mail.message'].sudo().search([
            ('res_id', '=', int(channel_id)),
            ('model', '=', 'discuss.channel'),
            ('message_type', 'in', ('comment', 'notification', 'whatsapp_message')),
        ], order='date asc')
        
        import re
        def clean_name(n):
            if not n: return n
            return re.sub(r'\s*\(\s*School\s*\)', '', n, flags=re.IGNORECASE).strip()
            
        # Fetch the latest whatsapp.message for this number to catch async errors
        wa_error = False
        if messages and channel.whatsapp_number:
            last_wa = self.env['whatsapp.message'].sudo().search([
                ('mobile_number', 'ilike', channel.whatsapp_number)
            ], order='id desc', limit=1)
            if last_wa and last_wa.state == 'error':
                wa_error = last_wa.failure_reason or last_wa.failure_type or 'Delivery failed'
        
        wa_msgs = self.env['whatsapp.message'].sudo().search([
            ('mail_message_id', 'in', messages.ids)
        ])
        wa_state_map = {wa.mail_message_id.id: wa.state for wa in wa_msgs if wa.mail_message_id}
        
        res = []
        for m in messages:
            # Skip messages with no body and no attachments
            body_text = re.sub(r'<[^>]+>', '', m.body or '').strip()
            if not body_text and not m.attachment_ids:
                continue
            
            wa_state = wa_state_map.get(m.id, False)
            
            if m.author_id and m.author_id.id == self.env.user.partner_id.id:
                is_me = True
            elif self.env.user.has_group('base.group_user'):
                if wa_state == 'received':
                    is_me = False
                elif m.author_id:
                    if channel.whatsapp_partner_id and m.author_id.id == channel.whatsapp_partner_id.id:
                        is_me = False
                    else:
                        public_partner = self.env.ref('base.public_partner', raise_if_not_found=False)
                        if public_partner and m.author_id.id == public_partner.id:
                            is_me = False
                        else:
                            is_me = True
                else:
                    is_me = False
            else:
                if m.author_id and channel.whatsapp_partner_id and m.author_id.id == channel.whatsapp_partner_id.id:
                    is_me = True
                else:
                    is_me = False
                
            # Format date as UTC ISO string so JS can parse it correctly
            date_str = m.date.strftime('%Y-%m-%dT%H:%M:%SZ') if m.date else False
            
            public_partner = self.env.ref('base.public_partner', raise_if_not_found=False)
            author_data = False
            if m.author_id:
                author_name = clean_name(m.author_id.name)
                # Replace "Public user" with the actual customer name
                if public_partner and m.author_id.id == public_partner.id:
                    customer = channel.whatsapp_partner_id
                    author_name = clean_name(customer.name) if customer else clean_name(channel.name)
                author_data = [m.author_id.id, author_name]
            
            msg_dict = {
                'id': m.id,
                'body': m.body,
                'author_id': author_data,
                'date': date_str,
                'message_type': m.message_type,
                'attachment_ids': [{'id': a.id, 'mimetype': a.mimetype} for a in m.attachment_ids],
                'is_me': is_me,
                'isMe': is_me,
                'wa_state': wa_state_map.get(m.id, False),
            }
            res.append(msg_dict)
            
        # Attach any recent delivery error to the last outgoing message
        if wa_error and res:
            for i in range(len(res)-1, -1, -1):
                if res[i]['is_me']:
                    res[i]['wa_error'] = wa_error
                    res[i]['wa_error_msg_id'] = last_wa.id
                    break
                    
        return res

    def _process_messages(self, value):
        # Temporarily disable the chatbot if wa_bot_active is False
        original_chatbot = False
        if not self.wa_bot_active:
            if 'chatbot_id' in self._fields:
                original_chatbot = self.chatbot_id
                if original_chatbot:
                    self.sudo().write({'chatbot_id': False})
            
            # Ensure no stray sessions intercept this message
            if 'wa.chatbot.session' in self.env:
                try:
                    sessions = self.env['wa.chatbot.session'].sudo().search([])
                    if sessions and 'account_id' in sessions[0]._fields:
                        sessions.filtered(lambda s: s.account_id.id == self.id).unlink()
                    else:
                        sessions.unlink()
                except Exception:
                    pass
                    
        # Extract whatsapp profile names to update partner names if they are just phone numbers
        wa_names = {}
        for contact in value.get('contacts', []):
            wa_id = contact.get('wa_id')
            profile_name = contact.get('profile', {}).get('name')
            if wa_id and profile_name:
                wa_names[str(wa_id)] = profile_name
                
        try:
            for message in value.get('messages', []):
                wa_id = message.get('from')
                if wa_id:
                    clean_phone = ''.join([c for c in str(wa_id) if c.isdigit()])
                    channel = self.env['discuss.channel'].sudo().search([
                        ('channel_type', '=', 'whatsapp'),
                        ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone]),
                        ('wa_account_id', '=', self.id)
                    ], limit=1)
                    
                    if channel:
                        if channel.whatsapp_number != clean_phone:
                            channel.sudo().write({'whatsapp_number': clean_phone})
                        channel.wa_is_unread_global = True
                        channel.wa_is_done = False
                        
                if message.get('type') == 'order':
                    order = message.get('order', {})
                    items = order.get('product_items', [])
                    
                    text_lines = ["🛒 *New Order Received!*"]
                    if order.get('text'):
                        text_lines.append(f"Note: {order['text']}")
                    text_lines.append("Items:")
                    
                    for item in items:
                        qty = item.get('quantity', 0)
                        price = item.get('item_price', '')
                        currency = item.get('currency', '')
                        product_id = item.get('product_retailer_id', 'Unknown Item')
                        
                        product = self.env['product.product'].sudo().search([
                            '|', ('default_code', '=', product_id), 
                            ('id', '=', int(product_id) if str(product_id).isdigit() else 0)
                        ], limit=1)
                        
                        product_name = product.name if product else product_id
                        text_lines.append(f"- {qty}x {product_name} ({currency} {price})")
                    
                    message['type'] = 'text'
                    message['text'] = {'body': '\n'.join(text_lines)}
                    
            res = super()._process_messages(value)
        finally:
            if not self.wa_bot_active and original_chatbot:
                self.sudo().write({'chatbot_id': original_chatbot.id})
                
        # After processing, try to update newly created partners with their WhatsApp profile name
        # if their current name is just a phone number
        for wa_id, profile_name in wa_names.items():
            partner = self.env['res.partner'].sudo().search([
                ('phone', 'ilike', wa_id)
            ], limit=1)
            if partner and partner.name:
                clean_name = ''.join(c for c in partner.name if c.isdigit() or c == '+')
                clean_wa = ''.join(c for c in wa_id if c.isdigit())
                # If the name is basically just their phone number
                if clean_name.endswith(clean_wa) or clean_name.startswith(clean_wa):
                    partner.sudo().write({'name': profile_name})
                    
        # Apply custom routing bot logic
        self._process_routing_bot(value)
                    
        return res

    def _process_routing_bot(self, value):
        if not self.wa_department_routing_active:
            return
            
        from datetime import datetime, timezone
        
        for message in value.get('messages', []):
            m_type = message.get('type')
            if m_type == 'interactive':
                inter = message.get('interactive', {})
                if inter.get('type') == 'list_reply':
                    text_body = inter.get('list_reply', {}).get('id', '')
                elif inter.get('type') == 'button_reply':
                    text_body = inter.get('button_reply', {}).get('id', '')
                else:
                    text_body = ''
            elif m_type == 'text':
                text_body = message.get('text', {}).get('body', '').strip().lower()
            else:
                continue
                
            wa_id = message.get('from')
            if not wa_id:
                continue
                
            clean_phone = ''.join([c for c in str(wa_id) if c.isdigit() or c == '+'])
            
            # Find the channel
            channel = self.env['discuss.channel'].sudo().search([
                ('channel_type', '=', 'whatsapp'),
                ('whatsapp_number', '=', clean_phone),
                ('wa_account_id', '=', self.id)
            ], limit=1)
            
            if not channel:
                continue
                
            # Check for 24 hours inactivity to reset
            last_msgs = self.env['mail.message'].sudo().search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
                ('message_type', '!=', 'notification')
            ], order='date desc', limit=2)
            
            if len(last_msgs) == 2:
                time_diff = last_msgs[0].date - last_msgs[1].date
                if time_diff.total_seconds() > 24 * 60 * 60:
                    channel.wa_bot_state = False
                    channel.wa_agent_id = False
                    channel.wa_department = False

            # text_body is already extracted above
            
            if not channel.wa_bot_state or channel.wa_bot_state == 'idle':
                channel.wa_bot_state = 'ask_department'
                departments = self.env['hr.department'].sudo().search([])
                if not departments:
                    self._send_bot_reply(channel, "Welcome! No departments are currently available.")
                    return
                
                fallback_lines = ["Welcome! Which department do you need support from?"]
                for i, d in enumerate(departments):
                    fallback_lines.append(f"{i+1}. {d.name}")
                    
                interactive = {
                    "type": "list",
                    "body": {"text": "Welcome! Which department do you need support from?"},
                    "action": {
                        "button": "Departments",
                        "sections": [{
                            "title": "Departments",
                            "rows": [{"id": str(i+1), "title": d.name[:24]} for i, d in enumerate(departments[:10])]
                        }]
                    }
                }
                    
                self._send_bot_reply(channel, "\n".join(fallback_lines), interactive_payload=interactive)
                
            elif channel.wa_bot_state == 'ask_department':
                departments = self.env['hr.department'].sudo().search([])
                selected_dept = False
                try:
                    idx = int(text_body) - 1
                    if 0 <= idx < len(departments):
                        selected_dept = departments[idx]
                except ValueError:
                    pass
                
                if selected_dept:
                    channel.wa_department = selected_dept.id
                    channel.wa_bot_state = 'ask_agent'
                    
                    employees = self.env['hr.employee'].sudo().search([('department_id', '=', selected_dept.id), ('user_id', '!=', False)])
                    wa_users = self.env['res.users'].sudo().search([('wa_department', '=', selected_dept.id)])
                    agents = (employees.mapped('user_id') | wa_users)
                    if not agents:
                        channel.wa_bot_state = 'routed'
                        channel._wa_bot_route_chat()
                        self._send_bot_reply(channel, f"Your chat has been successfully transferred to the {selected_dept.name} department under any available agent. Your issue will be solved soon, and we will get back to you when done.")
                    else:
                        agent_list = "\n".join([f"{i+1}. {a.name}" for i, a in enumerate(agents)])
                        msg = f"Please select an individual in {selected_dept.name} to speak with:\n{agent_list}\n0. Any available agent"
                        
                        rows = [{"id": str(i+1), "title": a.name[:24]} for i, a in enumerate(agents[:9])]
                        rows.append({"id": "0", "title": "Any available agent"})
                        
                        interactive = {
                            "type": "list",
                            "body": {"text": f"Please select an individual in {selected_dept.name} to speak with:"},
                            "action": {
                                "button": "Agents",
                                "sections": [{
                                    "title": "Agents",
                                    "rows": rows
                                }]
                            }
                        }
                        self._send_bot_reply(channel, msg, interactive_payload=interactive)
                else:
                    fallback_lines = ["Invalid selection. Which department do you need support from?"]
                    for i, d in enumerate(departments):
                        fallback_lines.append(f"{i+1}. {d.name}")
                        
                    interactive = {
                        "type": "list",
                        "body": {"text": "Invalid selection. Which department do you need support from?"},
                        "action": {
                            "button": "Departments",
                            "sections": [{
                                "title": "Departments",
                                "rows": [{"id": str(i+1), "title": d.name[:24]} for i, d in enumerate(departments[:10])]
                            }]
                        }
                    }
                    self._send_bot_reply(channel, "\n".join(fallback_lines), interactive_payload=interactive)
                    
            elif channel.wa_bot_state == 'ask_agent':
                if text_body == '0' or text_body == 'any':
                    channel.wa_agent_id = False
                    channel.wa_bot_state = 'routed'
                    channel._wa_bot_route_chat()
                    self._send_bot_reply(channel, f"Your chat has been successfully transferred to the {channel.wa_department.name} department under any available agent. Your issue will be solved soon, and we will get back to you when done.")
                else:
                    employees = self.env['hr.employee'].sudo().search([('department_id', '=', channel.wa_department.id), ('user_id', '!=', False)])
                    wa_users = self.env['res.users'].sudo().search([('wa_department', '=', channel.wa_department.id)])
                    agents = (employees.mapped('user_id') | wa_users)
                    try:
                        idx = int(text_body) - 1
                        if 0 <= idx < len(agents):
                            channel.wa_agent_id = agents[idx].id
                            channel.wa_bot_state = 'routed'
                            channel._wa_bot_route_chat()
                            self._send_bot_reply(channel, f"Your chat has been successfully transferred to the {channel.wa_department.name} department under {agents[idx].name}. Your issue will be solved soon, and we will get back to you when done.")
                        else:
                            self._send_bot_reply(channel, "Invalid selection. Please select an individual or 0 for Any.")
                    except ValueError:
                        self._send_bot_reply(channel, "Invalid selection. Please reply with a number.")

    def _send_bot_reply(self, channel, body_text, interactive_payload=None):
        try:
            # Always post as a comment so Odoo doesn't automatically send a WhatsApp text message
            mail_msg = channel.sudo().message_post(
                body=body_text,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.ref('base.partner_root').id,
            )
            
            # Send via whatsapp api natively
            phone = channel.whatsapp_number or (channel.whatsapp_partner_id and channel.whatsapp_partner_id.phone)
            if phone:
                account = channel.wa_account_id
                if account.phone_uid and account.token:
                    import requests
                    url = f"https://graph.facebook.com/v19.0/{account.phone_uid}/messages"
                    headers = {
                        "Authorization": f"Bearer {account.token}",
                        "Content-Type": "application/json"
                    }
                    if interactive_payload:
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": phone,
                            "type": "interactive",
                            "interactive": interactive_payload
                        }
                    else:
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": phone,
                            "type": "text",
                            "text": {"body": body_text}
                        }
                    try:
                        requests.post(url, headers=headers, json=payload, timeout=5)
                    except Exception:
                        pass
                else:
                    wa_msg = self.env['whatsapp.message'].sudo().create({
                        'mobile_number': phone,
                        'wa_account_id': channel.wa_account_id.id,
                        'mail_message_id': mail_msg.id,
                        'state': 'outgoing',
                        'message_type': 'outbound',
                        'body': body_text,
                    })
                    wa_msg._send(force_send_by_cron=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Failed to send bot reply: %s", e)

    @api.model
    def delete_whatsapp_chat(self, channel_id):
        """ Completely deletes a whatsapp chat (discuss.channel) """
        if not self.env.is_admin():
            return {'success': False, 'error': 'Only administrators can delete chats.'}
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if channel.exists():
                # We first unlink all mail.messages related to this channel just in case
                messages = self.env['mail.message'].sudo().search([
                    ('model', '=', 'discuss.channel'),
                    ('res_id', '=', channel.id)
                ])
                messages.unlink()
                # Then unlink the channel
                channel.unlink()
                return {'success': True}
            return {'success': False, 'error': 'Channel not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def delete_whatsapp_message(self, message_id):
        """ Deletes a specific mail.message """
        if not self.env.is_admin():
            return {'success': False, 'error': 'Only administrators can delete messages.'}
        try:
            message = self.env['mail.message'].sudo().browse(int(message_id))
            if message.exists():
                message.unlink()
                return {'success': True}
            return {'success': False, 'error': 'Message not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def mark_whatsapp_web_messages_read(self, channel_id):
        channel = self.env['discuss.channel'].browse(int(channel_id))
        if channel.exists() and channel.wa_is_unread_global:
            channel.sudo().write({'wa_is_unread_global': False})

        # Find the user's member record for this channel
        member = self.env['discuss.channel.member'].search([
            ('channel_id', '=', int(channel_id)),
            ('partner_id', '=', self.env.user.partner_id.id)
        ], limit=1)
        
        if member:
            # Find the last message in this channel
            last_message = self.env['mail.message'].search([
                ('res_id', '=', int(channel_id)),
                ('model', '=', 'discuss.channel'),
            ], order='id desc', limit=1)
            
            if last_message:
                # Mark as seen up to the last message, clearing the unread counter
                member._mark_as_read(last_message.id)
        
        return True

    @api.model
    def sync_device_contacts(self, contacts):
        """
        Receives a list of contacts from Flutter [{'name': '...', 'phone': '...'}].
        Creates res.partner records for those that don't exist by phone number.
        """
        Partner = self.env['res.partner'].sudo()
        results = []
        for contact in contacts:
            phone = contact.get('phone')
            name = contact.get('name')
            if not phone or not name:
                continue
                
            # Basic cleanup of phone number for searching
            clean_phone = ''.join([c for c in str(phone) if c.isdigit() or c == '+'])
            if not clean_phone:
                continue
                
            if not name:
                name = phone
                
            existing = Partner.search([
                ('phone', '=', phone)
            ], limit=1)
            
            if not existing:
                existing = Partner.search([
                    ('phone', 'ilike', clean_phone)
                ], limit=1)
            
            if existing:
                results.append({'id': existing.id, 'name': existing.name, 'phone': existing.phone, 'status': 'existing'})
            else:
                try:
                    new_partner = Partner.create({
                        'name': name,
                        'phone': phone,
                    })
                    results.append({'id': new_partner.id, 'name': new_partner.name, 'phone': new_partner.phone, 'status': 'created'})
                except Exception as e:
                    _logger.error(f"Failed to create partner {name}: {e}")
                    pass
                
        return {'success': True, 'contacts': results}

    @api.model
    def get_contacts_for_new_chat(self):
        """ Fetch all contacts that have a phone number to start a new chat with. """
        domain = [('phone', '!=', False)]
        contacts = self.env['res.partner'].sudo().search_read(
            domain, ['id', 'name', 'phone'], order='name asc'
        )
        import re
        for c in contacts:
            if c.get('name'):
                c['name'] = re.sub(r'\s*\(\s*School\s*\)', '', c['name'], flags=re.IGNORECASE).strip()
        return contacts

    @api.model
    def get_or_create_whatsapp_chat(self, partner_id, wa_account_id):
        """ Returns the existing whatsapp channel for a partner and account, or creates one. """
        partner = self.env['res.partner'].sudo().browse(int(partner_id))
        if not partner.exists():
            return {'success': False, 'error': 'Partner not found'}
            
        account = self.sudo().browse(int(wa_account_id))
        if not account.exists():
            return {'success': False, 'error': 'Account not found'}
            
        domain = [
            ('channel_type', '=', 'whatsapp'),
            ('whatsapp_partner_id', '=', partner.id),
            ('wa_account_id', '=', account.id)
        ]
        channel = self.env['discuss.channel'].sudo().search(domain, limit=1)
        
        if channel:
            return {'success': True, 'channel_id': channel.id}
            
        phone = partner.phone
        clean_phone = ''.join([c for c in str(phone) if c.isdigit()]) if phone else ''
        
        # Create new channel
        members = [(0, 0, {'partner_id': self.env.user.partner_id.id})]
        if partner.id != self.env.user.partner_id.id:
            members.append((0, 0, {'partner_id': partner.id}))
            
        new_channel = self.env['discuss.channel'].sudo().create({
            'name': partner.name,
            'channel_type': 'whatsapp',
            'whatsapp_partner_id': partner.id,
            'whatsapp_number': clean_phone,
            'wa_account_id': account.id,
            'company_id': account.company_id.id if account.company_id else False,
            'channel_member_ids': members
        })
        
        return {'success': True, 'channel_id': new_channel.id}

    @api.model
    def create_chat_from_number(self, number, wa_account_id):
        account = self.sudo().browse(int(wa_account_id))
        if not account.exists():
            return {'success': False, 'error': 'Account not found'}
            
        clean_phone = ''.join([c for c in str(number) if c.isdigit()])
        number = clean_phone
            
        if not clean_phone:
            return {'success': False, 'error': 'Invalid number'}
            
        # First check if a channel with this whatsapp_number already exists!
        # This prevents unique constraint violations if the partner phone is formatted differently.
        existing_channel = self.env['discuss.channel'].sudo().search([
            ('channel_type', '=', 'whatsapp'),
            ('whatsapp_number', '=', clean_phone),
            ('wa_account_id', '=', account.id)
        ], limit=1)
        
        if existing_channel:
            return {'success': True, 'channel_id': existing_channel.id}
            
        partner = self.env['res.partner'].sudo().search([
            ('phone', '=', number)
        ], limit=1)
        
        if not partner:
            partner = self.env['res.partner'].sudo().search([
                ('phone', 'ilike', clean_phone)
            ], limit=1)
        
        if not partner:
            try:
                partner = self.env['res.partner'].sudo().create({
                    'name': number,
                    'phone': number,
                })
            except Exception as e:
                return {'success': False, 'error': f"Failed to create contact: {e}"}
            
        try:
            return self.get_or_create_whatsapp_chat(partner.id, wa_account_id)
        except Exception as e:
            return {'success': False, 'error': f"Failed to create chat: {e}"}

    @api.model
    def update_contact_name(self, channel_id, new_name):
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if not channel.exists():
                return {'success': False, 'error': 'Channel not found'}
                
            channel.name = new_name
            if channel.whatsapp_partner_id:
                channel.whatsapp_partner_id.name = new_name
                
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def send_whatsapp_template(self, channel_id, template_id):
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if not channel.exists():
                return {'success': False, 'error': 'Channel not found'}

            template = self.env['whatsapp.template'].sudo().browse(int(template_id))
            if not template.exists():
                return {'success': False, 'error': 'Template not found'}

            if template.status != 'approved':
                return {'success': False, 'error': f'Template is not approved (status: {template.status})'}

            partner = channel.whatsapp_partner_id
            phone = channel.whatsapp_number or (partner.phone if partner else False)

            if not partner and phone:
                partner = self.env['res.partner'].sudo().search([('phone', 'ilike', phone)], limit=1)
                if not partner:
                    partner = self.env['res.partner'].sudo().create({
                        'name': phone,
                        'phone': phone,
                    })
                channel.sudo().write({'whatsapp_partner_id': partner.id})

            if not partner:
                return {'success': False, 'error': 'Channel has no partner attached and no phone number to create one'}

            if not phone:
                return {'success': False, 'error': 'No phone number found for contact'}

            # Force international E.164 format (with '+') so Odoo's core whatsapp module doesn't fail on country fallback
            clean_phone = ''.join(filter(str.isdigit, phone))
            if clean_phone:
                phone = '+' + clean_phone
            else:
                return {'success': False, 'error': 'Phone number is invalid (no digits found)'}

            wa_account = channel.wa_account_id
            if not wa_account:
                wa_account = self.sudo().search([], limit=1)
            if not wa_account:
                return {'success': False, 'error': 'No WhatsApp account found'}

            # Post the mail.message on res.partner so that mail_message_id.model == 'res.partner'
            # This must match the template's model field (all templates use res.partner)
            mail_msg = partner.sudo().message_post(
                body=f'[WhatsApp Template Sent: {template.template_name}]',
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.user.partner_id.id,
            )

            # Build free_text_json to fill {{1}}, {{2}}... placeholders in the template body.
            # All templates have `field_type=free_text` variables — we default to the contact name.
            free_text_json = {}
            free_text_vars = template.variable_ids.filtered(
                lambda v: v.line_type == 'body' and v.field_type == 'free_text'
            ).sorted(lambda v: v._extract_variable_index() or 0)
            contact_name = partner.name or ''
            for i, var in enumerate(free_text_vars, start=1):
                free_text_json[f'free_text_{i}'] = contact_name

            # Build the rendered template body to display in the chat
            import re as _re
            rendered_body = template.body or ''
            for i, var in enumerate(free_text_vars, start=1):
                rendered_body = _re.sub(r'\{\{' + str(i) + r'\}\}', contact_name, rendered_body)

            # Create the whatsapp.message that drives the actual Meta API call
            wa_msg = self.env['whatsapp.message'].sudo().create({
                'mobile_number': phone,
                'wa_template_id': template.id,
                'wa_account_id': wa_account.id,
                'mail_message_id': mail_msg.id,
                'state': 'outgoing',
                'message_type': 'outbound',
                'free_text_json': free_text_json,
            })

            # Send immediately (synchronously, not via cron)
            wa_msg._send(force_send_by_cron=False)

            # Check result
            wa_msg.invalidate_recordset()
            if wa_msg.state == 'error':
                err = wa_msg.failure_reason or wa_msg.failure_type or 'Send failed'
                _logger.warning("Template send failed: %s", err)
                return {'success': False, 'error': err}

            # Also post the rendered template text in the channel chat so the agent can see it
            from odoo.tools import html2plaintext
            channel_msg_body = rendered_body
            try:
                chan_msg = channel.sudo().message_post(
                    body=channel_msg_body,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=self.env.user.partner_id.id,
                )
                sent_date = chan_msg.date.strftime('%Y-%m-%d %H:%M:%S') if chan_msg.date else False
            except Exception:
                sent_date = False

            return {'success': True, 'body': rendered_body, 'sent_date': sent_date}
        except Exception as e:
            _logger.exception("Error in send_whatsapp_template")
            return {'success': False, 'error': str(e)}

    @api.model
    def get_profile_settings(self, account_id):
        account = self.sudo().browse(int(account_id))
        if account.exists():
            return {
                'name': account.name,
                'phone_uid': account.phone_uid if hasattr(account, 'phone_uid') else '',
                'phone': account.phone_number if hasattr(account, 'phone_number') and account.phone_number and account.phone_number.lower() != 'api' else (account.name if account.name and any(c.isdigit() for c in account.name) else (account.phone_uid if hasattr(account, 'phone_uid') else '')),
                'image_1920': account.image_1920 if hasattr(account, 'image_1920') else False,
            }
        return {}
