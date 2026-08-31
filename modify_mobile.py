import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Modify XML
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

if 'chat-active' not in xml:
    xml = xml.replace(
        '<div class="whatsapp-container">',
        '<div t-attf-class="whatsapp-container {{ state.selectedChannel ? \'chat-active\' : \'chat-inactive\' }}">'
    )
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml)

# 2. Modify CSS
css_path = os.path.join(base, "static", "src", "css", "chats.css")
with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Update sidebar width
css = css.replace('width: 32%;', 'width: 28%; max-width: 380px;')
css = css.replace('min-width: 320px;', 'min-width: 280px;')

# Add mobile queries
mobile_css = """
@media (max-width: 768px) {
    /* When a chat is selected (chat-active) */
    .whatsapp-container.chat-active .whatsapp-sidebar { 
        display: none !important; 
    }
    .whatsapp-container.chat-active .whatsapp-main { 
        display: flex !important; 
        width: 100% !important; 
    }
    
    /* When no chat is selected (chat-inactive) */
    .whatsapp-container.chat-inactive .whatsapp-sidebar { 
        display: flex !important; 
        width: 100% !important; 
        max-width: none !important; 
    }
    .whatsapp-container.chat-inactive .whatsapp-main { 
        display: none !important; 
    }
    
    /* Adjust modal for mobile */
    .modal-content {
        width: 90% !important;
        margin: 20px;
    }
}
"""

if '@media (max-width: 768px)' not in css:
    css += mobile_css
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)

print("Mobile view and sidebar width updated.")
