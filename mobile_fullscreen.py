import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"
css_path = os.path.join(base, "static", "src", "css", "chats.css")

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Make the mobile container take over the entire screen, hiding Odoo's navbar
old_mobile = ".whatsapp-container {\n        flex-direction: column-reverse !important;\n    }"
new_mobile = """.whatsapp-container {
        flex-direction: column-reverse !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        height: 100% !important;
        width: 100% !important;
        z-index: 99999 !important;
        background: var(--ws-bg-main) !important;
    }"""

if old_mobile in css:
    css = css.replace(old_mobile, new_mobile)
else:
    # Fallback if whitespace differs
    import re
    css = re.sub(
        r'\.whatsapp-container\s*\{\s*flex-direction:\s*column-reverse\s*!important;\s*\}', 
        new_mobile, 
        css
    )

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css)

print("Mobile full-screen override applied.")
