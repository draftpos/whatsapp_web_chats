import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"
css_path = os.path.join(base, "static", "src", "css", "chats.css")

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Replace the specific nav-top and nav-bottom rule in the mobile block
old_nav_groups = """    /* Flatten nav groups so icons distribute evenly */
    .nav-top, .nav-bottom {
        display: contents !important;
    }"""
    
new_nav_groups = """    /* Convert the two groups into horizontal flex rows */
    .nav-top, .nav-bottom {
        display: flex !important;
        flex-direction: row !important;
        flex: 1 !important;
        justify-content: space-around !important;
        align-items: center !important;
    }"""

css = css.replace(old_nav_groups, new_nav_groups)

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css)

print("Nav groups switched from display: contents to flex row.")
