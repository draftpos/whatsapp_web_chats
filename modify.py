import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Modify chats_template.xml
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

if 'fa-exchange' not in xml:
    xml = xml.replace(
        '<i class="fa fa-search" style="cursor: pointer;"></i>',
        '<i class="fa fa-exchange" title="Transfer Chat" t-on-click="openTransferModal" style="cursor: pointer; transition: color 0.2s;" onmouseover="this.style.color=\'var(--ws-primary)\'" onmouseout="this.style.color=\'var(--ws-text-muted)\'"></i>\n                            <i class="fa fa-search" style="cursor: pointer;"></i>'
    )

    transfer_modal = """
            <!-- Transfer Chat Modal -->
            <t t-if="state.isTransferModalOpen">
                <div class="modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); backdrop-filter: blur(5px); z-index: 9999; display: flex; align-items: center; justify-content: center;">
                    <div class="modal-content" style="background: white; width: 450px; border-radius: 16px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 16px 40px rgba(0,0,0,0.12); border: 1px solid rgba(0,0,0,0.05);">
                        <div class="modal-header" style="background: #ffffff; color: var(--ws-text-main); padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f0f2f5;">
                            <span style="font-size: 18px; font-weight: 700;">Transfer Chat</span>
                            <i class="fa fa-times" style="cursor: pointer; color: #8696a0; font-size: 20px;" t-on-click="closeTransferModal"></i>
                        </div>
                        <div class="modal-body" style="padding: 24px; background: white; max-height: 400px; overflow-y: auto;">
                            <p style="color: #8696a0; font-size: 14px; margin-bottom: 15px;">Select an agent to transfer this chat to:</p>
                            <t t-foreach="state.users" t-as="user" t-key="user.id">
                                <div class="user-transfer-item" t-on-click="() => this.transferChat(user.id)" style="padding: 12px; border-bottom: 1px solid #f0f2f5; display: flex; align-items: center; cursor: pointer;">
                                    <div class="chat-avatar" style="width: 35px; height: 35px; margin-right: 15px; font-size: 14px;"><t t-esc="user.name[0].toUpperCase()"/></div>
                                    <span style="font-size: 15px; font-weight: 500; color: var(--ws-text-main);"><t t-esc="user.name"/></span>
                                </div>
                            </t>
                        </div>
                    </div>
                </div>
            </t>
        </div>
"""
    xml = xml.replace('        </div>\n    </t>', transfer_modal + '    </t>')
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml)

# 2. Modify chats.js
js_path = os.path.join(base, "static", "src", "js", "chats.js")
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

if 'isTransferModalOpen' not in js:
    js = js.replace(
        'newNumberQuery: "",',
        'newNumberQuery: "",\n            isTransferModalOpen: false,\n            users: [],'
    )

    transfer_logic = """
    async openTransferModal() {
        this.state.isTransferModalOpen = true;
        this.state.users = await this.orm.searchRead("res.users", [["active", "=", true]], ["id", "name"]);
    }

    closeTransferModal() {
        this.state.isTransferModalOpen = false;
    }

    async transferChat(userId) {
        if (!this.state.selectedChannel) return;
        try {
            await this.orm.call(
                "discuss.channel",
                "transfer_whatsapp_chat",
                [this.state.selectedChannel.id, userId]
            );
            this.closeTransferModal();
            this.state.selectedChannel = null;
            await this.loadChannels();
        } catch (e) {
            console.error("Transfer failed", e);
        }
    }
}
"""
    js = js.replace('\n}\n\nChatsAction.template', transfer_logic + '\nChatsAction.template')
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)

# 3. Modify discuss_channel.py
models_path = os.path.join(base, "models", "discuss_channel.py")
with open(models_path, "r", encoding="utf-8") as f:
    py = f.read()

if 'transfer_whatsapp_chat' not in py:
    py_logic = """
    @api.model
    def transfer_whatsapp_chat(self, channel_id, user_id):
        channel = self.browse(channel_id)
        user = self.env['res.users'].browse(user_id)
        if channel.exists() and user.exists():
            partner_id = user.partner_id.id
            channel.add_members([partner_id])
            channel.message_post(body=f"Chat was transferred to {user.name}.", message_type='notification')
            return True
        return False
"""
    py = py + "\n" + py_logic
    with open(models_path, "w", encoding="utf-8") as f:
        f.write(py)

# 4. Modify wasphere_account.py
account_path = os.path.join(base, "models", "wasphere_account.py")
with open(account_path, "r", encoding="utf-8") as f:
    acc = f.read()

if 'sync_whatsapp_contacts' not in acc:
    acc_logic = """
    @api.model
    def sync_whatsapp_contacts(self, account_id):
        account = self.browse(account_id)
        if not account.exists():
            return False
        # Here we would make a request to the Wasphere API to get contacts
        # e.g., requests.get(f"{account.api_url}/sessions/{account.id}/contacts")
        # For now, we return a success status that flutter app or cron can listen to
        return True
"""
    acc = acc + "\n" + acc_logic
    with open(account_path, "w", encoding="utf-8") as f:
        f.write(acc)

# 5. Modify webhook.py
webhook_path = os.path.join(base, "controllers", "webhook.py")
with open(webhook_path, "r", encoding="utf-8") as f:
    web = f.read()

if 'api_flutter_sync_contacts' not in web:
    web_logic = """
    @http.route('/api/flutter/sync_contacts', type='json', auth='public', methods=['POST'], csrf=False)
    def api_flutter_sync_contacts(self, account_id=None, **kwargs):
        # JSON-RPC endpoint for Flutter to trigger sync and fetch
        if account_id:
            request.env['wasphere.account'].sudo().sync_whatsapp_contacts(account_id)
        
        # Return all synced contacts to flutter
        contacts = request.env['res.partner'].sudo().search_read([('phone', '!=', False)], ['id', 'name', 'phone'])
        return {'success': True, 'contacts': contacts}
"""
    web = web + "\n" + web_logic
    with open(webhook_path, "w", encoding="utf-8") as f:
        f.write(web)
