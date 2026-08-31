import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_havano_student_payment.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make colors more formal but rich
# 1. Update Title Bar Background
content = content.replace(
    'background:#071336;',
    'background: linear-gradient(135deg, #071336 0%, #1a3673 100%); border-bottom: 3px solid #d4af37;'
)
content = content.replace(
    'color:#D9E2EC;',
    'color:#e2e8f0;'
)
# 2. Update field labels
content = content.replace(
    'color:#6B7280;\n                            margin-bottom:4px;',
    'color:#1a3673;\n                            margin-bottom:4px;\n                            font-weight: 600;'
)
# 3. Update table headers
content = content.replace(
    'border-bottom:1px solid #DCD8CC;',
    'border-bottom:2px solid #0a1b4d;'
)
content = content.replace(
    'color:#6B7280;\n                            font-weight:600;\n                            padding:10px 6px;',
    'color:#0a1b4d;\n                            background: rgba(10,27,77,0.05);\n                            font-weight:700;\n                            padding:12px 8px;'
)
# 4. Table rows alternating background and cell padding
content = content.replace(
    'padding:11px 6px;',
    'padding:11px 8px;'
)
content = content.replace(
    'background:rgba(10,27,77,0.035);',
    'background:rgba(212,175,55,0.05);' # subtle gold tint for even rows
)
# 5. Table wrap border
content = content.replace(
    'border-bottom:2px solid #0a1b4d;',
    'border-bottom:2px solid #d4af37;'
)
# 6. Totals section
content = content.replace(
    'color:#6B7280;\n                            border-bottom:1px solid #DCD8CC;',
    'color:#1a3673;\n                            font-weight:600;\n                            border-bottom:1px dashed #DCD8CC;'
)
content = content.replace(
    'border-top:2px solid #0a1b4d;',
    'border-top:2px solid #0a1b4d; background: rgba(10,27,77,0.05); padding: 12px 16px; margin: 4px -16px 0; border-radius: 4px;'
)
# 7. Progress Bar
content = content.replace(
    'background:#DCD8CC;',
    'background:#e2e8f0; box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied more formal and colorful styles.")
