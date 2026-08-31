import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Fix CSS for the cut-off filters
css_path = os.path.join(base, "static", "src", "css", "chats.css")
with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Make sure sidebar header expands properly
old_header_css = """.sidebar-header-desktop {
    flex-direction: column;
    height: auto;
    align-items: flex-start;
    padding: 15px 20px;
}"""
new_header_css = """.sidebar-header-desktop {
    display: flex;
    flex-direction: column;
    height: auto !important;
    min-height: 140px;
    align-items: flex-start;
    padding: 15px 20px 10px 20px;
    background: var(--ws-bg-sidebar);
    z-index: 5;
    flex-shrink: 0;
}"""
if old_header_css in css:
    css = css.replace(old_header_css, new_header_css)
else:
    # Just aggressively append it
    css += "\n" + new_header_css

# Ensure chat filters have padding
css = css.replace(
    '.chat-filters {\n    display: flex;\n    gap: 8px;\n    margin-top: 5px;\n    width: 100%;\n    overflow-x: auto;\n    padding-bottom: 5px;\n    white-space: nowrap;\n}',
    '.chat-filters {\n    display: flex;\n    gap: 8px;\n    margin-top: 10px;\n    width: 100%;\n    overflow-x: auto;\n    padding-bottom: 10px;\n    white-space: nowrap;\n}'
)

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css)


# 2. Change Wedsphere to Websphere in UI
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

xml = xml.replace('WhatsApp Wedsphere', 'WhatsApp Websphere')

# Also fix the sidebar header classes to ensure it uses the new CSS correctly
# Remove whatsapp-header from the sidebar so it doesn't get the fixed 70px height
xml = xml.replace('class="whatsapp-header sidebar-header-desktop"', 'class="sidebar-header-desktop"')

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)


# 3. Change Web module names if needed (Optional, usually requested for menus too)
menu_path = os.path.join(base, "views", "wasphere_account_views.xml")
if os.path.exists(menu_path):
    with open(menu_path, "r", encoding="utf-8") as f:
        menu_xml = f.read()
    menu_xml = menu_xml.replace('WhatsApp Wedsphere', 'WhatsApp Websphere')
    with open(menu_path, "w", encoding="utf-8") as f:
        f.write(menu_xml)

print("CSS clipping fixed and text changed to Websphere.")
