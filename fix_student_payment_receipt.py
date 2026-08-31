import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_havano_student_payment.xml"
with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix invalid characters
content = content.replace("A", "|")
content = content.replace("?-", "✦")
content = content.replace("?\"", "-")

# Find the letterhead block
start_idx = content.find('<div class="letterhead">')
if start_idx == -1:
    print("Could not find letterhead")
else:
    end_idx = content.find('<div class="title-bar">', start_idx)

    new_block = """<table class="letterhead" style="width: 100%; margin:0; padding:36px 48px 24px; border-bottom:2px solid #0a1b4d; border-collapse: collapse;">
                                <tr>
                                    <td class="letterhead-details" style="width: 50%; vertical-align: top; text-align: left; padding: 0;">
                                        <h1 style="font-size:24px; margin:0; color:#071336; font-weight:700;"><t t-esc="o.company_id.name"/></h1>
                                        <p style="margin:0; font-size:12px; color:#6B7280; text-transform:uppercase;">Official Payment Receipt</p>
                                        <div class="school-address" style="margin-top:8px; font-size:12px; color:#6B7280; line-height:1.6;">
                                            <strong><t t-esc="o.company_id.name"/></strong><br/>
                                            <t t-if="o.company_id.street"><t t-esc="o.company_id.street"/><br/></t>
                                            <t t-if="o.company_id.phone"><t t-esc="o.company_id.phone"/> | </t> <t t-if="o.company_id.email"><t t-esc="o.company_id.email"/></t><br/>
                                            <t t-if="o.company_id.company_registry">Reg. No. <t t-esc="o.company_id.company_registry"/></t>
                                        </div>
                                    </td>
                                    <td class="brand-logo" style="width: 50%; vertical-align: top; text-align: right; padding: 0;">
                                        <div class="crest" style="width:72px;height:72px;border-radius:50%;background:#0a1b4d;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #FBFAF6, 0 0 0 4px #d4af37;">
                                            <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" alt="Logo" style="max-width:48px; max-height:48px;"/>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            """

    new_content = content[:start_idx] + new_block + content[end_idx:]

    # Remove flex from .letterhead CSS
    new_content = new_content.replace("""                        .letterhead{
                            display:flex;
                            justify-content:space-between;
                            align-items:flex-start;
                            padding:36px 48px 24px;
                            border-bottom:2px solid #0a1b4d;
                        }""", """                        .letterhead{
                            padding:36px 48px 24px;
                        }""")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Fixed report_havano_student_payment.xml")
