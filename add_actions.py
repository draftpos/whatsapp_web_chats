import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Update JS
js_path = os.path.join(base, "static", "src", "js", "chats.js")
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

# Add action service setup
if 'this.actionService = useService("action");' not in js:
    js = js.replace('this.orm = useService("orm");', 'this.orm = useService("orm");\n        this.actionService = useService("action");')

if 'async openAddProduct()' not in js:
    js = js.replace('async loadCatalogue() {', """
    async openAddProduct() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            views: [[false, 'form']],
            target: 'new',
            context: { 'default_is_wasphere_catalogue': true }
        }, {
            onClose: async () => {
                await this.loadCatalogue();
            }
        });
    }

    async openAccountSettings() {
        if (!this.state.selectedAccount) return;
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'wasphere.account',
            res_id: parseInt(this.state.selectedAccount),
            views: [[false, 'form']],
            target: 'new',
        }, {
            onClose: async () => {
                await this.loadAccounts();
            }
        });
    }

    async loadCatalogue() {""")
    
with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)


# 2. Update XML
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# Replace Catalogue structure
old_catalogue = """<div class="whatsapp-sidebar" style="width: 100%; max-width: none;">
                    <div class="whatsapp-header sidebar-header-desktop" style="background: var(--ws-bg-sidebar);">
                        <span class="sidebar-title">Product Catalogue</span>
                    </div>"""
new_catalogue = """<div class="whatsapp-sidebar" style="width: 100%; max-width: none;">
                    <div class="whatsapp-header sidebar-header-desktop" style="background: var(--ws-bg-sidebar); display: flex; flex-direction: row; justify-content: space-between; align-items: center; padding: 20px;">
                        <span class="sidebar-title" style="margin: 0;">Product Catalogue</span>
                        <button class="btn btn-primary" t-on-click="openAddProduct" style="background: var(--ws-primary); border: none; border-radius: 8px; font-weight: bold;">
                            <i class="fa fa-plus"></i> Add Product
                        </button>
                    </div>"""
xml = xml.replace(old_catalogue, new_catalogue)

# Replace Settings structure completely
old_settings = """<t t-elif="state.activeTab === 'settings'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Settings</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 20px;">
                         <p style="font-weight: bold; margin-bottom: 10px;">Active Account:</p>
                         <t t-if="state.accounts.length > 0">
                             <select class="whatsapp-account-select" t-model="state.selectedAccount" t-on-change="changeChatAccountDropdown" style="width: 100%; max-width: none; border: 1px solid var(--ws-border); padding: 10px; border-radius: 8px;">
                                 <t t-foreach="state.accounts" t-as="acc" t-key="acc.id">
                                     <option t-att-value="acc.id.toString()"><t t-esc="acc.name"/></option>
                                 </t>
                             </select>
                         </t>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-cog" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">Settings</h2>
                    </div>
                </div>
            </t>"""

new_settings = """<t t-elif="state.activeTab === 'settings'">
                <div class="whatsapp-sidebar" style="width: 100%; max-width: none; background: var(--ws-bg-main);">
                    <div class="whatsapp-header sidebar-header-desktop" style="background: var(--ws-bg-sidebar); border-bottom: 1px solid var(--ws-border);">
                        <span class="sidebar-title" style="padding: 10px 0;">Settings</span>
                    </div>
                    
                    <div style="padding: 30px; display: flex; flex-direction: column; gap: 20px; max-width: 600px; margin: 0 auto; width: 100%; overflow-y: auto;">
                        
                        <!-- Account Selection -->
                        <div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02);">
                            <h3 style="margin: 0 0 5px 0; color: var(--ws-text-main);">Active Connection</h3>
                            <p style="color: var(--ws-text-muted); font-size: 14px; margin-bottom: 20px;">Select which WhatsApp number you want to manage.</p>
                            <t t-if="state.accounts.length > 0">
                                <select class="whatsapp-account-select" t-model="state.selectedAccount" t-on-change="changeChatAccountDropdown" style="width: 100%; border: 1px solid var(--ws-border); padding: 12px; border-radius: 8px; font-size: 15px; background: #f8f9fa;">
                                    <t t-foreach="state.accounts" t-as="acc" t-key="acc.id">
                                        <option t-att-value="acc.id.toString()"><t t-esc="acc.name"/></option>
                                    </t>
                                </select>
                            </t>
                        </div>
                        
                        <!-- Bot Configuration -->
                        <div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3 style="margin: 0 0 5px 0; color: var(--ws-text-main);">Connection Settings</h3>
                                <p style="color: var(--ws-text-muted); font-size: 14px; margin: 0;">Configure the AI auto-responder and API keys for this number.</p>
                            </div>
                            <button class="btn btn-secondary" t-on-click="openAccountSettings" style="background: #f0f2f5; border: 1px solid var(--ws-border); padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; color: var(--ws-text-main);">
                                <i class="fa fa-sliders" style="margin-right: 5px;"></i> Configure
                            </button>
                        </div>
                        
                        <!-- Notifications -->
                        <div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3 style="margin: 0 0 5px 0; color: var(--ws-text-main);">Desktop Notifications</h3>
                                <p style="color: var(--ws-text-muted); font-size: 14px; margin: 0;">Get alerts for incoming messages.</p>
                            </div>
                            <button class="btn btn-primary" style="background: var(--ws-primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer;">
                                Enabled
                            </button>
                        </div>
                    </div>
                </div>
            </t>"""

xml = xml.replace(old_settings, new_settings)

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

print("Add Product button and Settings tab expanded.")
