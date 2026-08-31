import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_havano_student_payment.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Revert |4 back to A4
content = content.replace("|4", "A4")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed |4 back to A4")
