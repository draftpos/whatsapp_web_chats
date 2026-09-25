from odoo import models, fields

class WhatsAppAccount(models.Model):
    _inherit = 'whatsapp.account'

    saas_integration_active = fields.Boolean(string="Enable SaaS Integration", default=False)
    saas_app_url = fields.Char(string="SaaS App URL (Optional if local)", help="e.g. https://your-saas.com")
    saas_username = fields.Char(string="SaaS Admin Email")
    saas_password = fields.Char(string="SaaS Admin Password")
    
    saas_welcome_template_id = fields.Many2one(
        'whatsapp.template',
        string="New Tenant Welcome Template",
        domain="[('status', '=', 'approved')]",
        help="Template sent to new tenants. Variable {{1}}: Tenant Name"
    )
    
    saas_daily_sales_template_id = fields.Many2one(
        'whatsapp.template',
        string="Daily Sales Template",
        domain="[('status', '=', 'approved')]",
        help="Template sent for daily sales. Variable {{1}}: Tenant Name, {{2}}: Sales Data"
    )
