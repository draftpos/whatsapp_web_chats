import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_havano_student_payment.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix text-align for school-address
content = content.replace(
    '<div class="school-address" style="margin-top:8px; font-size:12px; color:#6B7280; line-height:1.6;">',
    '<div class="school-address" style="margin-top:8px; font-size:12px; color:#6B7280; line-height:1.6; text-align: left;">'
)

# Fix float for the crest so it goes to the right
content = content.replace(
    '<div class="crest" style="width:72px;height:72px;border-radius:50%;background:#0a1b4d;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #FBFAF6, 0 0 0 4px #d4af37;">',
    '<div class="crest" style="width:72px;height:72px;border-radius:50%;background:#0a1b4d;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #FBFAF6, 0 0 0 4px #d4af37; float: right;">'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed alignment of address and logo.")
