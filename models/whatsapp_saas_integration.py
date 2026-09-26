from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    saas_expiration_template_id = fields.Many2one(
        'whatsapp.template',
        string="Subscription Expiration Template",
        domain="[('status', '=', 'approved')]",
        help="Template sent when subscription is expiring. Variable {{1}}: Tenant Name, {{2}}: Days Left"
    )
    saas_expiration_days = fields.Char(
        string="Send Warning On Days Remaining",
        default="5,4,3,2,1",
        help="Comma-separated list of days before expiration to send warning (e.g. '5,4,3,2,1')."
    )

    saas_tenant_count = fields.Integer(
        string="Tenants",
        compute='_compute_saas_tenant_count',
    )

    @api.depends('saas_integration_active')
    def _compute_saas_tenant_count(self):
        for rec in self:
            rec.saas_tenant_count = self.env['whatsapp.saas.tenant'].search_count(
                [('account_id', '=', rec.id)]
            )

    def action_fetch_tenants(self):
        """Fetch/sync tenants from the configured SaaS URL and open the tenant list."""
        self.ensure_one()
        if not self.saas_integration_active:
            raise UserError(_("SaaS Integration is not enabled on this account."))

        tenant_model = self.env['whatsapp.saas.tenant']
        before_count = tenant_model.search_count([('account_id', '=', self.id)])

        # Run sync (reuses existing _sync_tenants_from_saas logic)
        tenant_model._sync_tenants_from_saas(self)

        after_count = tenant_model.search_count([('account_id', '=', self.id)])
        new_count = after_count - before_count

        if new_count > 0:
            msg = f"✅ Sync complete: {new_count} new tenant(s) added. Total: {after_count}."
        else:
            msg = f"✅ Sync complete: No new tenants found. {after_count} tenant(s) are already up to date."

        # Open the tenant list filtered to this account
        action = self.env['ir.actions.act_window']._for_xml_id(
            'whatsapp_web_chats.action_whatsapp_saas_tenant'
        )
        action['domain'] = [('account_id', '=', self.id)]
        action['context'] = {'default_account_id': self.id}
        action['target'] = 'current'
        # Attach notification message to display
        return dict(action, notification=msg)

    def action_open_tenants(self):
        """Open the tenant list filtered to this account."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'whatsapp_web_chats.action_whatsapp_saas_tenant'
        )
        action['domain'] = [('account_id', '=', self.id)]
        action['context'] = {'default_account_id': self.id}
        return action
