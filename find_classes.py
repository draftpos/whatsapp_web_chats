import re

with open('c:/odoo19/addons/whatsapp_web_chats/static/src/xml/chats_template.xml','r',encoding='utf-8') as f:
    content = f.read()

classes = set(re.findall(r'class="([^"]+)"', content))
for c in sorted(classes):
    if 'drop' in c.lower() or 'menu' in c.lower() or 'msg' in c.lower() or 'option' in c.lower():
        print(c)
