file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_havano_student_payment.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the broken template wrapper and fix it
broken = '<template id="report_payment_receipt_main">          <t t-call="havano_schools_odoo.report_payment_receipt_main_document"/>\n        </t>\n    </template>'
fixed = '''<template id="report_payment_receipt_main">
        <t t-call="web.html_container">
            <t t-call="havano_schools_odoo.report_payment_receipt_main_document"/>
        </t>
    </template>'''

if broken in content:
    content = content.replace(broken, fixed)
    print("Fixed the broken template wrapper!")
else:
    # Try to find it
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'report_payment_receipt_main">' in line and 'document' not in line:
            print(f"Line {i+1}: {repr(line)}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
