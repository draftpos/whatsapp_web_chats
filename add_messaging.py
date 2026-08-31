import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Update webhook.py
webhook_path = os.path.join(base, "controllers", "webhook.py")
with open(webhook_path, "r", encoding="utf-8") as f:
    webhook = f.read()

new_route = """
    @http.route('/api/flutter/receive_message', type='json', auth='public', methods=['POST'], csrf=False)
    def api_flutter_receive_message(self, **kwargs):
        account_id = kwargs.get('account_id')
        sender_phone = kwargs.get('sender_phone')
        body = kwargs.get('body')
        
        if not account_id or not sender_phone or not body:
            return {'success': False, 'error': 'Missing required fields'}
            
        env = request.env
        
        # 1. Find or create Partner
        partner = env['res.partner'].sudo().search([('phone', '=', sender_phone)], limit=1)
        if not partner:
            partner = env['res.partner'].sudo().create({
                'name': kwargs.get('sender_name') or sender_phone,
                'phone': sender_phone
            })
            
        # 2. Find or create Channel
        channel = env['discuss.channel'].sudo().search([
            ('wasphere_account_id', '=', account_id),
            ('whatsapp_partner_id', '=', partner.id)
        ], limit=1)
        
        if not channel:
            account = env['wasphere.account'].sudo().browse(account_id)
            channel = env['discuss.channel'].sudo().create({
                'name': partner.name,
                'wasphere_account_id': account.id,
                'whatsapp_partner_id': partner.id,
                'channel_type': 'chat'
            })
            
        # 3. Create Mail Message
        msg = env['mail.message'].sudo().create({
            'body': body,
            'model': 'discuss.channel',
            'res_id': channel.id,
            'author_id': partner.id,
            'message_type': 'comment'
        })
        
        # 4. Create whatsapp.message
        env['whatsapp.message'].sudo().create({
            'channel_id': channel.id,
            'body': body,
            'message_id': kwargs.get('message_id') or str(msg.id),
            'is_me': False,
            'status': 'received'
        })
        
        return {'success': True, 'message_id': msg.id, 'channel_id': channel.id}
"""
if 'api_flutter_receive_message' not in webhook:
    webhook += "\n" + new_route
    with open(webhook_path, "w", encoding="utf-8") as f:
        f.write(webhook)


# 2. Update chats.js for polling
js_path = os.path.join(base, "static", "src", "js", "chats.js")
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

poll_logic = """
        // Polling mechanism
        let polling = true;
        const poll = async () => {
            if (!polling) return;
            try {
                if (this.state.selectedChannel) {
                    await this.pollMessages();
                } else if (this.state.selectedAccount && this.state.activeTab === 'chats') {
                    await this.loadChannels(true); // silent load to update list
                }
            } catch (e) {}
            setTimeout(poll, 3000); // Poll every 3 seconds
        };
        poll();
"""

poll_methods = """
    async pollMessages() {
        if (!this.state.selectedChannel) return;
        const msgs = await this.orm.call("discuss.channel", "get_whatsapp_messages", [this.state.selectedChannel.id]);
        if (msgs.length > this.state.messages.length) {
            this.state.messages = msgs;
            this.scrollToBottom();
            await this.loadChannels(true); // Update left side preview
        }
    }
"""

if "const poll = async ()" not in js:
    # Insert in setup
    setup_idx = js.find("this.loadAccounts();")
    if setup_idx != -1:
        js = js[:setup_idx] + "this.loadAccounts();\n" + poll_logic + js[setup_idx+20:]

if "async pollMessages()" not in js:
    js = js.replace("async loadMessages(channelId) {", poll_methods + "\n    async loadMessages(channelId) {")
    
# Modify loadChannels to accept silent param to not cause UI flicker if not necessary, but our loadChannels replaces state.channels entirely, which Owl handles smoothly via virtual dom.
# Let's just do it.
with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)

print("Real-time messaging backend and frontend polling added.")
