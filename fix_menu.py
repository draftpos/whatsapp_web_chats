import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
js_path = os.path.join(base, "static", "src", "js", "chats.js")

# 1. Update JS
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

if "activeDropdown:" not in js:
    js = js.replace("activeTab: 'chats',", "activeTab: 'chats',\n            activeDropdown: null,")

if "toggleDropdown(name)" not in js:
    js = js.replace("async loadCatalogue() {", """
    toggleDropdown(name) {
        if (this.state.activeDropdown === name) {
            this.state.activeDropdown = null;
        } else {
            this.state.activeDropdown = name;
        }
    }
    
    closeDropdown() {
        this.state.activeDropdown = null;
    }

    async loadCatalogue() {""")
    
with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)


# 2. Update XML
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# The current 3-dots icon:
old_dots = '<i class="fa fa-ellipsis-v" style="cursor: pointer;" title="Menu"></i>'
new_dots = """<div style="position: relative; display: inline-block;">
                <i class="fa fa-ellipsis-v" style="cursor: pointer; padding: 0 10px;" title="Menu" t-on-click="() => this.toggleDropdown('mainMenu')"></i>
                <t t-if="state.activeDropdown === 'mainMenu'">
                    <div style="position: absolute; right: 0; top: 30px; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 1px solid var(--ws-border); width: 160px; z-index: 1000; display: flex; flex-direction: column; padding: 5px 0; font-size: 14px;">
                        <div style="padding: 12px 20px; cursor: pointer; color: var(--ws-text-main);" t-on-click="() => { this.setTab('settings'); this.closeDropdown(); }">Settings</div>
                        <div style="padding: 12px 20px; cursor: pointer; color: var(--ws-text-main);" t-on-click="() => { this.setTab('catalogue'); this.closeDropdown(); }">Catalogue</div>
                        <div style="padding: 12px 20px; cursor: pointer; color: var(--ws-text-main);" t-on-click="() => { this.setTab('communities'); this.closeDropdown(); }">Communities</div>
                        <div style="padding: 12px 20px; cursor: pointer; color: var(--ws-text-main);" t-on-click="() => { this.setTab('status'); this.closeDropdown(); }">Status</div>
                    </div>
                </t>
            </div>"""

xml = xml.replace(old_dots, new_dots)

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

print("Dropdown menu for 3 dots created.")
