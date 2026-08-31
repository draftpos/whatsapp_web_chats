import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Fix the product.template search error in discuss_channel.py
discuss_path = os.path.join(base, "models", "discuss_channel.py")
with open(discuss_path, "r", encoding="utf-8") as f:
    discuss = f.read()

# Change the search query to bypass the default ordering on 'name' which causes the Postgres JSONB cast error
discuss = discuss.replace(
    "products = self.env['product.template'].search([('is_wasphere_catalogue', '=', True)])",
    "products = self.env['product.template'].search([('is_wasphere_catalogue', '=', True)], order='id desc')"
)
with open(discuss_path, "w", encoding="utf-8") as f:
    f.write(discuss)

# 2. Fix the invisible icon in chats_template.xml
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# Odoo uses FontAwesome 4, so fa-comment-dots is invisible. Change to fa-comments.
xml = xml.replace('fa-comment-dots', 'fa-comments')

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

print("Bug fixes applied successfully.")
