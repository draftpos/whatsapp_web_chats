import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Update XML to add state class
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

xml = xml.replace('<div class="whatsapp-container">', '<div t-attf-class="whatsapp-container {{ state.selectedChannel ? \'chat-active\' : \'\' }}">')

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

# 2. Add Mobile CSS
css_path = os.path.join(base, "static", "src", "css", "chats.css")
with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Remove any existing media queries to avoid conflicts
css = re.sub(r'@media \(max-width: 768px\) \{.*?^\}', '', css, flags=re.DOTALL | re.MULTILINE)

mobile_css = """
@media (max-width: 768px) {
    /* Main container changes to column-reverse to put nav-rail at the bottom */
    .whatsapp-container {
        flex-direction: column-reverse !important;
    }
    
    /* Nav Rail becomes bottom tab bar */
    .whatsapp-nav-rail {
        width: 100% !important;
        height: 60px !important;
        flex-direction: row !important;
        justify-content: space-around !important;
        align-items: center !important;
        padding: 0 !important;
        border-right: none !important;
        border-top: 1px solid var(--ws-border);
    }
    .nav-item {
        margin: 0 !important;
        width: 100% !important;
        height: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        border-radius: 0 !important;
    }
    
    /* Content area (sidebar + main) logic */
    .whatsapp-content {
        flex: 1;
        width: 100%;
        display: flex;
        flex-direction: row;
        overflow: hidden;
    }

    /* Single pane view: Sidebar takes 100% when no chat is active */
    .whatsapp-sidebar {
        width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
    }
    
    /* Main chat pane is hidden when no chat is active */
    .whatsapp-main {
        display: none !important;
        width: 100% !important;
    }

    /* WHEN CHAT IS ACTIVE: Hide sidebar, show main chat */
    .whatsapp-container.chat-active .whatsapp-sidebar {
        display: none !important;
    }
    .whatsapp-container.chat-active .whatsapp-main {
        display: flex !important;
    }
    
    /* Show the back button in mobile */
    .mobile-back-btn {
        display: block !important;
    }

    /* Adjust settings grid for mobile */
    .whatsapp-container [style*="grid-template-columns"] {
        grid-template-columns: 1fr !important;
    }
}
"""

with open(css_path, "a", encoding="utf-8") as f:
    f.write("\n" + mobile_css)

print("Mobile responsiveness added.")
