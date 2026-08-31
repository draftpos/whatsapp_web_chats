import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")

with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# The regex replaced everything from <t t-elif="state.activeTab === 'settings'"> up to the FIRST </t>
# Which means it left stray closing tags like </select>, </t>, </div>, </div>, </div>, </t> lying around.
# We need to clean up everything from <t t-elif="state.activeTab === 'settings'"> to the END of the template (since Settings is the last tab).
# Wait, let's look at the end of the template.
# The template ends with:
#         </div>
#     </t>
# </templates>

# Let's extract everything BEFORE the Settings tab.
start_idx = xml.find('<t t-elif="state.activeTab === \'settings\'">')

if start_idx != -1:
    xml_start = xml[:start_idx]
    
    # Reconstruct the settings tab correctly
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
                            <t t-if="state.accounts.length &gt; 0">
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
            </t>
        </div>
    </t>
</templates>
"""
    final_xml = xml_start + new_settings
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(final_xml)
    print("XML fixed successfully.")
else:
    print("Could not find settings tab marker.")
