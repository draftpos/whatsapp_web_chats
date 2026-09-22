from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    wa_reaction = fields.Char(string='WhatsApp Reaction', help='Emoji reaction from the user')
    wa_reaction_me = fields.Char(string='My Reaction', help='Emoji reaction sent by me')
    wa_is_starred = fields.Boolean(string='Starred (Local)')
    wa_is_pinned = fields.Boolean(string='Pinned (Local)')

    def _send(self, force_send_by_cron=False):
        if self.env.context.get('wa_web_chats_defer_send'):
            return
        return super()._send(force_send_by_cron=force_send_by_cron)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('is_compressing_video'):
            for v in vals_list:
                v['state'] = 'cancel'
                
        records = super().create(vals_list)
        for rec in records:
            if not rec.company_id and rec.wa_account_id and rec.wa_account_id.company_id:
                rec.company_id = rec.wa_account_id.company_id.id
            if rec.mail_message_id:
                # Find the copied discuss.channel message
                copied_msg = self.env['mail.message'].sudo().search([
                    ('model', '=', 'discuss.channel'),
                    ('message_type', 'in', ('whatsapp_message', 'comment')),
                    ('body', '=', rec.mail_message_id.body),
                    ('res_id', '!=', False)
                ], order='id desc', limit=1)
                
                if copied_msg:
                    new_author_id = copied_msg.author_id.id
                    if rec.message_type == 'inbound':
                        # Customer message (should be left)
                        session = self.env['wa.chatbot.session'].sudo().search([('id', '=', rec.chatbot_session_id.id)], limit=1) if hasattr(rec, 'chatbot_session_id') else False
                        if session and session.partner_id:
                            new_author_id = session.partner_id.id
                        else:
                            # Try to find the partner from the whatsapp_number
                            channel = self.env['discuss.channel'].sudo().browse(copied_msg.res_id)
                            if channel.whatsapp_partner_id:
                                new_author_id = channel.whatsapp_partner_id.id
                            else:
                                new_author_id = False # System message
                    elif rec.message_type == 'outbound':
                        # Outbound message (should be right). Use the company's partner or the user who sent it.
                        if rec.is_bot_message:
                            new_author_id = self.env.ref('base.partner_root').id
                        else:
                            new_author_id = rec.create_uid.partner_id.id if rec.create_uid else self.env.ref('base.partner_root').id
                            
                    if copied_msg.author_id.id != new_author_id:
                        copied_msg.sudo().write({'author_id': new_author_id})

        return records

    def _send(self, force_send_by_cron=False, **kwargs):
        if self.env.context.get('is_compressing_video'):
            return
            
        from odoo.tools import html2plaintext
        
        # Meta API throws 'text.body is required' if we send a text message with empty body.
        # Odoo sometimes creates these alongside media messages. Cancel them here before sending.
        handled_directly = self.env['whatsapp.message']
        for msg in self:
            is_audio = False
            has_attachments = bool(msg.mail_message_id.attachment_ids)
            if has_attachments:
                # Check if it's an audio attachment to prevent caption error
                att = msg.mail_message_id.attachment_ids[0]
                if att.mimetype and att.mimetype.startswith('audio/'):
                    is_audio = True
                elif att.mimetype and att.mimetype.startswith('video/'):
                    # Direct Meta API Send for videos to bypass Odoo's broken payload construction
                    import requests
                    import base64
                    import re
                    account = msg.wa_account_id
                    if not account:
                        if msg.mail_message_id.model == 'discuss.channel':
                            account = self.env['discuss.channel'].browse(msg.mail_message_id.res_id).wa_account_id
                            
                    if account and account.token and account.phone_uid:
                        try:
                            clean_phone = re.sub(r'\D', '', str(msg.mobile_number or ''))
                            if not clean_phone:
                                raise Exception(f"Invalid mobile number: {msg.mobile_number}")
                                
                            headers = {'Authorization': f'Bearer {account.token}'}
                            files = {
                                'file': (att.name or 'video.mp4', base64.b64decode(att.datas), 'video/mp4'),
                            }
                            data = {
                                'messaging_product': 'whatsapp',
                                'type': 'video/mp4'
                            }
                            upload_res = requests.post(
                                f"https://graph.facebook.com/v19.0/{account.phone_uid}/media", 
                                headers=headers, data=data, files=files, timeout=60
                            )
                            upload_data = upload_res.json()
                            if 'id' not in upload_data:
                                raise Exception(f"Upload failed: {upload_data}")
                                
                            media_id = upload_data['id']
                            clean_caption = html2plaintext(msg.body or '').strip()
                            
                            payload = {
                                "messaging_product": "whatsapp",
                                "recipient_type": "individual",
                                "to": clean_phone,
                                "type": "video",
                                "video": { 
                                    "id": media_id
                                }
                            }
                            if clean_caption and clean_caption != 'False':
                                payload['video']['caption'] = clean_caption
                                
                            send_res = requests.post(
                                f"https://graph.facebook.com/v19.0/{account.phone_uid}/messages",
                                headers={'Authorization': f'Bearer {account.token}', 'Content-Type': 'application/json'},
                                json=payload, timeout=15
                            )
                            send_data = send_res.json()
                            if 'messages' in send_data:
                                msg.write({'state': 'sent', 'msg_uid': send_data['messages'][0]['id']})
                            else:
                                raise Exception(f"Send failed: {send_data}")
                            handled_directly |= msg
                            continue
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).error("Direct video send error: %s", str(e))
                            msg.write({'state': 'error'})
                            handled_directly |= msg
                            continue
                    
            clean_body = html2plaintext(msg.body or '').strip()
            
            if not has_attachments and (not clean_body or clean_body == 'False'):
                msg.write({'state': 'cancel'})
                
            # Meta API doesn't support 'caption' on audio. Odoo standard adds it if body exists.
            if is_audio and msg.body:
                msg.write({'body': ''})
                
        valid_messages = self.filtered(lambda m: m.state != 'cancel' and m not in handled_directly)
        if not valid_messages:
            return valid_messages
                    
        return super(WhatsAppMessage, valid_messages)._send(force_send_by_cron=force_send_by_cron, **kwargs)
        
    def _send_message(self, **kwargs):
        if self.env.context.get('is_compressing_video'):
            return
            
        from odoo.tools import html2plaintext
        
        # Cancel any bogus empty text messages to avoid Meta API errors
        handled_directly = self.env['whatsapp.message']
        for msg in self:
            is_audio = False
            has_attachments = bool(msg.mail_message_id.attachment_ids)
            if has_attachments:
                # Check if it's an audio attachment to prevent caption error
                att = msg.mail_message_id.attachment_ids[0]
                if att.mimetype and att.mimetype.startswith('audio/'):
                    is_audio = True
                elif att.mimetype and att.mimetype.startswith('video/'):
                    # Direct Meta API Send for videos to bypass Odoo's broken payload construction
                    import requests
                    import base64
                    import re
                    account = msg.wa_account_id
                    if not account:
                        if msg.mail_message_id.model == 'discuss.channel':
                            account = self.env['discuss.channel'].browse(msg.mail_message_id.res_id).wa_account_id
                            
                    if account and account.token and account.phone_uid:
                        try:
                            clean_phone = re.sub(r'\D', '', str(msg.mobile_number or ''))
                            if not clean_phone:
                                raise Exception(f"Invalid mobile number: {msg.mobile_number}")
                                
                            headers = {'Authorization': f'Bearer {account.token}'}
                            files = {
                                'file': (att.name or 'video.mp4', base64.b64decode(att.datas), 'video/mp4'),
                            }
                            data = {
                                'messaging_product': 'whatsapp',
                                'type': 'video/mp4'
                            }
                            upload_res = requests.post(
                                f"https://graph.facebook.com/v19.0/{account.phone_uid}/media", 
                                headers=headers, data=data, files=files, timeout=60
                            )
                            upload_data = upload_res.json()
                            if 'id' not in upload_data:
                                raise Exception(f"Upload failed: {upload_data}")
                                
                            media_id = upload_data['id']
                            clean_caption = html2plaintext(msg.body or '').strip()
                            
                            payload = {
                                "messaging_product": "whatsapp",
                                "recipient_type": "individual",
                                "to": clean_phone,
                                "type": "video",
                                "video": { 
                                    "id": media_id
                                }
                            }
                            if clean_caption and clean_caption != 'False':
                                payload['video']['caption'] = clean_caption
                                
                            send_res = requests.post(
                                f"https://graph.facebook.com/v19.0/{account.phone_uid}/messages",
                                headers={'Authorization': f'Bearer {account.token}', 'Content-Type': 'application/json'},
                                json=payload, timeout=15
                            )
                            send_data = send_res.json()
                            if 'messages' in send_data:
                                msg.write({'state': 'sent', 'msg_uid': send_data['messages'][0]['id']})
                            else:
                                raise Exception(f"Send failed: {send_data}")
                            handled_directly |= msg
                            continue
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).error("Direct video send error: %s", str(e))
                            msg.write({'state': 'error'})
                            handled_directly |= msg
                            continue
                    
            clean_body = html2plaintext(msg.body or '').strip()
            
            if not has_attachments and not msg.wa_template_id and (not clean_body or clean_body == 'False'):
                import logging
                logging.getLogger(__name__).warning("Silently cancelling empty message %s", msg.id)
                msg.write({'state': 'cancel'})
                
            # Meta API doesn't support 'caption' on audio. Odoo standard adds it if body exists.
            if is_audio and msg.body:
                msg.write({'body': ''})
                
        valid_messages = self.filtered(lambda m: m.state != 'cancel' and m not in handled_directly)
        if not valid_messages:
            return valid_messages
                    
        return super(WhatsAppMessage, valid_messages)._send_message(**kwargs)

    @api.model
    def _send_cron(self):
        """ Send all outgoing messages. 
        Overridden to add FOR UPDATE SKIP LOCKED to prevent database locking issues 
        and duplicate message sending when multiple cron threads run.
        """
        # Lock outgoing messages to prevent concurrent crons from picking the same messages
        self.env.cr.execute("""
            SELECT id FROM whatsapp_message 
            WHERE state = 'outgoing'
            ORDER BY wa_template_id DESC 
            LIMIT 500
            FOR UPDATE SKIP LOCKED
        """)
        locked_ids = [row[0] for row in self.env.cr.fetchall()]
        
        if not locked_ids:
            return

        records = self.browse(locked_ids)
        # Call the core _send_message logic.
        # Note: Registry.in_test_mode() was removed in Odoo 17. We always commit in
        # production cron context; tests use their own transaction rollback mechanisms.
        try:
            in_test_mode = self.env.registry.in_test_mode()
        except AttributeError:
            in_test_mode = getattr(self.env.registry, '_is_test_mode', False)
        records._send_message(with_commit=not in_test_mode)
        
        if len(records) == 500:
            self.env.ref('whatsapp.ir_cron_send_whatsapp_queue')._trigger()
