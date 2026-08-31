import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# ----------------- CSS -----------------
css_path = os.path.join(base, "static", "src", "css", "chats.css")
with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

if 'var(--ws-primary: #0A7CFF;)' not in css:
    # Change to Blue theme
    css = css.replace('--ws-primary: #128C7E;', '--ws-primary: #0A7CFF;')
    css = css.replace('--ws-primary-light: #25D366;', '--ws-primary-light: #4A9FFF;')
    css = css.replace('linear-gradient(145deg, #e3fcf0, #c8f5d6)', 'linear-gradient(145deg, #e3f2fd, #bbdefb)')
    css = css.replace('color: #0b5e40;', 'color: #0d47a1;')
    css = css.replace('rgba(37,211,102,0.3)', 'rgba(10,124,255,0.3)')
    css = css.replace('rgba(37,211,102,0.4)', 'rgba(10,124,255,0.4)')
    css = css.replace('rgba(18, 140, 126, 0.2)', 'rgba(10,124,255,0.2)')

    # Add new styles for unread badge and timestamps
    new_css = """
.unread-badge {
    background-color: var(--ws-primary);
    color: white;
    border-radius: 10px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: bold;
    min-width: 18px;
    text-align: center;
}
.chat-preview {
    font-size: 13px;
    color: var(--ws-text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 200px;
}
.chat-time {
    font-size: 11px;
    color: var(--ws-text-muted);
}
.msg-time {
    font-size: 10px;
    color: rgba(0,0,0,0.45);
    align-self: flex-end;
    margin-top: 4px;
    margin-left: 10px;
}
.message-me .msg-time {
    color: rgba(13, 71, 161, 0.6);
}
"""
    css += new_css

    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)


# ----------------- XML -----------------
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

if 'fa-arrow-left' not in xml:
    # Modify Chat List Item
    old_item = """<div class="chat-name-row" style="display:flex; justify-content:space-between; align-items:center;">
                                    <div class="chat-name"><t t-esc="channel.name || 'Unknown'"/></div>
                                </div>"""
    new_item = """<div class="chat-name-row" style="display:flex; justify-content:space-between; align-items:center; width: 100%;">
                                    <div class="chat-name"><t t-esc="channel.name || 'Unknown'"/></div>
                                    <div class="chat-time"><t t-esc="channel.last_message_date"/></div>
                                </div>
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-top: 5px;">
                                    <div class="chat-preview" t-out="channel.last_message_body || 'Start chatting...'"/>
                                    <t t-if="channel.unread_count > 0">
                                        <div class="unread-badge"><t t-esc="channel.unread_count"/></div>
                                    </t>
                                </div>"""
    xml = xml.replace(old_item, new_item)

    # Modify Main Header (Add back button)
    xml = xml.replace(
        '<div class="chat-avatar" style="margin-right: 15px;">',
        '<i class="fa fa-arrow-left" t-on-click="closeChat" style="margin-right: 15px; font-size: 18px; color: var(--ws-text-muted); cursor: pointer;"></i>\n                            <div class="chat-avatar" style="margin-right: 15px;">'
    )

    # Add timestamp to message bubble
    xml = xml.replace(
        '<div class="message-body" t-esc="msg.bodyText"/>',
        '<div class="message-body" t-out="msg.bodyText"/>\n                                    <span class="msg-time"><t t-esc="msg.timeStr"/></span>'
    )

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml)


# ----------------- JS -----------------
js_path = os.path.join(base, "static", "src", "js", "chats.js")
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

if 'onGlobalKeydown' not in js:
    # Setup event listener for Escape key
    js = js.replace('onWillStart(async () => {', 'onMounted(() => {\n            window.addEventListener("keydown", this.onGlobalKeydown.bind(this));\n        });\n        onWillDestroy(() => {\n            window.removeEventListener("keydown", this.onGlobalKeydown.bind(this));\n        });\n        onWillStart(async () => {')

    js = js.replace('onKeydown(ev) {', 'onGlobalKeydown(ev) {\n        if (ev.key === "Escape") {\n            this.closeChat();\n        }\n    }\n    closeChat() {\n        this.state.selectedChannel = null;\n    }\n    onKeydown(ev) {')

    # Use get_wasphere_channels instead of searchRead
    old_load_channels = """const channels = await this.orm.searchRead(
            "discuss.channel",
            [["channel_type", "=", "whatsapp"], ["wasphere_account_id", "=", parseInt(this.state.selectedAccount)]],
            ["id", "name", "whatsapp_number"]
        );"""
    new_load_channels = """const channels = await this.orm.call(
            "discuss.channel",
            "get_wasphere_channels",
            [parseInt(this.state.selectedAccount)]
        );"""
    js = js.replace(old_load_channels, new_load_channels)

    # Format messages and clear unreads
    js = js.replace('this.state.selectedChannel = channel;', 'this.state.selectedChannel = channel;\n        await this.orm.call("discuss.channel", "mark_channel_read", [channel.id]);\n        channel.unread_count = 0;')

    js = js.replace('isMe: isMe', 'isMe: isMe,\n                timeStr: new Date(msg.date).toLocaleTimeString([], {hour: "2-digit", minute:"2-digit"})')

    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)


# ----------------- PYTHON MODELS -----------------
py_path = os.path.join(base, "models", "discuss_channel.py")
with open(py_path, "r", encoding="utf-8") as f:
    py = f.read()

if 'get_wasphere_channels' not in py:
    backend_logic = """
    @api.model
    def get_wasphere_channels(self, account_id):
        channels = self.search([
            ('channel_type', '=', 'whatsapp'),
            ('wasphere_account_id', '=', int(account_id))
        ])
        res = []
        for ch in channels:
            last_msg = self.env['mail.message'].search([('res_id', '=', ch.id), ('model', '=', 'discuss.channel'), ('message_type', '=', 'comment')], order='id desc', limit=1)
            
            unread = self.env['mail.message'].search_count([
                ('res_id', '=', ch.id),
                ('model', '=', 'discuss.channel'),
                ('needaction', '=', True)
            ])
            if unread == 0 and hasattr(ch, 'message_unread_counter'):
                unread = ch.message_unread_counter
                
            res.append({
                'id': ch.id,
                'name': ch.name,
                'whatsapp_number': ch.whatsapp_number,
                'unread_count': unread,
                'last_message_body': last_msg.body if last_msg else '',
                'last_message_date': last_msg.date.strftime('%H:%M') if last_msg else ''
            })
        res.sort(key=lambda x: x['last_message_date'] or '', reverse=True)
        return res

    @api.model
    def mark_channel_read(self, channel_id):
        channel = self.browse(channel_id)
        if channel.exists():
            messages = self.env['mail.message'].search([
                ('res_id', '=', channel.id),
                ('model', '=', 'discuss.channel'),
                ('needaction', '=', True)
            ])
            if messages:
                messages.sudo().write({'needaction': False})
            
            try:
                channel.channel_seen()
            except Exception:
                pass
            return True
        return False
"""
    py += backend_logic
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(py)

print("Modification complete.")
