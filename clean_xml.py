import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")

with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# Find where settings tab starts
start_idx = xml.find('<t t-elif="state.activeTab === \'settings\'">')

if start_idx != -1:
    # Take everything before it
    clean_xml = xml[:start_idx]
    
    # Append the perfectly formatted Settings tab and close the main wrappers
    settings_tab = """<t t-elif="state.activeTab === 'settings'">
                <div class="whatsapp-sidebar" style="width: 100%; max-width: none; background: var(--ws-bg-main);">
                    <!-- Header -->
                    <div class="sidebar-header-desktop" style="background: var(--ws-bg-sidebar); border-bottom: 1px solid var(--ws-border); display: flex; align-items: flex-start; justify-content: center; flex-direction: column;">
                        <span class="sidebar-title" style="margin: 0; font-size: 20px; font-weight: 600;">Settings</span>
                    </div>
                    
                    <!-- Content Wrapper with Scroll -->
                    <div style="flex: 1; overflow-y: auto; width: 100%; padding: 30px 20px;">
                        <!-- Centered Cards -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; width: 100%; align-items: start;">
                            
                            <!-- Account Selection -->
                            <div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column; height: 100%; justify-content: flex-start;">
                                <h3 style="margin: 0 0 5px 0; color: var(--ws-text-main);">Active Connection</h3>
                                <p style="color: var(--ws-text-muted); font-size: 14px; margin-bottom: 20px;">Select which WhatsApp number you want to manage.</p>
                                
                                <select class="whatsapp-account-select" t-model="state.selectedAccount" t-on-change="changeChatAccountDropdown" style="width: 100%; border: 1px solid var(--ws-border); padding: 12px; border-radius: 8px; font-size: 15px; background: #f8f9fa;">
                                    <t t-foreach="state.accounts" t-as="acc" t-key="acc.id">
                                        <option t-att-value="acc.id.toString()"><t t-esc="acc.name"/></option>
                                    </t>
                                </select>
                            </div>
                            
                            <!-- Bot Configuration -->
                            <div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column; gap: 20px; align-items: flex-start; height: 100%; justify-content: space-between;">
                                <div>
                                    <h3 style="margin: 0 0 5px 0; color: var(--ws-text-main);">Connection Settings</h3>
                                    <p style="color: var(--ws-text-muted); font-size: 14px; margin: 0;">Configure the AI auto-responder and API keys for this number.</p>
                                </div>
                                <button class="btn btn-secondary" t-on-click="openAccountSettings" style="background: #f0f2f5; border: 1px solid var(--ws-border); padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; color: var(--ws-text-main);">
                                    <i class="fa fa-sliders" style="margin-right: 5px;"></i> Configure
                                </button>
                            </div>
                            
                            <!-- Notifications -->
                            <div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column; gap: 20px; align-items: flex-start; height: 100%; justify-content: space-between;">
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
                </div>
            </t>
        </div>
    </t>
</templates>"""

    clean_xml += settings_tab

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(clean_xml)
    print("XML perfectly cleaned and fixed.")
