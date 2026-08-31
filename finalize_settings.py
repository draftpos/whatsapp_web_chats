import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
js_path = os.path.join(base, "static", "src", "js", "chats.js")

# 1. Update JS
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

# Make configure button open in current window
js = js.replace("target: 'new',", "target: 'current',")

# Add notification state and toggle
if "notificationsEnabled:" not in js:
    js = js.replace("activeTab: 'chats',", "activeTab: 'chats',\n            notificationsEnabled: window.Notification ? window.Notification.permission === 'granted' : false,")

if "async toggleNotifications()" not in js:
    js = js.replace("async loadCatalogue() {", """
    async toggleNotifications() {
        if (!window.Notification) return;
        if (window.Notification.permission === 'granted') {
            this.state.notificationsEnabled = !this.state.notificationsEnabled;
        } else if (window.Notification.permission !== 'denied') {
            const permission = await window.Notification.requestPermission();
            if (permission === 'granted') {
                this.state.notificationsEnabled = true;
            }
        }
    }

    async loadCatalogue() {""")
    
with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)


# 2. Update XML
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# Remove the Settings header completely
header_pattern = re.compile(r'<!-- Header -->\s*<div class="sidebar-header-desktop".*?</div>', re.DOTALL)
xml = header_pattern.sub('', xml)

# Wire up the Notifications button
old_button = '<button class="btn btn-primary" style="background: var(--ws-primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer;">\n                                    Enabled\n                                </button>'
new_button = """<button t-on-click="toggleNotifications" t-attf-class="btn {{ state.notificationsEnabled ? 'btn-primary' : 'btn-secondary' }}" t-attf-style="{{ state.notificationsEnabled ? 'background: var(--ws-primary); color: white;' : 'background: #f0f2f5; color: var(--ws-text-main);' }} border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer;">
                                    <t t-esc="state.notificationsEnabled ? 'Enabled' : 'Disabled'"/>
                                </button>"""
xml = xml.replace(old_button, new_button)

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

print("Settings header removed, config button routes to current window, and notifications toggle wired up.")
