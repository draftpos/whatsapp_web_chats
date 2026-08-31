import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_havano_student_payment.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the main receipt document template
old_start = '<template id="report_payment_receipt_main_document">'
old_end = '</template>\n\n    <template id="report_payment_receipt_main">'

start_idx = content.find(old_start)
end_idx = content.find(old_end) + len(old_end)

new_template = '''<template id="report_payment_receipt_main_document">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="o">
                <div class="article" t-att-data-oe-model="o and o._name" t-att-data-oe-id="o and o.id" t-att-data-oe-lang="o and o.env.context.get('lang')">
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
                        * { box-sizing: border-box; margin: 0; padding: 0; }
                        body { font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; }
                        .receipt-wrapper {
                            width: 100%;
                            background: #ffffff;
                            position: relative;
                            overflow: hidden;
                        }
                        /* Top stripe */
                        .top-stripe {
                            height: 5px;
                            background: linear-gradient(90deg, #0a1b4d 0%, #0a1b4d 70%, #d4af37 70%, #d4af37 100%);
                        }
                        /* Bottom stripe */
                        .bottom-stripe {
                            height: 5px;
                            background: linear-gradient(90deg, #d4af37 0%, #d4af37 30%, #0a1b4d 30%, #0a1b4d 100%);
                        }
                        /* DRAFT ribbon */
                        .draft-ribbon {
                            position: absolute;
                            top: 18px;
                            right: -38px;
                            width: 160px;
                            transform: rotate(38deg);
                            background: #d4af37;
                            color: #071336;
                            text-align: center;
                            font-weight: 800;
                            font-size: 11px;
                            letter-spacing: 2.5px;
                            padding: 5px 0;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
                            z-index: 10;
                        }
                        /* Letterhead */
                        .letterhead {
                            padding: 28px 40px 22px;
                            border-bottom: 1px solid #e8e4d9;
                            overflow: hidden;
                        }
                        .lh-table {
                            width: 100%;
                            border-collapse: collapse;
                        }
                        .lh-left {
                            width: 55%;
                            vertical-align: top;
                        }
                        .lh-right {
                            width: 45%;
                            vertical-align: top;
                            text-align: right;
                        }
                        .brand-row {
                            display: flex;
                            align-items: center;
                            gap: 14px;
                        }
                        .logo-circle {
                            width: 60px;
                            height: 60px;
                            border-radius: 50%;
                            background: #0a1b4d;
                            border: 3px solid #d4af37;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            flex-shrink: 0;
                            overflow: hidden;
                        }
                        .logo-circle img {
                            max-width: 40px;
                            max-height: 40px;
                            object-fit: contain;
                        }
                        .brand-name {
                            font-size: 22px;
                            font-weight: 700;
                            color: #0a1b4d;
                            letter-spacing: 0.2px;
                        }
                        .brand-sub {
                            font-size: 10px;
                            color: #8a8a8a;
                            letter-spacing: 2px;
                            text-transform: uppercase;
                            margin-top: 3px;
                        }
                        .school-details {
                            font-size: 11.5px;
                            color: #555;
                            line-height: 1.75;
                            text-align: right;
                        }
                        .school-details strong {
                            display: block;
                            font-size: 13px;
                            color: #0a1b4d;
                            font-weight: 600;
                            margin-bottom: 2px;
                        }
                        /* Title bar */
                        .title-bar {
                            background: #0a1b4d;
                            padding: 16px 40px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }
                        .title-bar h2 {
                            font-size: 17px;
                            font-weight: 700;
                            color: #ffffff;
                            letter-spacing: 0.3px;
                        }
                        .title-meta {
                            text-align: right;
                            font-size: 12px;
                            color: #aec0d8;
                            line-height: 1.8;
                        }
                        .title-meta span {
                            color: #d4af37;
                            font-weight: 700;
                        }
                        /* Ornament divider */
                        .ornament {
                            display: flex;
                            align-items: center;
                            gap: 10px;
                            padding: 8px 40px;
                        }
                        .ornament .rule { flex: 1; height: 1px; background: #e8e4d9; }
                        .ornament .diamond { color: #d4af37; font-size: 10px; }
                        /* Details grid */
                        .details {
                            padding: 4px 40px 0;
                            overflow: hidden;
                        }
                        .field-row {
                            overflow: hidden;
                            margin-bottom: 0;
                        }
                        .field {
                            float: left;
                            width: 50%;
                            padding: 14px 24px 12px 0;
                            border-bottom: 1.5px solid #d4af37;
                            margin-bottom: 16px;
                            box-sizing: border-box;
                        }
                        .field:nth-child(2n) {
                            padding-right: 0;
                        }
                        .field .label {
                            font-size: 9.5px;
                            text-transform: uppercase;
                            letter-spacing: 1.2px;
                            color: #0a1b4d;
                            margin-bottom: 5px;
                            font-weight: 600;
                        }
                        .field .value {
                            font-size: 14.5px;
                            font-weight: 700;
                            color: #1a1a2e;
                        }
                        /* Table section */
                        .table-section {
                            padding: 4px 40px 0;
                            clear: both;
                        }
                        .section-title {
                            font-size: 11px;
                            font-weight: 700;
                            text-transform: uppercase;
                            letter-spacing: 1.5px;
                            color: #0a1b4d;
                            border-bottom: 2px solid #d4af37;
                            padding-bottom: 7px;
                            margin-bottom: 0;
                        }
                        table {
                            width: 100%;
                            border-collapse: collapse;
                            font-size: 12px;
                        }
                        thead th {
                            text-align: left;
                            font-size: 9.5px;
                            text-transform: uppercase;
                            letter-spacing: 0.8px;
                            color: #6b7280;
                            font-weight: 600;
                            padding: 10px 6px 8px;
                            border-bottom: 1px solid #e5e7eb;
                        }
                        thead th.num, tbody td.num { text-align: right; }
                        tbody td {
                            padding: 10px 6px;
                            border-bottom: 1px solid #f0ede6;
                            color: #1a1a2e;
                            font-size: 12px;
                        }
                        tbody tr:last-child td { border-bottom: none; }
                        tbody tr:nth-child(even) { background: rgba(10,27,77,0.025); }
                        /* Totals */
                        .totals {
                            display: flex;
                            justify-content: flex-end;
                            padding: 10px 40px 6px;
                        }
                        .totals-box { width: 280px; }
                        .totals-row {
                            display: flex;
                            justify-content: space-between;
                            font-size: 12.5px;
                            padding: 7px 0;
                            color: #555;
                            border-bottom: 1px solid #f0ede6;
                        }
                        .totals-row .amt { color: #1a1a2e; font-weight: 600; }
                        .totals-row.grand {
                            border-bottom: none;
                            border-top: 2px solid #0a1b4d;
                            margin-top: 4px;
                            padding-top: 10px;
                            font-size: 14px;
                            font-weight: 700;
                            color: #0a1b4d;
                        }
                        .totals-row.grand .amt { font-size: 17px; color: #0a1b4d; }
                        /* Progress bar */
                        .progress-wrap { padding: 4px 40px 10px; }
                        .progress-labels {
                            display: flex;
                            justify-content: space-between;
                            font-size: 9.5px;
                            color: #9ca3af;
                            text-transform: uppercase;
                            letter-spacing: 0.8px;
                            margin-bottom: 5px;
                        }
                        .progress {
                            height: 5px;
                            background: #e5e7eb;
                            border-radius: 99px;
                            overflow: hidden;
                        }
                        .progress-fill {
                            height: 100%;
                            background: linear-gradient(90deg, #d4af37, #0a1b4d);
                            border-radius: 99px;
                        }
                        /* Footer */
                        .footer {
                            display: flex;
                            justify-content: space-between;
                            align-items: flex-end;
                            padding: 24px 40px 28px;
                            margin-top: 8px;
                        }
                        .signature { font-size: 11.5px; color: #6b7280; }
                        .sig-line {
                            width: 200px;
                            border-bottom: 1.5px solid #1a1a2e;
                            margin-bottom: 6px;
                            height: 32px;
                        }
                        .official-stamp {
                            width: 90px;
                            height: 90px;
                            border-radius: 50%;
                            border: 3px solid #2F6B4F;
                            color: #2F6B4F;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            text-align: center;
                            transform: rotate(-12deg);
                            font-weight: 800;
                            font-size: 12px;
                            letter-spacing: 1.5px;
                            line-height: 1.3;
                            flex-shrink: 0;
                        }
                        .verify-block {
                            display: flex;
                            align-items: center;
                            gap: 12px;
                        }
                        .qr-box {
                            width: 52px;
                            height: 52px;
                            border-radius: 4px;
                            border: 1px solid #e5e7eb;
                            background:
                                linear-gradient(#1a1a2e 0 0) 0 0/11px 11px,
                                linear-gradient(#1a1a2e 0 0) 15px 0/11px 11px,
                                linear-gradient(#1a1a2e 0 0) 0 15px/11px 11px,
                                linear-gradient(#1a1a2e 0 0) 30px 30px/8px 8px,
                                linear-gradient(#1a1a2e 0 0) 15px 30px/6px 6px,
                                linear-gradient(#1a1a2e 0 0) 30px 15px/6px 6px;
                            background-repeat: no-repeat;
                            background-color: #fff;
                            flex-shrink: 0;
                        }
                        .verify-text { font-size: 10px; color: #6b7280; line-height: 1.6; max-width: 160px; }
                        .verify-text strong { display: block; color: #1a1a2e; font-size: 11px; margin-bottom: 2px; }
                        /* Bottom note */
                        .bottom-note {
                            text-align: center;
                            font-size: 10.5px;
                            color: #9ca3af;
                            padding: 0 40px 20px;
                            letter-spacing: 0.2px;
                        }
                    </style>

                    <div class="receipt-wrapper">
                        <!-- Top stripe -->
                        <div class="top-stripe"></div>

                        <!-- DRAFT ribbon -->
                        <t t-if="o.state != 'posted'">
                            <div class="draft-ribbon">DRAFT</div>
                        </t>

                        <!-- Letterhead -->
                        <div class="letterhead">
                            <table class="lh-table">
                                <tr>
                                    <td class="lh-left">
                                        <table style="border-collapse:collapse;">
                                            <tr>
                                                <td style="vertical-align:middle; padding-right:14px;">
                                                    <div class="logo-circle">
                                                        <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" alt="Logo"/>
                                                    </div>
                                                </td>
                                                <td style="vertical-align:middle;">
                                                    <div class="brand-name"><t t-esc="o.company_id.name"/></div>
                                                    <div class="brand-sub">Official Payment Receipt</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                    <td class="lh-right">
                                        <div class="school-details">
                                            <strong><t t-esc="o.company_id.name"/></strong>
                                            <t t-if="o.company_id.street"><t t-esc="o.company_id.street"/><br/></t>
                                            <t t-if="o.company_id.city"><t t-esc="o.company_id.city"/><t t-if="o.company_id.country_id">, <t t-esc="o.company_id.country_id.name"/></t><br/></t>
                                            <t t-if="o.company_id.phone"><t t-esc="o.company_id.phone"/><br/></t>
                                            <t t-if="o.company_id.email"><t t-esc="o.company_id.email"/><br/></t>
                                            <t t-if="o.company_id.company_registry">Reg. No. <t t-esc="o.company_id.company_registry"/></t>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </div>

                        <!-- Title bar -->
                        <div class="title-bar">
                            <h2>Student Payment Receipt</h2>
                            <div class="title-meta">
                                Receipt No. <span><t t-esc="o.name"/></span><br/>
                                Date Issued <span><t t-esc="o.date" t-options=\'{"widget": "date"}\'/>  </span>
                            </div>
                        </div>

                        <!-- Ornament -->
                        <div class="ornament">
                            <div class="rule"></div>
                            <span class="diamond">&#9670;</span>
                            <div class="rule"></div>
                        </div>

                        <!-- Details fields -->
                        <div class="details">
                            <div class="field">
                                <div class="label">Student Name</div>
                                <div class="value"><t t-esc="o.student_id.name"/></div>
                            </div>
                            <div class="field">
                                <div class="label">Date</div>
                                <div class="value"><t t-esc="o.date" t-options=\'{"widget": "date"}\'/></div>
                            </div>
                            <div class="field">
                                <div class="label">Class</div>
                                <div class="value"><t t-esc="o.course_id.name or \'—\'"/></div>
                            </div>
                            <div class="field">
                                <div class="label">Account Paid To</div>
                                <div class="value"><t t-esc="o.journal_id.name or \'—\'"/></div>
                            </div>
                            <div class="field">
                                <div class="label">Section</div>
                                <div class="value"><t t-esc="o.batch_id.name or \'—\'"/></div>
                            </div>
                            <div class="field">
                                <div class="label">Total Balance</div>
                                <div class="value"><t t-esc="o.total_balance" t-options=\'{"widget": "monetary", "display_currency": o.currency_id}\'/></div>
                            </div>
                        </div>

                        <!-- Outstanding Invoices table -->
                        <div class="table-section">
                            <div class="section-title">Outstanding Invoices</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Invoice No.</th>
                                        <th>Fees Structure</th>
                                        <th>Invoice Date</th>
                                        <th>Year</th>
                                        <th>Term</th>
                                        <th class="num">Outstanding</th>
                                        <th class="num">Allocated</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="o.line_ids" t-as="line">
                                        <tr>
                                            <td><t t-esc="line.name"/></td>
                                            <td><t t-esc="line.sub_fees_structure_id.name"/></td>
                                            <td><t t-esc="line.invoice_date" t-options=\'{"widget": "date"}\'/>  </td>
                                            <td><t t-esc="line.academic_year_id.name"/></td>
                                            <td><t t-esc="line.term_id.name"/></td>
                                            <td class="num"><t t-esc="line.amount_residual" t-options=\'{"widget": "monetary", "display_currency": o.currency_id}\'/></td>
                                            <td class="num"><t t-esc="line.amount_allocated" t-options=\'{"widget": "monetary", "display_currency": o.currency_id}\'/></td>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>
                        </div>

                        <!-- Totals -->
                        <div class="totals">
                            <div class="totals-box">
                                <div class="totals-row">
                                    <span>Total Outstanding</span>
                                    <span class="amt"><t t-esc="o.total_balance" t-options=\'{"widget": "monetary", "display_currency": o.currency_id}\'/></span>
                                </div>
                                <div class="totals-row">
                                    <span>Allocated Amount</span>
                                    <span class="amt"><t t-esc="o.allocated_amount" t-options=\'{"widget": "monetary", "display_currency": o.currency_id}\'/></span>
                                </div>
                                <div class="totals-row grand">
                                    <span>Balance Due</span>
                                    <span class="amt"><t t-esc="o.total_balance - o.allocated_amount" t-options=\'{"widget": "monetary", "display_currency": o.currency_id}\'/></span>
                                </div>
                            </div>
                        </div>

                        <!-- Progress bar -->
                        <div class="progress-wrap">
                            <div class="progress-labels"><span>Allocated</span><span>Outstanding</span></div>
                            <div class="progress">
                                <div class="progress-fill" t-attf-style="width: {{ (o.allocated_amount / o.total_balance * 100) if o.total_balance > 0 else 0 }}%;"></div>
                            </div>
                        </div>

                        <!-- Footer -->
                        <div class="footer">
                            <div class="signature">
                                <div class="sig-line"></div>
                                Authorised Signature &#8212; Bursar&#39;s Office
                            </div>
                            <div class="official-stamp">OFFICIAL<br/>RECEIPT</div>
                            <div class="verify-block">
                                <div class="qr-box"></div>
                                <div class="verify-text">
                                    <strong>Verify this receipt</strong>
                                    <t t-esc="o.company_id.website or 'portal.havanohigh.ac.zw'"/>/verify/<t t-esc="o.name"/>
                                </div>
                            </div>
                        </div>

                        <!-- Bottom note -->
                        <div class="bottom-note">This receipt is computer-generated and valid without a signature when issued through the <t t-esc="o.company_id.name"/> portal.</div>

                        <!-- Bottom stripe -->
                        <div class="bottom-stripe"></div>
                    </div>
                </div>
            </t>
        </t>
    </template>

    <template id="report_payment_receipt_main">'''

content = content[:start_idx] + new_template + content[end_idx + len('<template id="report_payment_receipt_main">'):]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done - receipt template rewritten to match design.")
