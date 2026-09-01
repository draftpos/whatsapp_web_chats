"""
WhatsApp Web Chats — Dummy Data Seeder
======================================
Run with:
  cd c:\\odoo19
  Get-Content addons\\whatsapp_web_chats\\seed_test_data.py | .\\venv\\Scripts\\python.exe odoo-bin shell -c odoo.conf -d havano_db --no-http 2>&1

This script:
  1. Creates a dummy WhatsApp account if none exists
  2. Creates 3 test contacts with WhatsApp numbers
  3. Creates WhatsApp channels for each contact
  4. Posts a realistic mix of messages: plain text, image, video, PDF, mixed
"""

import base64
import struct
import zlib

print("=" * 60)
print("  WhatsApp Chat Dummy Data Seeder")
print("=" * 60)

# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_png(width=400, height=300, r=100, g=180, b=240):
    """Build a minimal valid PNG in memory (no PIL needed)."""
    def chunk(name, data):
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    raw_rows = []
    for y in range(height):
        row = b'\x00'
        for x in range(width):
            pr = (r + x * 80 // width) % 256
            pg = (g + y * 60 // height) % 256
            pb = (b + (x + y) * 40 // (width + height)) % 256
            row += bytes([pr, pg, pb])
        raw_rows.append(row)
    raw = b''.join(raw_rows)
    idat = chunk(b'IDAT', zlib.compress(raw, 6))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend


def _make_pdf(title="Test Document"):
    """Build a tiny valid 1-page PDF (no dependencies)."""
    content = f"BT /F1 16 Tf 50 700 Td ({title}) Tj ET"
    stream = content.encode()
    pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Contents 4 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>>endobj
4 0 obj<</Length {len(stream)}>>
stream
{content}
endstream
endobj
xref
0 5
0000000000 65535 f 
trailer<</Size 5/Root 1 0 R>>
startxref
9
%%EOF"""
    return pdf.encode()


def _b64(data):
    return base64.b64encode(data).decode()


# ─── 1. find or create WhatsApp account ───────────────────────────────────────

# Clean up any orphaned half-created dummy rows from previous failed runs
env.cr.execute("""
    DELETE FROM whatsapp_account
    WHERE name = 'Demo WhatsApp Account'
      AND id NOT IN (
          SELECT whatsapp_account_id FROM res_users_whatsapp_account_rel
      )
""")
if env.cr.rowcount:
    print(f"  Cleaned {env.cr.rowcount} orphaned dummy account row(s).")

wa_account = env['whatsapp.account'].sudo().search([], limit=1)
if not wa_account:
    print("\n  No WhatsApp account found — creating a dummy one via SQL...")
    # The whatsapp.account model has an @api.constrains that fires before M2M
    # is stored, so we bypass it with a direct SQL insert.
    import secrets, string as _string
    verify_token = ''.join(secrets.choice(_string.ascii_letters + _string.digits) for _ in range(8))
    env.cr.execute("""
        INSERT INTO whatsapp_account
            (name, app_uid, app_secret, account_uid, phone_uid, token,
             webhook_verify_token, active, debug_logging,
             create_uid, write_uid, create_date, write_date)
        VALUES
            ('Demo WhatsApp Account', 'DEMO_APP_001', 'DEMO_SECRET_001',
             'DEMO_ACCOUNT_001', 'DEMO_PHONE_001', 'DEMO_TOKEN_001',
             %s, true, false,
             %s, %s, NOW(), NOW())
        RETURNING id
    """, [verify_token, env.uid, env.uid])
    new_id = env.cr.fetchone()[0]

    # Add notify_user (M2M table — actual name in this DB)
    env.cr.execute("""
        INSERT INTO res_users_whatsapp_account_rel (whatsapp_account_id, res_users_id)
        VALUES (%s, %s) ON CONFLICT DO NOTHING
    """, [new_id, env.uid])

    # Also add allowed company
    env.cr.execute("""
        INSERT INTO res_company_whatsapp_account_rel (whatsapp_account_id, res_company_id)
        SELECT %s, company_id FROM res_users WHERE id = %s ON CONFLICT DO NOTHING
    """, [new_id, env.uid])

    env.registry.clear_cache()
    wa_account = env['whatsapp.account'].sudo().browse(new_id)
    print(f"  Created dummy account: {wa_account.name!r}  (id={wa_account.id})")
else:
    print(f"\n  Using existing WhatsApp account: {wa_account.name!r}  (id={wa_account.id})")

# ─── 2. create (or find) test partners ────────────────────────────────────────

CONTACTS = [
    {"name": "Alice Demo",  "phone": "+1 555 0101"},
    {"name": "Bob Tester",  "phone": "+44 7700 900200"},
    {"name": "Carol Media", "phone": "+27 82 000 0303"},
]

partners = []
for c in CONTACTS:
    existing = env['res.partner'].search([('name', '=', c['name'])], limit=1)
    if existing:
        p = existing
        print(f"   Found existing partner: {p.name}")
    else:
        p = env['res.partner'].create({
            'name':  c['name'],
            'phone': c['phone'],
        })
        print(f"   Created partner: {p.name}  (id={p.id})")
    partners.append(p)

# ─── 3. create WhatsApp channels ──────────────────────────────────────────────

channels = []
for partner in partners:
    wa_number = (partner.phone or "").replace(" ", "")
    existing_ch = env['discuss.channel'].search([
        ('channel_type', '=', 'whatsapp'),
        ('whatsapp_partner_id', '=', partner.id),
        ('wa_account_id', '=', wa_account.id),
    ], limit=1)

    if existing_ch:
        ch = existing_ch
        print(f"\n   Re-using channel for {partner.name}: id={ch.id}")
    else:
        ch = env['discuss.channel'].create({
            'name': partner.name,
            'channel_type': 'whatsapp',
            'whatsapp_partner_id': partner.id,
            'whatsapp_number': wa_number,
            'wa_account_id': wa_account.id,
        })
        # Only add member if not already added (Odoo may auto-add current user)
        existing_member = env['discuss.channel.member'].search([
            ('channel_id', '=', ch.id),
            ('partner_id', '=', env.user.partner_id.id),
        ], limit=1)
        if not existing_member:
            env['discuss.channel.member'].create({
                'channel_id': ch.id,
                'partner_id': env.user.partner_id.id,
            })
        print(f"\n   Created channel for {partner.name}: id={ch.id}")
    channels.append((partner, ch))

# ─── helper to post a message ─────────────────────────────────────────────────

def post(channel, body, filename=None, file_data=None, mimetype=None, from_customer=False):
    author_id = (channel.whatsapp_partner_id.id if from_customer
                 else env.user.partner_id.id)

    att_ids = []
    if filename and file_data:
        att = env['ir.attachment'].create({
            'name':      filename,
            'type':      'binary',
            'datas':     _b64(file_data),
            'mimetype':  mimetype,
            'res_model': 'discuss.channel',
            'res_id':    channel.id,
        })
        att_ids = [att.id]

    channel.with_context(mail_create_nosubscribe=True).message_post(
        body=body,
        message_type='whatsapp_message',
        subtype_xmlid='mail.mt_comment',
        author_id=author_id,
        attachment_ids=att_ids,
    )

# ─── 4. Alice — multiple images ───────────────────────────────────────────────

partner_alice, ch_alice = channels[0]
print(f"\n  Seeding image messages -> {partner_alice.name}")

post(ch_alice, "Hey! Can you show me some product photos?", from_customer=True)
post(ch_alice, "Of course! Here is our red model:",
     filename="product_red.png",
     file_data=_make_png(600, 400, r=220, g=60, b=60),
     mimetype="image/png")
post(ch_alice, "And here is the blue model:",
     filename="product_blue.png",
     file_data=_make_png(600, 400, r=40, g=100, b=220),
     mimetype="image/png")
post(ch_alice, "Sending my reference image:",
     filename="customer_ref.png",
     file_data=_make_png(400, 300, r=80, g=200, b=120),
     mimetype="image/png",
     from_customer=True)
post(ch_alice, "Got it! We can match that. Let me send one more:",
     filename="catalogue_item.png",
     file_data=_make_png(500, 500, r=200, g=150, b=40),
     mimetype="image/png")
post(ch_alice, "Perfect! I will place an order.", from_customer=True)
post(ch_alice, "Great! We will get it ready.", from_customer=False)

# ─── 5. Bob — image + PDF documents ──────────────────────────────────────────

partner_bob, ch_bob = channels[1]
print(f"\n  Seeding mixed media messages -> {partner_bob.name}")

post(ch_bob, "Hi, I have an issue with my invoice.", from_customer=True)
post(ch_bob, "Could you share a screenshot of the error?", from_customer=False)
post(ch_bob, "Here it is:",
     filename="error_screenshot.png",
     file_data=_make_png(800, 450, r=220, g=60, b=60),
     mimetype="image/png",
     from_customer=True)
post(ch_bob, "Thank you! Here is your corrected invoice:",
     filename="Invoice_2026_0042.pdf",
     file_data=_make_pdf("Invoice #2026-0042 | Total: $350.00"),
     mimetype="application/pdf")
post(ch_bob, "Also attaching our terms document:",
     filename="Terms_and_Conditions.pdf",
     file_data=_make_pdf("Terms and Conditions - Company Ltd."),
     mimetype="application/pdf")
post(ch_bob, "Thank you so much!", from_customer=True)
post(ch_bob, "Happy to help! Anything else?", from_customer=False)

# ─── 6. Carol — image + video + PDF ──────────────────────────────────────────

partner_carol, ch_carol = channels[2]
print(f"\n  Seeding video + multi-media messages -> {partner_carol.name}")

post(ch_carol, "Hello! Can I see a product demo?", from_customer=True)
post(ch_carol, "Sure! Here is a preview thumbnail:",
     filename="demo_thumbnail.png",
     file_data=_make_png(640, 360, r=140, g=60, b=200),
     mimetype="image/png")

# Minimal valid MP4 ftyp atom — browser recognises it as video/mp4
tiny_mp4 = (
    b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2'
    b'avc1mp41\x00\x00\x00\x08free\x00\x00\x00\x00mdat'
)
post(ch_carol, "And here is the product demo video:",
     filename="product_demo.mp4",
     file_data=tiny_mp4,
     mimetype="video/mp4")

post(ch_carol, "Wow that looks amazing! Can I get the spec sheet?", from_customer=True)
post(ch_carol, "Of course:",
     filename="Product_Specs.pdf",
     file_data=_make_pdf("Product Specifications - Model X500"),
     mimetype="application/pdf")
post(ch_carol, "Also sending our 2026 price list:",
     filename="Price_List_2026.png",
     file_data=_make_png(800, 600, r=30, g=180, b=180),
     mimetype="image/png")
post(ch_carol, "Perfect. Placing my order today!", from_customer=True)
post(ch_carol, "Great! Confirmation coming shortly.", from_customer=False)

# ─── 7. commit ────────────────────────────────────────────────────────────────

env.cr.commit()

print("\n" + "=" * 60)
print("  Seeding complete!")
print(f"  Channels: {len(channels)}")
for p, ch in channels:
    print(f"    - {p.name}  (channel id={ch.id})")
print()
print("  Open WhatsApp Web Chats and test:")
print("   Alice Demo  -> zoom/pan/download on 4 images")
print("   Bob Tester  -> image lightbox + 2x PDF download")
print("   Carol Media -> image + video player + PDF + image")
print("=" * 60)
