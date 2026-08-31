import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")

with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

# I will replace the flex-direction: column container for the settings cards
old_container = '<div style="display: flex; flex-direction: column; gap: 20px; max-width: 600px; margin: 0 auto; width: 100%;">'
new_container = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; width: 100%; align-items: start;">'

xml = xml.replace(old_container, new_container)

# Also, change the display flex on the Bot Configuration and Notifications cards so they stack vertically inside the card 
# if they are side by side, they might get too squished if we keep them horizontal inside the card.
# Actually, minmax(350px) is wide enough to keep text and button side-by-side, but let's change them to flex-direction: column with align-items: flex-start to look like nice standard cards.
old_card_1 = '<div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center;">'
new_card_1 = '<div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column; gap: 20px; align-items: flex-start; height: 100%; justify-content: space-between;">'

xml = xml.replace(old_card_1, new_card_1)

# And for the first card (Active Connection), make it match the height: 100% and flex layout
old_acc_card = '<div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02);">'
new_acc_card = '<div style="background: white; padding: 24px; border-radius: 12px; border: 1px solid var(--ws-border); box-shadow: 0 2px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column; height: 100%; justify-content: flex-start;">'

xml = xml.replace(old_acc_card, new_acc_card)


with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

print("Settings layout changed to side by side grid.")
