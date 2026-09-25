from odoo import models, fields, api
import requests
import logging
from datetime import datetime
from pytz import timezone

_logger = logging.getLogger(__name__)

class WhatsAppSaaSTenant(models.Model):
    _name = 'whatsapp.saas.tenant'
    _description = 'WhatsApp SaaS Tenant Schedule'

    account_id = fields.Many2one('whatsapp.account', string="WhatsApp Account", required=True)
    tenant_id = fields.Char(string="Tenant ID (SaaS)")
    tenant_name = fields.Char(string="Tenant Name")
    tenant_phone = fields.Char(string="Tenant Phone")
    
    scheduled_time = fields.Float(string="Scheduled Send Time", default=17.5, help="Time to send daily sales report (e.g. 17.5 = 5:30 PM)")
    last_sales_sent_date = fields.Date(string="Last Sales Sent Date")
    welcome_message_sent = fields.Boolean(string="Welcome Message Sent", default=False)

    @api.model
    def _cron_sync_and_send_saas_data(self):
        accounts = self.env['whatsapp.account'].search([('saas_integration_active', '=', True)])
        if not accounts:
            return

        for account in accounts:
            self._sync_tenants_from_saas(account)
            self._process_daily_sales(account)

    def _sync_tenants_from_saas(self, account):
        # Local SaaS setup check
        has_local_saas = 'havanoposdesk.tenant' in self.env
        
        tenants_data = []
        if has_local_saas:
            # Sync directly from local HavanoPOS module
            local_tenants = self.env['havanoposdesk.tenant'].sudo().search([])
            for t in local_tenants:
                phone = getattr(t, 'phone', '')
                if not phone and hasattr(t, 'admin_id') and t.admin_id.phone:
                    phone = t.admin_id.phone
                tenants_data.append({
                    'id': str(t.id),
                    'name': t.name,
                    'phone': phone
                })
        elif account.saas_app_url:
            try:
                auth = (account.saas_username, account.saas_password) if account.saas_username and account.saas_password else None
                response = requests.get(f"{account.saas_app_url.rstrip('/')}/api/get_users", auth=auth, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for t in data.get('users', []):
                        tenants_data.append({
                            'id': str(t.get('id')),
                            'name': t.get('name'),
                            'phone': t.get('phone')
                        })
            except Exception as e:
                _logger.error(f"Error fetching remote tenants from SaaS API: {e}")
        for t_data in tenants_data:
            if not t_data.get('phone'):
                continue
                
            existing = self.search([('account_id', '=', account.id), ('tenant_id', '=', t_data['id'])])
            if not existing:
                new_tenant = self.create({
                    'account_id': account.id,
                    'tenant_id': t_data['id'],
                    'tenant_name': t_data['name'],
                    'tenant_phone': t_data['phone'],
                })
                # Send welcome message upon new tenant discovery
                if account.saas_welcome_template_id:
                    self._send_whatsapp_message(
                        account, 
                        t_data['phone'], 
                        account.saas_welcome_template_id, 
                        [t_data['name']]
                    )
                new_tenant.welcome_message_sent = True

    def _process_daily_sales(self, account):
        tz = timezone(self.env.user.tz or 'UTC')
        now = datetime.now(tz)
        current_time_float = now.hour + now.minute / 60.0
        current_date = now.date()

        # Find tenants whose scheduled time is reached and haven't received it today
        tenants_to_send = self.search([
            ('account_id', '=', account.id),
            ('scheduled_time', '<=', current_time_float),
            '|', ('last_sales_sent_date', '!=', current_date), ('last_sales_sent_date', '=', False)
        ])

        has_local_saas = 'havanoposdesk.tenant' in self.env

        for tenant in tenants_to_send:
            store_lines = []
            if has_local_saas:
                try:
                    stores = self.env['havanoposdesk.store'].sudo().search([('tenant_id', '=', int(tenant.tenant_id))])
                    from odoo.addons.havanoposdesk_odoo.inventory.controllers.api import API
                    api_controller = API()

                    for store in stores:
                        # Query today's POS orders for this store directly from local models
                        today_start = datetime.now(timezone(self.env.user.tz or 'UTC')).replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        orders = self.env['pos.order'].sudo().search([
                            ('store_id', '=', store.id),
                            ('date_order', '>=', today_start.strftime('%Y-%m-%d %H:%M:%S')),
                            ('state', 'in', ['done', 'invoiced']),
                        ])
                        total = sum(orders.mapped('amount_total'))
                        num_orders = len(orders)
                        currency = store.currency_id.symbol if hasattr(store, 'currency_id') and store.currency_id else '$'
                        store_lines.append(
                            f"🏪 *{store.name}*\n"
                            f"   Sales: {currency}{total:,.2f}  |  Orders: {num_orders}"
                        )
                except Exception as e:
                    _logger.error(f"Error fetching local sales for tenant {tenant.tenant_name}: {e}")
            elif account.saas_app_url:
                try:
                    auth = (account.saas_username, account.saas_password) if account.saas_username and account.saas_password else None
                    response = requests.get(
                        f"{account.saas_app_url.rstrip('/')}/api/daily_sales",
                        params={'tenant_id': tenant.tenant_id},
                        auth=auth,
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for store in data.get('stores', []):
                            total = store.get('sales_total', 0)
                            num_orders = store.get('orders_count', 0)
                            currency = store.get('currency', '$')
                            store_lines.append(
                                f"🏪 *{store.get('name')}*\n"
                                f"   Sales: {currency}{total:,.2f}  |  Orders: {num_orders}"
                            )
                except Exception as e:
                    _logger.error(f"Error fetching remote sales for tenant {tenant.tenant_name}: {e}")

            if store_lines and account.saas_daily_sales_template_id:
                sales_data_str = "\n\n".join(store_lines)
                self._send_whatsapp_message(
                    account,
                    tenant.tenant_phone,
                    account.saas_daily_sales_template_id,
                    [tenant.tenant_name, sales_data_str]
                )
                tenant.last_sales_sent_date = current_date


    def _send_whatsapp_message(self, account, phone, template, variables):
        try:
            # We use standard WhatsApp composer to send the template
            composer = self.env['whatsapp.composer'].with_context(
                default_wa_account_id=account.id,
                default_wa_template_id=template.id,
                default_phone=phone,
            ).create({})
            
            # Send action
            composer.action_send_whatsapp_template()
            _logger.info(f"SaaS notification sent successfully to {phone}")
        except Exception as e:
            _logger.error(f"Failed to send WA SaaS message to {phone}: {e}")
