import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"
models_dir = os.path.join(base, "models")
controllers_dir = os.path.join(base, "controllers")

# 1. Create New Backend Models
status_py = """
from odoo import models, fields

class WasphereStatus(models.Model):
    _name = 'wasphere.status'
    _description = 'Wasphere Status Updates'
    _order = 'create_date desc'

    account_id = fields.Many2one('wasphere.account', string='Account', required=True)
    partner_id = fields.Many2one('res.partner', string='Contact', required=True)
    status_type = fields.Selection([
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video')
    ], default='text', required=True)
    body = fields.Text(string='Text Content')
    image = fields.Image(string='Image/Media')
    expires_at = fields.Datetime(string='Expires At')
    
    # Just to quickly fetch active ones
    active = fields.Boolean(default=True)
"""
with open(os.path.join(models_dir, "wasphere_status.py"), "w", encoding="utf-8") as f:
    f.write(status_py.strip())

call_py = """
from odoo import models, fields

class WasphereCallLog(models.Model):
    _name = 'wasphere.call.log'
    _description = 'Wasphere Call Logs'
    _order = 'start_time desc'

    account_id = fields.Many2one('wasphere.account', string='Account', required=True)
    partner_id = fields.Many2one('res.partner', string='Contact', required=True)
    call_type = fields.Selection([('audio', 'Audio'), ('video', 'Video')], default='audio', required=True)
    direction = fields.Selection([('inbound', 'Inbound'), ('outbound', 'Outbound'), ('missed', 'Missed')], required=True)
    start_time = fields.Datetime(string='Time', default=fields.Datetime.now, required=True)
    duration_seconds = fields.Integer(string='Duration (sec)', default=0)
"""
with open(os.path.join(models_dir, "wasphere_call.py"), "w", encoding="utf-8") as f:
    f.write(call_py.strip())

product_py = """
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_wasphere_catalogue = fields.Boolean(string="Show in WhatsApp Catalogue", default=False)
"""
with open(os.path.join(models_dir, "product_template.py"), "w", encoding="utf-8") as f:
    f.write(product_py.strip())

# Update __init__.py
init_path = os.path.join(models_dir, "__init__.py")
with open(init_path, "r", encoding="utf-8") as f:
    init_content = f.read()
if "wasphere_status" not in init_content:
    with open(init_path, "a", encoding="utf-8") as f:
        f.write("\nfrom . import wasphere_status")
        f.write("\nfrom . import wasphere_call")
        f.write("\nfrom . import product_template")

# 2. Update webhook.py with new endpoints
webhook_path = os.path.join(controllers_dir, "webhook.py")
with open(webhook_path, "a", encoding="utf-8") as f:
    new_endpoints = """
    @http.route('/api/flutter/sync_status', type='json', auth='public', methods=['POST'], csrf=False)
    def api_flutter_sync_status(self, account_id, statuses=None, **kwargs):
        # expects statuses: [{'phone': '12345', 'body': 'Hello', 'type': 'text'}]
        account = request.env['wasphere.account'].sudo().browse(account_id)
        if account.exists() and statuses:
            for st in statuses:
                partner = request.env['res.partner'].sudo().search([('phone', '=', st['phone'])], limit=1)
                if partner:
                    request.env['wasphere.status'].sudo().create({
                        'account_id': account.id,
                        'partner_id': partner.id,
                        'status_type': st.get('type', 'text'),
                        'body': st.get('body', '')
                    })
        return {'success': True}

    @http.route('/api/flutter/sync_call', type='json', auth='public', methods=['POST'], csrf=False)
    def api_flutter_sync_call(self, account_id, calls=None, **kwargs):
        account = request.env['wasphere.account'].sudo().browse(account_id)
        if account.exists() and calls:
            for call in calls:
                partner = request.env['res.partner'].sudo().search([('phone', '=', call['phone'])], limit=1)
                if partner:
                    request.env['wasphere.call.log'].sudo().create({
                        'account_id': account.id,
                        'partner_id': partner.id,
                        'call_type': call.get('call_type', 'audio'),
                        'direction': call.get('direction', 'inbound'),
                        'duration_seconds': call.get('duration', 0)
                    })
        return {'success': True}
"""
    f.write(new_endpoints)

# 3. Add fetching methods to discuss_channel.py
discuss_path = os.path.join(models_dir, "discuss_channel.py")
with open(discuss_path, "r", encoding="utf-8") as f:
    discuss = f.read()

# Add partner image to channel fetching
discuss = discuss.replace(
    "'last_message_date': last_msg.date.strftime('%H:%M') if last_msg else ''",
    "'last_message_date': last_msg.date.strftime('%H:%M') if last_msg else '',\n                'partner_image': ch.channel_partner_ids[0].image_128 if ch.channel_partner_ids else False"
)

# Add new fetching endpoints for the UI Tabs
backend_ui_methods = """
    @api.model
    def get_wasphere_statuses(self, account_id):
        statuses = self.env['wasphere.status'].search([('account_id', '=', int(account_id))])
        res = []
        for st in statuses:
            res.append({
                'id': st.id,
                'partner_name': st.partner_id.name or 'Unknown',
                'partner_image': st.partner_id.image_128,
                'body': st.body,
                'type': st.status_type,
                'time': st.create_date.strftime('%H:%M')
            })
        return res

    @api.model
    def get_wasphere_calls(self, account_id):
        calls = self.env['wasphere.call.log'].search([('account_id', '=', int(account_id))])
        res = []
        for call in calls:
            res.append({
                'id': call.id,
                'partner_name': call.partner_id.name or 'Unknown',
                'partner_image': call.partner_id.image_128,
                'direction': call.direction,
                'type': call.call_type,
                'time': call.start_time.strftime('%b %d, %H:%M')
            })
        return res

    @api.model
    def get_wasphere_catalogue(self):
        products = self.env['product.template'].search([('is_wasphere_catalogue', '=', True)])
        res = []
        for p in products:
            res.append({
                'id': p.id,
                'name': p.name,
                'price': p.list_price,
                'image': p.image_128
            })
        return res
"""
if "get_wasphere_statuses" not in discuss:
    with open(discuss_path, "a", encoding="utf-8") as f:
        f.write("\n" + backend_ui_methods)

# Security - need to add the new models to ir.model.access.csv if it exists, but for demo we can assume sudo/admin.
# Let's write them explicitly to be safe.
csv_path = os.path.join(base, "security", "ir.model.access.csv")
if os.path.exists(csv_path):
    with open(csv_path, "a", encoding="utf-8") as f:
        f.write("\naccess_wasphere_status,access_wasphere_status,model_wasphere_status,base.group_user,1,1,1,1")
        f.write("\naccess_wasphere_call_log,access_wasphere_call_log,model_wasphere_call_log,base.group_user,1,1,1,1")

print("Backend Models and Webhook endpoints created.")
