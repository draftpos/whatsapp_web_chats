import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Update JS
js_path = os.path.join(base, "static", "src", "js", "chats.js")
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

# Add states for the new data
if "statuses: []" not in js:
    js = js.replace("activeTab: 'chats',", "activeTab: 'chats',\n            statuses: [],\n            calls: [],\n            catalogue: [],")

# Update setTab to fetch data
if "this.loadStatuses();" not in js:
    js = js.replace(
        "this.state.activeTab = tabName;",
        "this.state.activeTab = tabName;\n        if(tabName === 'status') this.loadStatuses();\n        if(tabName === 'calls') this.loadCalls();\n        if(tabName === 'catalogue') this.loadCatalogue();"
    )

    fetch_logic = """
    async loadStatuses() {
        if (!this.state.selectedAccount) return;
        this.state.statuses = await this.orm.call("discuss.channel", "get_wasphere_statuses", [parseInt(this.state.selectedAccount)]);
    }
    async loadCalls() {
        if (!this.state.selectedAccount) return;
        this.state.calls = await this.orm.call("discuss.channel", "get_wasphere_calls", [parseInt(this.state.selectedAccount)]);
    }
    async loadCatalogue() {
        this.state.catalogue = await this.orm.call("discuss.channel", "get_wasphere_catalogue", []);
    }
"""
    js = js.replace("get filteredChannels() {", fetch_logic + "\n    get filteredChannels() {")

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)

# 2. Update XML
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# Replace Nav Rail Settings with Catalogue + Settings
if 'fa-shopping-bag' not in xml:
    xml = xml.replace(
        '<div t-attf-class="nav-item {{ state.activeTab === \'settings\' ? \'active\' : \'\' }}" title="Settings" t-on-click="() => this.setTab(\'settings\')"><i class="fa fa-cog"></i></div>',
        '<div t-attf-class="nav-item {{ state.activeTab === \'catalogue\' ? \'active\' : \'\' }}" title="Store/Catalogue" t-on-click="() => this.setTab(\'catalogue\')"><i class="fa fa-shopping-bag"></i></div>\n                    <div t-attf-class="nav-item {{ state.activeTab === \'settings\' ? \'active\' : \'\' }}" title="Settings" t-on-click="() => this.setTab(\'settings\')"><i class="fa fa-cog"></i></div>'
    )

# Replace Avatar logic in Chat list
old_avatar = '<div class="chat-avatar"><t t-esc="(channel.name and channel.name.length > 0) ? channel.name[0].toUpperCase() : \'?\'"/></div>'
new_avatar = """<t t-if="channel.partner_image">
                                        <img t-attf-src="data:image/jpeg;base64,{{channel.partner_image}}" class="chat-avatar" style="object-fit: cover; border: none;"/>
                                    </t>
                                    <t t-else="">
                                        <div class="chat-avatar"><t t-esc="(channel.name and channel.name.length > 0) ? channel.name[0].toUpperCase() : '?'"/></div>
                                    </t>"""
xml = xml.replace(old_avatar, new_avatar)

# Replace Header Avatar
old_header_avatar = '<div class="chat-avatar" style="margin-right: 15px;"><t t-esc="(state.selectedChannel.name and state.selectedChannel.name.length > 0) ? state.selectedChannel.name[0].toUpperCase() : \'?\'"/></div>'
new_header_avatar = """<t t-if="state.selectedChannel.partner_image">
                                    <img t-attf-src="data:image/jpeg;base64,{{state.selectedChannel.partner_image}}" class="chat-avatar" style="object-fit: cover; border: none; margin-right: 15px;"/>
                                </t>
                                <t t-else="">
                                    <div class="chat-avatar" style="margin-right: 15px;"><t t-esc="(state.selectedChannel.name and state.selectedChannel.name.length > 0) ? state.selectedChannel.name[0].toUpperCase() : '?'"/></div>
                                </t>"""
xml = xml.replace(old_header_avatar, new_header_avatar)

# Replace Status Tab
old_status = """<t t-elif="state.activeTab === 'status'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Status</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 20px; text-align: center; color: var(--ws-text-muted);">
                        <i class="fa fa-circle-o-notch" style="font-size: 40px; margin-bottom: 15px; color: #dfe5e7;"></i>
                        <p>No recent updates</p>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-circle-o-notch" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">Click on a contact to view their status updates</h2>
                    </div>
                </div>
            </t>"""
new_status = """<t t-elif="state.activeTab === 'status'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Status</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 10px;">
                        <t t-if="state.statuses.length === 0">
                            <div style="padding: 20px; text-align: center; color: var(--ws-text-muted);">No recent updates</div>
                        </t>
                        <t t-foreach="state.statuses" t-as="st" t-key="st.id">
                            <div class="whatsapp-chat-item">
                                <div class="chat-avatar-container" style="border: 2px solid var(--ws-primary); border-radius: 50%; padding: 2px;">
                                    <t t-if="st.partner_image">
                                        <img t-attf-src="data:image/jpeg;base64,{{st.partner_image}}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;"/>
                                    </t>
                                    <t t-else="">
                                        <div class="chat-avatar"><t t-esc="st.partner_name[0].toUpperCase()"/></div>
                                    </t>
                                </div>
                                <div class="chat-info" style="margin-left: 15px;">
                                    <div class="chat-name"><t t-esc="st.partner_name"/></div>
                                    <div class="chat-time"><t t-esc="st.time"/></div>
                                </div>
                            </div>
                        </t>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-circle-o-notch" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">Click on a contact to view their status updates</h2>
                    </div>
                </div>
            </t>"""
xml = xml.replace(old_status, new_status)

# Replace Calls Tab
old_calls = """<t t-elif="state.activeTab === 'calls'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Calls</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 20px; text-align: center; color: var(--ws-text-muted);">
                         <p>Your call history will appear here.</p>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-phone" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">No recent calls</h2>
                    </div>
                </div>
            </t>"""
new_calls = """<t t-elif="state.activeTab === 'calls'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Calls</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 10px;">
                        <t t-if="state.calls.length === 0">
                            <div style="padding: 20px; text-align: center; color: var(--ws-text-muted);">No recent calls</div>
                        </t>
                        <t t-foreach="state.calls" t-as="call" t-key="call.id">
                            <div class="whatsapp-chat-item">
                                <div class="chat-avatar-container">
                                    <t t-if="call.partner_image">
                                        <img t-attf-src="data:image/jpeg;base64,{{call.partner_image}}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;"/>
                                    </t>
                                    <t t-else="">
                                        <div class="chat-avatar"><t t-esc="call.partner_name[0].toUpperCase()"/></div>
                                    </t>
                                </div>
                                <div class="chat-info" style="margin-left: 15px; flex: 1;">
                                    <div t-attf-class="chat-name {{ call.direction === 'missed' ? 'text-danger' : '' }}"><t t-esc="call.partner_name"/></div>
                                    <div class="chat-time" style="display:flex; align-items:center; gap: 5px;">
                                        <i t-attf-class="fa {{ call.direction === 'missed' ? 'fa-arrow-down text-danger' : (call.direction === 'inbound' ? 'fa-arrow-down text-success' : 'fa-arrow-up text-success') }}"></i>
                                        <t t-esc="call.time"/>
                                    </div>
                                </div>
                                <i t-attf-class="fa {{ call.type === 'video' ? 'fa-video-camera' : 'fa-phone' }}" style="color: var(--ws-primary); font-size: 18px;"></i>
                            </div>
                        </t>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-phone" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">Select a call log to view details</h2>
                    </div>
                </div>
            </t>"""
xml = xml.replace(old_calls, new_calls)

# Replace Catalogue (Inject at the end before </t>)
catalogue_xml = """
            <t t-elif="state.activeTab === 'catalogue'">
                <div class="whatsapp-sidebar" style="width: 100%; max-width: none;">
                    <div class="whatsapp-header sidebar-header-desktop" style="background: var(--ws-bg-sidebar);">
                        <span class="sidebar-title">Product Catalogue</span>
                    </div>
                    <div style="padding: 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; overflow-y: auto; height: 100%; background: var(--ws-bg-main);">
                        <t t-if="state.catalogue.length === 0">
                            <p style="color: var(--ws-text-muted);">No products marked for WhatsApp Catalogue.</p>
                        </t>
                        <t t-foreach="state.catalogue" t-as="prod" t-key="prod.id">
                            <div style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid var(--ws-border);">
                                <t t-if="prod.image">
                                    <img t-attf-src="data:image/jpeg;base64,{{prod.image}}" style="width: 100%; height: 150px; object-fit: cover;"/>
                                </t>
                                <t t-else="">
                                    <div style="width: 100%; height: 150px; background: #f0f2f5; display:flex; align-items:center; justify-content:center;"><i class="fa fa-box" style="font-size: 40px; color: #ccc;"></i></div>
                                </t>
                                <div style="padding: 15px;">
                                    <h4 style="margin: 0 0 5px 0; font-size: 16px;"><t t-esc="prod.name"/></h4>
                                    <p style="color: var(--ws-primary); font-weight: bold; margin: 0;">$<t t-esc="prod.price"/></p>
                                </div>
                            </div>
                        </t>
                    </div>
                </div>
            </t>
"""
if "state.activeTab === 'catalogue'" not in xml:
    xml = xml.replace("</t>\n\n        </div>\n    </t>", catalogue_xml + "\n            </t>\n\n        </div>\n    </t>")


with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

print("Frontend XML/JS updated for real data.")
