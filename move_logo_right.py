import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_account_payment_receipt_override.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('<div class="letterhead row"')
if start_idx == -1:
    start_idx = content.find('<div class="letterhead"')

end_idx = content.find('<div class="title-bar">', start_idx)

new_block = """<div class="letterhead row" style="margin:0; padding:36px 48px 24px; border-bottom:2px solid #0a1b4d;">
                        <div class="col-6 letterhead-details" style="padding:0; text-align:left;">
                            <h1 style="font-size:24px; margin:0; color:#071336; font-weight:700;"><t t-esc="o.company_id.name"/></h1>
                            <p style="margin:0; font-size:12px; color:#6B7280; text-transform:uppercase;">Official Payment Receipt</p>
                            <div class="school-address" style="margin-top:8px; font-size:12px; color:#6B7280; line-height:1.6;">
                                <strong><t t-esc="o.company_id.name"/></strong><br/>
                                <t t-if="o.company_id.street"><t t-esc="o.company_id.street"/><br/></t>
                                <t t-if="o.company_id.phone"><t t-esc="o.company_id.phone"/> | </t> <t t-if="o.company_id.email"><t t-esc="o.company_id.email"/></t><br/>
                                <t t-if="o.company_id.company_registry">Reg. No. <t t-esc="o.company_id.company_registry"/></t>
                            </div>
                        </div>
                        <div class="col-6 brand-logo" style="padding:0; text-align:right;">
                            <div class="crest" style="width:72px;height:72px;border-radius:50%;background:#0a1b4d;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #FBFAF6, 0 0 0 4px #d4af37; float:right;">
                                <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" alt="Logo" style="max-width:48px; max-height:48px;"/>
                            </div>
                            <div style="clear:both;"></div>
                        </div>
                    </div>

                    """

new_content = content[:start_idx] + new_block + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Rewrote letterhead to details on left, logo on right")
