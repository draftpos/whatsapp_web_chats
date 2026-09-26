from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import threading

_logger = logging.getLogger(__name__)

class WAChatbotSession(models.Model):
    _name = 'wa.chatbot.session'
    _inherit = 'wa.chatbot.session'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        # Prevent creating bot sessions if the account bot is disabled
        filtered_vals = []
        for vals in vals_list:
            account_id = vals.get('account_id')
            if not account_id and 'chatbot_id' in vals:
                # Try to get account from chatbot
                chatbot = self.env['wa.chatbot'].sudo().browse(vals['chatbot_id'])
                if hasattr(chatbot, 'account_id'):
                    account_id = chatbot.account_id.id
            
            if account_id:
                account = self.env['whatsapp.account'].sudo().browse(account_id)
                if account.exists() and hasattr(account, 'wa_bot_active') and not account.wa_bot_active:
                    _logger.info("Blocked creation of wa.chatbot.session because wa_bot_active is False")
                    continue
            filtered_vals.append(vals)
            
        if not filtered_vals:
            return self.env['wa.chatbot.session']
            
        return super().create(filtered_vals)

class WhatsAppAccount(models.Model):
    _inherit = 'whatsapp.account'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    image_1920 = fields.Image(string="Profile Picture", max_width=1920, max_height=1920)
    wa_bot_active = fields.Boolean(string="Automated Bot Responses", default=True)
    wa_department_routing_active = fields.Boolean(string="Auto Response for Departments", default=True)
    followup_rule_ids = fields.One2many('whatsapp.followup.rule', 'account_id', string='Auto Follow-up Sequence')

    wa_group_auto_message_share = fields.Boolean("WhatsApp Group Auto Message Share", default=False)
    wa_group_auto_message_text = fields.Text("Auto Message Text", default="Hi you can also joing our group for Fitted Kitchen Designs more vairables group link")
    wa_group_auto_message_link = fields.Char("Auto Message Link")

    # School Integration
    allow_school_balances = fields.Boolean(string="Allow sending balances from school app", default=False)
    school_integration_type = fields.Selection([
        ('local', 'Local (Same Database)'),
        ('remote', 'Remote Server')
    ], string="Integration Type", default='local')
    school_app_url = fields.Char(string="School App URL")
    school_db_name = fields.Char(string="School Database Name")
    school_username = fields.Char(string="School Username/Email")
    school_password = fields.Char(string="School Password")
    
    is_school_installed = fields.Boolean(compute="_compute_is_school_installed")

    def _compute_is_school_installed(self):
        for rec in self:
            rec.is_school_installed = 'havano.student' in self.env

    school_balance_wa_template_id = fields.Many2one(
        'whatsapp.template', 
        string="School Balance Template",
        domain="[('status', '=', 'approved')]",
        help="Used to bypass 24-hour rule. Variables must be: {{1}}: Parent Name, {{2}}: Student Name, {{3}}: School Name, {{4}}: Balance, {{5}}: Doc Type"
    )
    
    # Fallback field in case older/custom views still reference it
    school_balance_template = fields.Many2one(
        'whatsapp.template',
        related='school_balance_wa_template_id',
        string="Legacy School Balance Template",
        readonly=False
    )
    school_auto_send_frequency = fields.Selection([
        ('manual', 'Manual Only'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Date')
    ], string="Auto-Send Frequency", default='manual')
    school_auto_send_custom_date = fields.Date(string="Custom Send Date")

    # POS Integration
    allow_pos_sales_summary = fields.Boolean(string="Allow sending daily POS sales summary", default=False)
    pos_sales_wa_template_id = fields.Many2one(
        'whatsapp.template', 
        string="POS Sales Summary Template",
        domain="[('status', '=', 'approved')]",
        help="Variables: {{1}}: Manager Name, {{2}}: Date, {{3}}: Sales Amount, {{4}}: Store Name, {{5}}: Receipts Count, {{6}}: Profit Amount"
    )
    pos_manager_mobile = fields.Char(string="Manager WhatsApp Number (with country code)")
    pos_manager_name = fields.Char(string="Manager Name", default="Manager")
    pos_sales_auto_send_frequency = fields.Selection([
        ('manual', 'Manual Only'),
        ('daily', 'Daily')
    ], string="POS Auto-Send Frequency", default='manual')

    @api.model
    def _cron_sync_school_balances(self):
        accounts = self.search([('allow_school_balances', '=', True), ('school_auto_send_frequency', '!=', 'manual')])
        from datetime import date
        today = date.today()
        
        for acc in accounts:
            if acc.school_auto_send_frequency == 'custom' and acc.school_auto_send_custom_date != today:
                continue
                
            try:
                if acc.school_integration_type == 'local':
                    acc._sync_school_balances_local()
                elif acc.school_integration_type == 'remote':
                    acc._sync_school_balances_remote()
            except Exception as e:
                _logger.error(f"Failed to sync school balances for account {acc.name}: {str(e)}")

    @api.model
    def _cron_sync_pos_sales_summary(self):
        accounts = self.search([('allow_pos_sales_summary', '=', True), ('pos_sales_auto_send_frequency', '=', 'daily')])
        for acc in accounts:
            try:
                acc._sync_pos_sales_summary()
            except Exception as e:
                _logger.error(f"Failed to sync POS sales for account {acc.name}: {str(e)}")

    def _sync_pos_sales_summary(self):
        self.ensure_one()
        if 'pos.order' not in self.env:
            _logger.warning("POS module not installed.")
            return

        wa_template = self.pos_sales_wa_template_id
        if not wa_template:
            return
            
        manager_phone = self.pos_manager_mobile
        if not manager_phone:
            return

        from datetime import date
        today = date.today()

        # Search pos.orders for today and this company
        orders = self.env['pos.order'].search([
            ('company_id', '=', self.company_id.id),
            ('date_order', '>=', today.strftime('%Y-%m-%d 00:00:00')),
            ('date_order', '<=', today.strftime('%Y-%m-%d 23:59:59')),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ])

        # Group by store (pos.config)
        stores_data = {}
        for order in orders:
            config = order.session_id.config_id
            if config not in stores_data:
                stores_data[config] = {'sales': 0.0, 'receipts': 0, 'profit': 0.0}
            
            stores_data[config]['sales'] += order.amount_total
            stores_data[config]['receipts'] += 1
            
            margin = getattr(order, 'margin', 0.0)
            stores_data[config]['profit'] += margin

        manager_name = self.pos_manager_name or 'Manager'
        date_str = today.strftime('%d %b %Y')
        phone = manager_phone.replace(' ', '').replace('+', '')

        for config, data in stores_data.items():
            store_name = config.name
            sales = f"${data['sales']:,.2f}"
            receipts = str(data['receipts'])
            profit = f"${data['profit']:,.2f}"
            
            free_text_json = {
                'free_text_1': manager_name,
                'free_text_2': date_str,
                'free_text_3': sales,
                'free_text_4': store_name,
                'free_text_5': receipts,
                'free_text_6': profit,
            }
            
            local_partner = self.env['res.partner'].search([('mobile', '=', manager_phone)], limit=1)
            if not local_partner:
                local_partner = self.env.user.partner_id
                
            target_model = wa_template.model_id.model or 'res.partner'
            target_record = self.env[target_model].sudo().search([], limit=1)
            if not target_record:
                target_record = local_partner
            
            mail_msg = target_record.sudo().message_post(
                body=f'[WhatsApp Template Sent: {wa_template.template_name} - {store_name}]',
                message_type='comment',
                subtype_xmlid='mail.mt_note',
                author_id=self.env.user.partner_id.id,
            )
            msg_vals = {
                'wa_account_id': self.id,
                'mobile_number': phone,
                'wa_template_id': wa_template.id,
                'free_text_json': free_text_json,
                'mail_message_id': mail_msg.id,
                'body': f'[WhatsApp Template Sent: {wa_template.template_name} - {store_name}]',
                'state': 'outgoing',
                'message_type': 'outbound',
            }
            wa_msg = self.env['whatsapp.message'].create(msg_vals)
            wa_msg._send(force_send_by_cron=False)

    def _generate_balance_message(self, student_name, parent_name, balance):
        return f"Hello {parent_name}, the current balance for {student_name} is {balance}."

    def _sync_school_balances_local(self):
        self.ensure_one()
        # Find all posted invoices that are out of balance (receivable)
        # Assuming havano.student is linked to res.partner and account.move
        if 'havano.student' not in self.env:
            _logger.warning("Local sync failed: havano_schools_odoo is not installed on this database.")
            return

        moves = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ], order='id desc', limit=100) # Process latest 100 to avoid long crons

        wa_template = self.school_balance_wa_template_id
        if not wa_template:
            _logger.warning("School balance auto-sync skipped: no approved WhatsApp template configured on account %s.", self.name)
            return
        school_name = self.company_id.name or 'Our School'

        for move in moves:
            if move.amount_residual <= 0:
                continue

            # Check if this move is already logged
            existing_log = self.env['whatsapp.school.balance.log'].search([
                ('whatsapp_account_id', '=', self.id),
                ('move_id_ref', '=', move.id)
            ], limit=1)
            
            if existing_log and existing_log.status == 'sent':
                continue

            student = self.env['havano.student'].search([('partner_id', '=', move.partner_id.id)], limit=1)
            if not student:
                continue

            # Need to find the parent
            parent = self.env['havano.parent'].search([('student_ids', 'in', student.id)], limit=1)
            if not parent:
                continue

            # Safe fallback for mobile or phone, since some DBs might not have mobile field
            try:
                parent_phone = parent.mobile or parent.phone or parent.partner_id.mobile or parent.partner_id.phone
            except AttributeError:
                parent_phone = parent.phone or getattr(parent.partner_id, 'mobile', False) or parent.partner_id.phone
            if not parent_phone:
                self._create_balance_log(student.name, parent.name, False, move.amount_residual, move.id, 'billing', 'failed', 'Parent has no phone number.')
                continue

            # Send message via WhatsApp
            try:
                # Normalize phone (very basic, actual implementation should use standard phone formatting)
                phone = parent_phone.replace(' ', '').replace('+', '')
                
                # Generate PDF Report
                attachment = False
                try:
                    import base64
                    from datetime import date
                    from dateutil.relativedelta import relativedelta
                    
                    start_date = date.today().replace(day=1) - relativedelta(months=1)
                    end_date = date.today()
                    
                    wizard = self.env['customer.statement.wizard'].create({
                        'partner_id': parent.id,
                        'start_date': start_date,
                        'end_date': end_date
                    })
                    
                    report = self.env.ref('havano_schools_odoo.statement_receipt')
                    pdf_content, _ = report._render_qweb_pdf(wizard.id)
                    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                    
                    attachment = self.env['ir.attachment'].create({
                        'name': f"Statement_{student.name}_{date.today()}.pdf",
                        'type': 'binary',
                        'datas': pdf_base64,
                        'res_model': 'whatsapp.message',
                        'mimetype': 'application/pdf'
                    })
                except Exception as e:
                    _logger.error(f"Failed to generate PDF for {student.name}: {e}")
                    attachment = False

                free_text_json = {
                    'free_text_1': parent.name or 'Parent',
                    'free_text_2': student.name or 'Student',
                    'free_text_3': school_name or 'School',
                    'free_text_4': str(move.amount_residual),
                    'free_text_5': 'Statement'
                }
                local_partner = self.env['res.partner'].search([('mobile', '=', parent_phone)], limit=1)
                if not local_partner:
                    local_partner = self.env.user.partner_id
                    
                target_model = wa_template.model_id.model or 'res.partner'
                target_record = self.env[target_model].sudo().search([], limit=1)
                if not target_record:
                    if target_model == 'account.move':
                        target_record = self.env[target_model].sudo().create({'partner_id': self.env.user.partner_id.id, 'move_type': 'out_invoice'})
                    else:
                        target_record = local_partner

                mail_msg = target_record.sudo().message_post(
                    body=f'[WhatsApp Template Sent: {wa_template.template_name}]',
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                    author_id=self.env.user.partner_id.id,
                )
                msg_vals = {
                    'wa_account_id': self.id,
                    'mobile_number': phone,
                    'wa_template_id': wa_template.id,
                    'free_text_json': free_text_json,
                    'mail_message_id': mail_msg.id,
                    'body': f'[WhatsApp Template Sent: {wa_template.template_name}]',
                    'state': 'outgoing',
                    'message_type': 'outbound',
                }
                if attachment:
                    msg_vals['attachment_id'] = attachment.id

                wa_msg = self.env['whatsapp.message'].create(msg_vals)
                wa_msg._send(force_send_by_cron=False)
                
                self._create_balance_log(student.name, parent.name, parent_phone, move.amount_residual, move.id, 'billing', 'sent', '')
            except Exception as e:
                self._create_balance_log(student.name, parent.name, parent_phone, move.amount_residual, move.id, 'billing', 'failed', str(e))

    def _sync_school_balances_remote(self):
        self.ensure_one()
        import xmlrpc.client
        if not all([self.school_app_url, self.school_db_name, self.school_username, self.school_password]):
            _logger.warning("Remote sync failed: Missing credentials.")
            return

        url = self.school_app_url.rstrip('/')
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        try:
            uid = common.authenticate(self.school_db_name, self.school_username, self.school_password, {})
            if not uid:
                _logger.error("Authentication failed for remote school app.")
                return
        except Exception as e:
            _logger.error(f"Failed to connect to remote school app: {e}")
            return

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Search recent posted invoices
        move_ids = models.execute_kw(self.school_db_name, uid, self.school_password, 'account.move', 'search', [[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]], {'limit': 100, 'order': 'id desc'})
        if not move_ids:
            return

        moves = models.execute_kw(self.school_db_name, uid, self.school_password, 'account.move', 'read', [move_ids], {'fields': ['partner_id', 'amount_residual']})
        
        wa_template = self.school_balance_wa_template_id
        if not wa_template:
            _logger.warning("School balance remote auto-sync skipped: no approved WhatsApp template configured on account %s.", self.name)
            return
        school_name = self.company_id.name or 'Our School'

        for move in moves:
            if move.get('amount_residual', 0) <= 0:
                continue

            existing_log = self.env['whatsapp.school.balance.log'].search([
                ('whatsapp_account_id', '=', self.id),
                ('move_id_ref', '=', move['id'])
            ], limit=1)
            
            if existing_log and existing_log.status == 'sent':
                continue

            partner_id = move['partner_id'][0] if move.get('partner_id') else False
            if not partner_id:
                continue

            # Find student
            student_ids = models.execute_kw(self.school_db_name, uid, self.school_password, 'havano.student', 'search', [[('partner_id', '=', partner_id)]], {'limit': 1})
            if not student_ids:
                continue
                
            students = models.execute_kw(self.school_db_name, uid, self.school_password, 'havano.student', 'read', [student_ids], {'fields': ['name']})
            student_name = students[0]['name']

            # Find parent
            parent_ids = models.execute_kw(self.school_db_name, uid, self.school_password, 'havano.parent', 'search', [[('student_ids', 'in', student_ids[0])]], {'limit': 1})
            if not parent_ids:
                continue
                
            parents = models.execute_kw(self.school_db_name, uid, self.school_password, 'havano.parent', 'read', [parent_ids], {'fields': ['name', 'phone']})
            parent = parents[0] if parents else None
            if not parent:
                continue
            parent_phone = parent.get('phone')
            
            if not parent_phone:
                self._create_balance_log(student_name, parent['name'], False, move['amount_residual'], move['id'], 'billing', 'failed', 'Parent has no phone number.')
                continue

            try:
                phone = parent_phone.replace(' ', '').replace('+', '')
                local_partner = self.env['res.partner'].search([('mobile', '=', parent_phone)], limit=1)
                if not local_partner:
                    local_partner = self.env.user.partner_id
                    
                target_model = wa_template.model_id.model or 'res.partner'
                target_record = self.env[target_model].sudo().search([], limit=1)
                if not target_record:
                    if target_model == 'account.move':
                        target_record = self.env[target_model].sudo().create({'partner_id': self.env.user.partner_id.id, 'move_type': 'out_invoice'})
                    else:
                        target_record = local_partner
                        
                free_text_json = {
                    'free_text_1': parent['name'] or 'Parent',
                    'free_text_2': student_name or 'Student',
                    'free_text_3': school_name or 'School',
                    'free_text_4': str(move['amount_residual']),
                    'free_text_5': 'Statement'
                }
                mail_msg = target_record.sudo().message_post(
                    body=f'[WhatsApp Template Sent: {wa_template.template_name}]',
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                    author_id=self.env.user.partner_id.id,
                )
                self.env['whatsapp.message'].create({
                    'wa_account_id': self.id,
                    'mobile_number': phone,
                    'wa_template_id': wa_template.id,
                    'free_text_json': free_text_json,
                    'mail_message_id': mail_msg.id,
                    'body': f'[WhatsApp Template Sent: {wa_template.template_name}]',
                    'state': 'outgoing',
                    'message_type': 'outbound',
                })._send(force_send_by_cron=False)
                self._create_balance_log(student_name, parent['name'], parent_phone, move['amount_residual'], move['id'], 'billing', 'sent', '')
            except Exception as e:
                self._create_balance_log(student_name, parent['name'], parent_phone, move['amount_residual'], move['id'], 'billing', 'failed', str(e))

    def _create_balance_log(self, student_name, parent_name, parent_number, balance, move_id, trigger_type, status, error_msg):
        self.env['whatsapp.school.balance.log'].create({
            'whatsapp_account_id': self.id,
            'student_name': student_name,
            'parent_name': parent_name,
            'parent_number': parent_number,
            'balance_amount': balance,
            'move_id_ref': move_id,
            'trigger_type': trigger_type,
            'status': status,
            'error_message': error_msg
        })

    @api.model
    def toggle_account_bot(self, wa_account_id, active):
        account = self.browse(int(wa_account_id))
        if account.exists():
            account.sudo().wa_bot_active = bool(active)
            if not active and 'wa.chatbot.session' in self.env:
                try:
                    sessions = self.env['wa.chatbot.session'].sudo().search([])
                    if sessions and 'account_id' in sessions[0]._fields:
                        sessions.filtered(lambda s: s.account_id.id == account.id).unlink()
                    else:
                        sessions.unlink() # fallback if account_id isn't the relation
                except Exception as e:
                    pass
            return True
        return False

    @api.model
    def get_whatsapp_web_accounts(self):
        """Return WhatsApp accounts scoped to the current tenant (company).
        Falls back to including legacy accounts with no tenant_id so no data is lost."""
        current_company = self.env.company
        domain = ['|', ('tenant_id', '=', False), ('tenant_id', '=', current_company.id)]
        
        if not self.env.is_admin():
            if hasattr(self.env.user, 'whatsapp_account_ids'):
                domain.append(('id', 'in', self.env.user.whatsapp_account_ids.ids))
            
        accounts = self.sudo().search_read(
            domain,
            ['id', 'name', 'image_1920', 'wa_bot_active', 'tenant_id'],
        )
        # Normalize tenant_id and decode binary image
        for acc in accounts:
            if isinstance(acc.get('tenant_id'), (list, tuple)):
                pass  # already [id, name]
            elif acc.get('tenant_id'):
                company = self.env['res.company'].sudo().browse(acc['tenant_id'])
                acc['tenant_id'] = [company.id, company.name]
            else:
                acc['tenant_id'] = False
                
            # Decode binary image to base64 string for JSON serialization
            if acc.get('image_1920') and isinstance(acc['image_1920'], bytes):
                acc['image_1920'] = acc['image_1920'].decode('utf-8')
                
        return accounts

    @api.model
    def update_tenant_data(self):
        """One-time data migration: stamp tenant_id on all existing records
        that are missing it, deriving the value from the linked WhatsApp account."""
        _logger.info("Starting tenant_id data migration...")

        # ── 0. Stamp whatsapp.account ─────────────────────────────────────────
        accounts = self.sudo().search([('tenant_id', '=', False), ('company_id', '!=', False)])
        for acc in accounts:
            acc.sudo().write({'tenant_id': acc.company_id.id})
        _logger.info("Stamped %d whatsapp.account records", len(accounts))

        # ── 1. Stamp discuss.channel ──────────────────────────────────────────
        channels = self.env['discuss.channel'].sudo().search([
            ('channel_type', '=', 'whatsapp'),
        ])

        for ch in channels:
            new_tenant = False
            if ch.wa_account_id and ch.wa_account_id.tenant_id:
                new_tenant = ch.wa_account_id.tenant_id.id
            elif ch.wa_account_id and ch.wa_account_id.company_id:
                new_tenant = ch.wa_account_id.company_id.id
            if new_tenant and not ch.tenant_id:
                ch.sudo().write({'tenant_id': new_tenant, 'company_id': new_tenant})
        _logger.info("Stamped %d discuss.channel records", len(channels))

        # ── 2. Stamp whatsapp.message via mail_message → discuss.channel ─────
        wa_messages = self.env['whatsapp.message'].sudo().search([
            '|', ('mail_message_id.res_id', '!=', False), ('wa_account_id', '!=', False),
        ])
        for msg in wa_messages:
            if not msg.tenant_id and msg.wa_account_id and msg.wa_account_id.tenant_id:
                msg.sudo().write({'tenant_id': msg.wa_account_id.tenant_id.id})
        _logger.info("Stamped %d whatsapp.message records", len(wa_messages))

        # ── 3. Stamp mail.message (scoped to whatsapp discuss channels) ───────
        stamped_channel_ids = self.env['discuss.channel'].sudo().search([
            ('channel_type', '=', 'whatsapp'),
            ('tenant_id', '!=', False),
        ])
        for ch in stamped_channel_ids:
            mail_msgs = self.env['mail.message'].sudo().search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', ch.id),
                ('tenant_id', '=', False),
            ])
            if mail_msgs:
                mail_msgs.sudo().write({'tenant_id': ch.tenant_id.id})
        _logger.info("Stamped mail.message records under whatsapp channels")

        _logger.info("tenant_id migration complete.")
        return True

    @api.model
    def mark_whatsapp_web_messages_read(self, channel_id):
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if channel.exists():
            # Find the last message and explicitly mark it seen for the CURRENT user
            last_msg = self.env['mail.message'].sudo().search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id)
            ], order='id desc', limit=1)
            
            if last_msg:
                # Make read status GLOBAL: If one agent reads it, it's read for everyone
                members = self.env['discuss.channel.member'].sudo().search([
                    ('channel_id', '=', channel.id)
                ])
                members.sudo().write({'seen_message_id': last_msg.id})
            
            # Also clear our custom flag so the badge disappears
            if channel.wa_is_unread_global:
                channel.sudo().write({'wa_is_unread_global': False})
            return True
        return False

    @api.model
    def get_whatsapp_web_channels(self, wa_account_id=None, limit=5000, offset=0):
        current_company = self.env.company
        domain = [
            ('channel_type', '=', 'whatsapp'),
            '|', ('whatsapp_partner_id', '!=', False), ('whatsapp_number', '!=', False),
            # Tenant scoping: show channels belonging to current company OR legacy unscoped ones
            '|', ('tenant_id', '=', False), ('tenant_id', '=', current_company.id),
        ]
        if wa_account_id:
            domain.append(('wa_account_id', '=', int(wa_account_id)))
            
        if not self.env.is_admin():
            if hasattr(self.env.user, 'whatsapp_account_ids'):
                domain.append(('wa_account_id', 'in', self.env.user.whatsapp_account_ids.ids))
        
        channels = self.env['discuss.channel'].sudo().search(domain, limit=int(limit), offset=int(offset), order='write_date desc, id desc')
        
        res = []
        if not channels:
            return res

        # 1. Bulk fetch last message for each channel
        channel_ids = tuple(channels.ids)
        self.env.cr.execute("""
            SELECT res_id, MAX(id) as last_msg_id
            FROM mail_message
            WHERE model = 'discuss.channel' AND res_id IN %s
            GROUP BY res_id
        """, [channel_ids])
        last_msg_ids = {row[0]: row[1] for row in self.env.cr.fetchall()}
        
        last_messages = {}
        if last_msg_ids:
            msg_recs = self.env['mail.message'].sudo().search([('id', 'in', list(last_msg_ids.values()))])
            for m in msg_recs:
                last_messages[m.res_id] = m
                
        # 2. Bulk fetch whatsapp message states
        wa_states = {}
        if last_msg_ids:
            wa_msgs = self.env['whatsapp.message'].sudo().search([('mail_message_id', 'in', list(last_msg_ids.values()))])
            for w in wa_msgs:
                wa_states[w.mail_message_id.id] = w.state
                
        # 3. Bulk fetch channel members for current user
        members = self.env['discuss.channel.member'].sudo().search([
            ('channel_id', 'in', channels.ids),
            ('partner_id', '=', self.env.user.partner_id.id)
        ])
        seen_ids = {m.channel_id.id: (m.seen_message_id.id if m.seen_message_id else 0) for m in members}
        
        # 4. Prepare excluded partners
        try:
            excluded = self.env.ref('base.group_user').sudo().users.mapped('partner_id').ids
        except Exception:
            excluded = [self.env.user.partner_id.id]
        public_partner = self.env.ref('base.public_partner', raise_if_not_found=False)
        if public_partner:
            excluded.append(public_partner.id)

        import re
        for c in channels:
            last_message = last_messages.get(c.id)
            
            sort_date_obj = last_message.date if last_message else c.write_date
            sort_date = sort_date_obj.strftime('%Y-%m-%dT%H:%M:%SZ') if sort_date_obj else ''
            
            last_msg_body = ''
            last_msg_time = ''
            last_msg_is_me = False
            last_msg_wa_state = False
            if last_message:
                raw = re.sub(r'<[^>]+>', '', last_message.body or '').strip()
                last_msg_body = raw[:60] + ('...' if len(raw) > 60 else '')
                last_msg_time = last_message.date.strftime('%Y-%m-%dT%H:%M:%SZ') if last_message.date else ''
                
                # Fetch whatsapp.message state
                last_msg_wa_state = wa_states.get(last_message.id, False)
                
                # Determine is_me
                if last_message.author_id and last_message.author_id.id == self.env.user.partner_id.id:
                    last_msg_is_me = True
                elif self.env.user.has_group('base.group_user'):
                    if last_msg_wa_state == 'received':
                        last_msg_is_me = False
                    elif last_message.author_id:
                        if c.whatsapp_partner_id and last_message.author_id.id == c.whatsapp_partner_id.id:
                            last_msg_is_me = False
                        else:
                            if public_partner and last_message.author_id.id == public_partner.id:
                                last_msg_is_me = False
                            else:
                                last_msg_is_me = True
                    else:
                        last_msg_is_me = False
                else:
                    if last_message.author_id and c.whatsapp_partner_id and last_message.author_id.id == c.whatsapp_partner_id.id:
                        last_msg_is_me = True
                    else:
                        last_msg_is_me = False
            
            seen_id = seen_ids.get(c.id, 0)
            
            unread_count = 0
            domain_unread = []
            if not c.wa_is_unread_global or last_msg_is_me:
                unread_count = 0
                if c.wa_is_unread_global:
                    c.sudo().write({'wa_is_unread_global': False})
            else:
                domain_unread = [
                    ('model', '=', 'discuss.channel'),
                    ('res_id', '=', c.id),
                    ('id', '>', seen_id),
                    ('message_type', 'not in', ['notification', 'user_notification']),
                ]
                domain_unread = ['|', ('author_id', '=', False), ('author_id', 'not in', excluded)] + domain_unread
                unread_count = self.env['mail.message'].sudo().search_count(domain_unread)
            
            import logging
            _logger = logging.getLogger(__name__)
            _logger.debug("DEBUG unread: channel=%s, seen_id=%s, domain=%s, unread_count=%s", c.id, seen_id, domain_unread, unread_count)

            
            import re
            def clean_name(n):
                if not n: return n
                # Strip any trailing parenthetical e.g. "(School)", "(Havano Support)", etc.
                return re.sub(r'\s*\([^)]+\)\s*$', '', n, flags=re.IGNORECASE).strip()
                
            res.append({
                'id': c.id,
                'name': clean_name(c.name),
                'channel_type': c.channel_type,
                'whatsapp_partner_id': [c.whatsapp_partner_id.id, clean_name(c.whatsapp_partner_id.name)] if c.whatsapp_partner_id else False,
                'wa_account_id': [c.wa_account_id.id, c.wa_account_id.name] if c.wa_account_id else False,
                'tenant_id': [c.tenant_id.id, c.tenant_id.name] if c.tenant_id else False,
                'message_needaction_counter': unread_count,
                'unread_count': unread_count,
                'write_date': sort_date,
                'whatsapp_number': c.whatsapp_number,
                'last_message_preview': last_msg_body,
                'last_message_time': last_msg_time,
                'last_message_is_me': last_msg_is_me,
                'last_message_wa_state': last_msg_wa_state,
                'wa_bot_state': c.wa_bot_state,
                'wa_department': [c.wa_department.id, c.wa_department.name] if c.wa_department else False,
                'wa_agent_id': [c.wa_agent_id.id, c.wa_agent_id.name] if c.wa_agent_id else False,
                'wa_is_done': c.wa_is_done,
                'wa_is_unread_global': c.wa_is_unread_global,
                'wa_is_favourite': c.wa_is_favourite,
                'wa_is_urgent': c.wa_is_urgent,
                'wa_is_muted': c.wa_is_muted,
                'wa_is_blocked': c.wa_is_blocked,
                'wa_disappearing_mode': c.wa_disappearing_mode,
                'wa_tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in c.wa_tag_ids],
            })
            
        res.sort(key=lambda x: x['write_date'], reverse=True)
        show_labels = self.env['ir.config_parameter'].sudo().get_param('whatsapp_web_chats.wa_show_labels', 'True') == 'True'
        return {
            'channels': res,
            'show_labels': show_labels
        }

    @api.model
    def get_whatsapp_web_channel_total(self, wa_account_id=None):
        domain = [('channel_type', '=', 'whatsapp')]
        if wa_account_id:
            domain.append(('wa_account_id', '=', wa_account_id))
        return self.env['discuss.channel'].sudo().search_count(domain)

    @api.model
    def get_all_chat_tags(self):
        current_company = self.env.company
        # Show tags for this company OR unassigned legacy tags
        tags = self.env['wa.chat.tag'].sudo().search(['|', ('tenant_id', '=', False), ('tenant_id', '=', current_company.id)])
        return [{'id': t.id, 'name': t.name, 'color': t.color} for t in tags]

    @api.model
    def update_chat_tags(self, channel_id, tag_ids):
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if channel.exists():
            channel.sudo().write({'wa_tag_ids': [(6, 0, tag_ids)]})
            return True
        return False

    @api.model
    def set_whatsapp_chat_state(self, channel_id, field, value):
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if channel.exists() and field in ['wa_is_done', 'wa_is_unread_global', 'wa_is_favourite', 'wa_is_urgent']:
            channel.sudo().write({field: bool(value)})
            # If marked as done, remove unread flag
            if field == 'wa_is_done' and value:
                channel.sudo().write({'wa_is_unread_global': False})
                self.mark_whatsapp_web_messages_read(channel_id)
            return {'success': True}
        return {'success': False, 'error': 'Invalid channel or field'}

    @api.model
    def toggle_message_star(self, message_id):
        wa_msg = self.env['whatsapp.message'].sudo().search([('mail_message_id', '=', int(message_id))], limit=1)
        if wa_msg:
            wa_msg.wa_is_starred = not wa_msg.wa_is_starred
            return {'success': True, 'wa_is_starred': wa_msg.wa_is_starred}
        return {'success': False, 'error': 'Message not found'}

    @api.model
    def toggle_message_pin(self, message_id):
        wa_msg = self.env['whatsapp.message'].sudo().search([('mail_message_id', '=', int(message_id))], limit=1)
        if wa_msg:
            wa_msg.wa_is_pinned = not wa_msg.wa_is_pinned
            return {'success': True, 'wa_is_pinned': wa_msg.wa_is_pinned}
        return {'success': False, 'error': 'Message not found'}

    @api.model
    def send_whatsapp_reaction(self, message_id, emoji):
        """Sends a reaction to a specific WhatsApp message via the Cloud API"""
        import requests
        wa_msg = self.env['whatsapp.message'].sudo().search([('mail_message_id', '=', int(message_id))], limit=1)
        if not wa_msg or not wa_msg.msg_uid:
            return {'success': False, 'error': 'Message not found or has no WhatsApp ID'}
            
        channel = self.env['discuss.channel'].sudo().search([('message_ids', 'in', [wa_msg.mail_message_id.id])], limit=1)
        if not channel:
            return {'success': False, 'error': 'Channel not found'}
            
        account = channel.wa_account_id
        if not account or not account.phone_uid or not account.token:
            return {'success': False, 'error': 'WhatsApp account not configured properly'}
            
        phone = channel.whatsapp_number or (channel.whatsapp_partner_id and channel.whatsapp_partner_id.phone)
        if not phone:
            return {'success': False, 'error': 'No phone number for channel'}

        url = f"https://graph.facebook.com/v19.0/{account.phone_uid}/messages"
        headers = {
            "Authorization": f"Bearer {account.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "reaction",
            "reaction": {
                "message_id": wa_msg.msg_uid,
                "emoji": emoji
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            # Update local DB
            wa_msg.sudo().write({'wa_reaction_me': emoji})
            return {'success': True, 'emoji': emoji, 'message_id': message_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def send_whatsapp_sticker(self, channel_id, attachment_id):
        """Sends a sticker via the Cloud API using an Odoo attachment"""
        import requests
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if not channel:
            return {'success': False, 'error': 'Channel not found'}
            
        account = channel.wa_account_id
        if not account or not account.phone_uid or not account.token:
            return {'success': False, 'error': 'WhatsApp account not configured properly'}
            
        phone = channel.whatsapp_number or (channel.whatsapp_partner_id and channel.whatsapp_partner_id.phone)
        if not phone:
            return {'success': False, 'error': 'No phone number for channel'}

        attachment = self.env['ir.attachment'].sudo().browse(int(attachment_id))
        if not attachment:
            return {'success': False, 'error': 'Attachment not found'}

        # 1. Upload media to WhatsApp
        upload_url = f"https://graph.facebook.com/v19.0/{account.phone_uid}/media"
        files = {
            'file': (attachment.name, attachment.raw, 'image/webp'),
        }
        data = {
            'messaging_product': 'whatsapp',
            'type': 'image/webp'
        }
        auth_header = {"Authorization": f"Bearer {account.token}"}
        
        try:
            upload_resp = requests.post(upload_url, headers=auth_header, data=data, files=files, timeout=15)
            upload_resp.raise_for_status()
            media_id = upload_resp.json().get('id')
            if not media_id:
                return {'success': False, 'error': 'Failed to get media ID from WhatsApp'}
                
            # 2. Send the sticker message
            msg_url = f"https://graph.facebook.com/v19.0/{account.phone_uid}/messages"
            headers = {
                "Authorization": auth_header["Authorization"],
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone,
                "type": "sticker",
                "sticker": {
                    "id": media_id
                }
            }
            
            response = requests.post(msg_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            # WhatsApp will echo this back to our webhook, which will add it to the chat
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
    @api.model
    def get_whatsapp_web_messages(self, channel_id, offset=0, limit=50):
        import re
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        
        domain = ['|', '&', ('res_id', '=', int(channel_id)), ('model', '=', 'discuss.channel')]
        if channel.whatsapp_number:
            wa_msgs = self.env['whatsapp.message'].sudo().search([
                ('mobile_number', 'in', [channel.whatsapp_number, '+' + channel.whatsapp_number]),
                ('wa_account_id', '=', channel.wa_account_id.id),
                ('mail_message_id', '!=', False)
            ])
            wa_mail_ids = wa_msgs.mapped('mail_message_id').ids
            if wa_mail_ids:
                domain.append(('id', 'in', wa_mail_ids))
            else:
                domain = domain[1:]
        else:
            domain = domain[1:]
            
        messages = self.env['mail.message'].sudo().search(domain, order='id desc', offset=int(offset), limit=int(limit))
        messages = messages.sorted(key=lambda m: m.id)
        
        import re
        def clean_name(n):
            if not n: return n
            return re.sub(r'\s*\(\s*School\s*\)', '', n, flags=re.IGNORECASE).strip()
            
        # Fetch the latest whatsapp.message for this number to catch async errors
        wa_error = False
        if messages and channel.whatsapp_number:
            last_wa = self.env['whatsapp.message'].sudo().search([
                ('mobile_number', 'ilike', channel.whatsapp_number)
            ], order='id desc', limit=1)
            if last_wa and last_wa.state == 'error':
                wa_error = last_wa.failure_reason or last_wa.failure_type or 'Delivery failed'
        
        wa_msgs = self.env['whatsapp.message'].sudo().search([
            ('mail_message_id', 'in', messages.ids)
        ])
        wa_map = {wa.mail_message_id.id: wa for wa in wa_msgs if wa.mail_message_id}
        
        # Fetch recent outbound whatsapp messages for this number to match with echo messages (templates)
        outbound_wa_msgs = []
        if channel.whatsapp_number:
            clean_num = ''.join(filter(str.isdigit, channel.whatsapp_number))
            if clean_num:
                outbound_wa_msgs = self.env['whatsapp.message'].sudo().search([
                    ('mobile_number', 'ilike', clean_num),
                    ('message_type', '=', 'outbound')
                ], order='id desc', limit=30)
        
        res = []
        for m in messages:
            body_text = re.sub(r'<[^>]+>', '', m.body or '').strip()
            
            if m.author_id and m.author_id.id == self.env.user.partner_id.id:
                is_me = True
            elif self.env.user.has_group('base.group_user'):
                wa_rec = wa_map.get(m.id)
                wa_state = wa_rec.state if wa_rec else False
                if wa_state == 'received':
                    is_me = False
                elif m.author_id:
                    if channel.whatsapp_partner_id and m.author_id.id == channel.whatsapp_partner_id.id:
                        is_me = False
                    else:
                        public_partner = self.env.ref('base.public_partner', raise_if_not_found=False)
                        if public_partner and m.author_id.id == public_partner.id:
                            is_me = False
                        else:
                            is_me = True
                else:
                    is_me = False
            else:
                if m.author_id and channel.whatsapp_partner_id and m.author_id.id == channel.whatsapp_partner_id.id:
                    is_me = True
                else:
                    is_me = False
                
            # Format date as UTC ISO string so JS can parse it correctly
            date_str = m.date.strftime('%Y-%m-%dT%H:%M:%SZ') if m.date else False
            
            public_partner = self.env.ref('base.public_partner', raise_if_not_found=False)
            author_data = False
            if m.author_id:
                author_name = clean_name(m.author_id.name)
                # Replace "Public user" with the actual customer name
                if public_partner and m.author_id.id == public_partner.id:
                    customer = channel.whatsapp_partner_id
                    author_name = clean_name(customer.name) if customer else clean_name(channel.name)
                author_data = [m.author_id.id, author_name]
            
            wa_rec = wa_map.get(m.id)
            if not wa_rec and m.author_id and m.author_id.id == self.env.user.partner_id.id:
                # Try to find a matching outbound message by body (for templates echoing on channel)
                for o_wa in outbound_wa_msgs:
                    if o_wa.mail_message_id and o_wa.mail_message_id.body:
                        o_body = re.sub(r'<[^>]+>', '', o_wa.mail_message_id.body).strip()
                        if o_body and (o_body in body_text or body_text in o_body):
                            wa_rec = o_wa
                            break

            wa_state = wa_rec.state if wa_rec else False
            wa_is_starred = wa_rec.wa_is_starred if wa_rec else False
            wa_is_pinned = wa_rec.wa_is_pinned if wa_rec else False
            wa_reaction = wa_rec.wa_reaction if wa_rec else False
            wa_reaction_me = wa_rec.wa_reaction_me if wa_rec else False
            wa_is_edited = '<!--edited-->' in (m.body or '')
            
            quoted_body = False
            quoted_attachment = False
            quoted_author = False
            if m.parent_id:
                # Determine quoted author
                if m.parent_id.author_id:
                    quoted_author = m.parent_id.author_id.name
                else:
                    quoted_author = "You" if getattr(m.parent_id, 'is_me', getattr(m, 'is_me', False)) else "Customer"

                quoted_body = re.sub(r'<[^>]+>', '', m.parent_id.body or '').strip()[:100]
                if m.parent_id.attachment_ids:
                    att = m.parent_id.attachment_ids[0]
                    quoted_attachment = {
                        'id': att.id,
                        'mimetype': att.mimetype,
                        'name': att.name,
                        'access_token': att.access_token if 'access_token' in att else getattr(att, 'access_token', '')
                    }
                    if not quoted_body:
                        if att.mimetype and att.mimetype.startswith('image/'):
                            quoted_body = 'image'
                        elif att.mimetype and att.mimetype.startswith('video/'):
                            quoted_body = 'video'
                        elif att.mimetype and att.mimetype.startswith('audio/'):
                            quoted_body = 'audio'
                        else:
                            quoted_body = 'document'

            atts_data = []
            for a in m.attachment_ids:
                if not a.access_token:
                    a.generate_access_token()
                atts_data.append({
                    'id': a.id,
                    'mimetype': a.mimetype,
                    'name': a.name,
                    'access_token': a.access_token or ''
                })

            msg_dict = {
                'id': m.id,
                'body': m.body,
                'author_id': author_data,
                'date': date_str,
                'message_type': m.message_type,
                'attachment_ids': atts_data,
                'is_me': is_me,
                'isMe': is_me,
                'wa_state': wa_state,
                'wa_is_starred': wa_is_starred,
                'wa_is_pinned': wa_is_pinned,
                'wa_reaction': wa_reaction,
                'wa_reaction_me': wa_reaction_me,
                'is_edited': wa_is_edited,
                'quoted_message_id': m.parent_id.id if m.parent_id else False,
                'quoted_message_body': quoted_body,
                'quoted_attachment': quoted_attachment,
                'quoted_author': quoted_author,
            }
            res.append(msg_dict)
            
        # Attach any recent delivery error to the last outgoing message
        if wa_error and res:
            for i in range(len(res)-1, -1, -1):
                if res[i]['is_me']:
                    res[i]['wa_error'] = wa_error
                    res[i]['wa_state'] = 'error'
                    res[i]['wa_error_msg_id'] = last_wa.id
                    break
                    
        return res

    @api.model
    def edit_whatsapp_message(self, message_id, new_body):
        msg = self.env['mail.message'].sudo().browse(int(message_id))
        if not msg.exists():
            return {'success': False, 'error': 'Message not found'}
        
        # Update the body with the edited flag as an HTML comment
        msg.write({'body': new_body + '<!--edited-->'})
            
        return {'success': True}


    def _process_messages(self, value):
        # Temporarily disable the chatbot if wa_bot_active is False
        original_chatbot = False
        if not self.wa_bot_active:
            if 'chatbot_id' in self._fields:
                original_chatbot = self.chatbot_id
                if original_chatbot:
                    self.sudo().write({'chatbot_id': False})
            
            # Ensure no stray sessions intercept this message
            if 'wa.chatbot.session' in self.env:
                try:
                    sessions = self.env['wa.chatbot.session'].sudo().search([])
                    if sessions and 'account_id' in sessions[0]._fields:
                        sessions.filtered(lambda s: s.account_id.id == self.id).unlink()
                    else:
                        sessions.unlink()
                except Exception:
                    pass
                    
        # Extract whatsapp profile names to update partner names if they are just phone numbers
        wa_names = {}
        for contact in value.get('contacts', []):
            wa_id = contact.get('wa_id')
            profile_name = contact.get('profile', {}).get('name')
            if wa_id and profile_name:
                wa_names[str(wa_id)] = profile_name
                
        try:
            # Get our own phone number(s) to filter out echo-backs of our own sent messages
            own_phone = ''.join([c for c in str(self.phone_uid or '') if c.isdigit()])
            own_phone_alt = ''.join([c for c in str(self.phone_number or '') if c.isdigit()])

            # Build a filtered list — remove any message sent FROM our own number
            # (WhatsApp API echoes back messages we send as webhook events)
            filtered_messages = []
            for message in value.get('messages', []):
                wa_id = message.get('from', '')
                sender_phone = ''.join([c for c in str(wa_id) if c.isdigit()])
                if own_phone and sender_phone == own_phone:
                    continue  # This is an echo of our own outgoing message — skip entirely
                if own_phone_alt and sender_phone == own_phone_alt:
                    continue

                # Mark channel as unread for genuine incoming messages
                clean_phone = sender_phone
                if clean_phone:
                    channel = self.env['discuss.channel'].sudo().search([
                        ('channel_type', '=', 'whatsapp'),
                        ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone]),
                        ('wa_account_id', '=', self.id)
                    ], limit=1)
                    if channel:
                        if channel.whatsapp_number != clean_phone:
                            channel.sudo().write({'whatsapp_number': clean_phone})
                        channel.wa_is_unread_global = True
                        channel.wa_is_done = False
                        
                        # Cancel any pending auto follow-ups since the customer replied
                        self.env['whatsapp.scheduled.message'].sudo().search([
                            ('channel_id', '=', channel.id),
                            ('is_auto_followup', '=', True),
                            ('state', '=', 'pending')
                        ]).write({'state': 'cancelled'})

                # Convert order type messages to text
                if message.get('type') == 'order':
                    order = message.get('order', {})
                    items = order.get('product_items', [])
                    text_lines = ["🛒 *New Order Received!*"]
                    if order.get('text'):
                        text_lines.append(f"Note: {order['text']}")
                    text_lines.append("Items:")
                    for item in items:
                        qty = item.get('quantity', 0)
                        price = item.get('item_price', '')
                        currency = item.get('currency', '')
                        product_id = item.get('product_retailer_id', 'Unknown Item')
                        product = self.env['product.product'].sudo().search([
                            '|', ('default_code', '=', product_id),
                            ('id', '=', int(product_id) if str(product_id).isdigit() else 0)
                        ], limit=1)
                        product_name = product.name if product else product_id
                        text_lines.append(f"- {qty}x {product_name} ({currency} {price})")
                    message['type'] = 'text'
                    message['text'] = {'body': '\n'.join(text_lines)}

                # Handle Reactions
                if message.get('type') == 'reaction':
                    reaction = message.get('reaction', {})
                    orig_msg_id = reaction.get('message_id')
                    emoji = reaction.get('emoji', '')
                    if orig_msg_id:
                        wa_msg = self.env['whatsapp.message'].sudo().search([('msg_uid', '=', orig_msg_id)], limit=1)
                        if wa_msg:
                            wa_msg.wa_reaction = emoji
                    # Do not pass reaction to super(), Odoo standard doesn't support it
                    continue
                    
                # Handle Stickers (convert to image so standard Odoo downloads them)
                if message.get('type') == 'sticker':
                    message['type'] = 'image'
                    message['image'] = message.pop('sticker')

                filtered_messages.append(message)

            # Replace the messages list with the filtered one before calling super
            # This prevents base Odoo from processing or re-sending our own echo-back messages
            value = dict(value)
            value['messages'] = filtered_messages

            res = super()._process_messages(value)
        finally:
            if not self.wa_bot_active and original_chatbot:
                self.sudo().write({'chatbot_id': original_chatbot.id})
                
        # After processing, try to update newly created partners with their WhatsApp profile name
        # if their current name is just a phone number
        for wa_id, profile_name in wa_names.items():
            partner = self.env['res.partner'].sudo().search([
                ('phone', 'ilike', wa_id)
            ], limit=1)
            if partner and partner.name:
                clean_name = ''.join(c for c in partner.name if c.isdigit() or c == '+')
                clean_wa = ''.join(c for c in wa_id if c.isdigit())
                # If the name is basically just their phone number
                if clean_name.endswith(clean_wa) or clean_name.startswith(clean_wa):
                    partner.sudo().write({'name': profile_name})
                    
        # Apply custom routing bot logic — use filtered value so echo-backs never trigger bot replies
        self._process_routing_bot(value)

        # NOTE: Group auto message is triggered via the discuss_channel.message_post hook
        # (see discuss_channel.py). It does NOT need a separate trigger here, as doing so
        # creates a double-fire race condition. The message_post hook + atomic DB flag is
        # the single authoritative path that guarantees exactly-once delivery.

        return res

    def _process_routing_bot(self, value):
        if not self.wa_department_routing_active:
            return
            
        from datetime import datetime, timezone
        
        for message in value.get('messages', []):
            m_type = message.get('type')
            if m_type == 'interactive':
                inter = message.get('interactive', {})
                if inter.get('type') == 'list_reply':
                    text_body = inter.get('list_reply', {}).get('id', '')
                elif inter.get('type') == 'button_reply':
                    text_body = inter.get('button_reply', {}).get('id', '')
                else:
                    text_body = ''
            elif m_type == 'text':
                text_body = message.get('text', {}).get('body', '').strip().lower()
            else:
                continue
                
            wa_id = message.get('from')
            if not wa_id:
                continue
                
            clean_phone = ''.join([c for c in str(wa_id) if c.isdigit() or c == '+'])
            
            # Find the channel
            channel = self.env['discuss.channel'].sudo().search([
                ('channel_type', '=', 'whatsapp'),
                ('whatsapp_number', '=', clean_phone),
                ('wa_account_id', '=', self.id)
            ], limit=1)
            
            if not channel:
                continue
                
            # Check for 24 hours inactivity to reset
            last_msgs = self.env['mail.message'].sudo().search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
                ('message_type', '!=', 'notification')
            ], order='date desc', limit=2)
            
            if len(last_msgs) == 2:
                time_diff = last_msgs[0].date - last_msgs[1].date
                if time_diff.total_seconds() > 24 * 60 * 60:
                    channel.wa_bot_state = False
                    channel.wa_agent_id = False
                    channel.wa_department = False

            # text_body is already extracted above
            
            if not channel.wa_bot_state or channel.wa_bot_state == 'idle':
                channel.wa_bot_state = 'ask_department'
                departments = self.env['hr.department'].sudo().search([])
                if not departments:
                    self._send_bot_reply(channel, "Welcome! No departments are currently available.")
                    return
                
                fallback_lines = ["Welcome! Which department do you need support from?"]
                for i, d in enumerate(departments):
                    fallback_lines.append(f"{i+1}. {d.name}")
                    
                interactive = {
                    "type": "list",
                    "body": {"text": "Welcome! Which department do you need support from?"},
                    "action": {
                        "button": "Departments",
                        "sections": [{
                            "title": "Departments",
                            "rows": [{"id": str(i+1), "title": d.name[:24]} for i, d in enumerate(departments[:10])]
                        }]
                    }
                }
                    
                self._send_bot_reply(channel, "\n".join(fallback_lines), interactive_payload=interactive)
                
            elif channel.wa_bot_state == 'ask_department':
                departments = self.env['hr.department'].sudo().search([])
                selected_dept = False
                try:
                    idx = int(text_body) - 1
                    if 0 <= idx < len(departments):
                        selected_dept = departments[idx]
                except ValueError:
                    pass
                
                if selected_dept:
                    channel.wa_department = selected_dept.id
                    channel.wa_bot_state = 'ask_agent'
                    
                    employees = self.env['hr.employee'].sudo().search([('department_id', '=', selected_dept.id), ('user_id', '!=', False)])
                    wa_users = self.env['res.users'].sudo().search([('wa_department', '=', selected_dept.id)])
                    agents = (employees.mapped('user_id') | wa_users)
                    if not agents:
                        channel.wa_bot_state = 'routed'
                        channel._wa_bot_route_chat()
                        self._send_bot_reply(channel, f"Your chat has been successfully transferred to the {selected_dept.name} department under any available agent. Your issue will be solved soon, and we will get back to you when done.")
                    else:
                        agent_list = "\n".join([f"{i+1}. {a.name}" for i, a in enumerate(agents)])
                        msg = f"Please select an individual in {selected_dept.name} to speak with:\n{agent_list}\n0. Any available agent"
                        
                        rows = [{"id": str(i+1), "title": a.name[:24]} for i, a in enumerate(agents[:9])]
                        rows.append({"id": "0", "title": "Any available agent"})
                        
                        interactive = {
                            "type": "list",
                            "body": {"text": f"Please select an individual in {selected_dept.name} to speak with:"},
                            "action": {
                                "button": "Agents",
                                "sections": [{
                                    "title": "Agents",
                                    "rows": rows
                                }]
                            }
                        }
                        self._send_bot_reply(channel, msg, interactive_payload=interactive)
                else:
                    fallback_lines = ["Invalid selection. Which department do you need support from?"]
                    for i, d in enumerate(departments):
                        fallback_lines.append(f"{i+1}. {d.name}")
                        
                    interactive = {
                        "type": "list",
                        "body": {"text": "Invalid selection. Which department do you need support from?"},
                        "action": {
                            "button": "Departments",
                            "sections": [{
                                "title": "Departments",
                                "rows": [{"id": str(i+1), "title": d.name[:24]} for i, d in enumerate(departments[:10])]
                            }]
                        }
                    }
                    self._send_bot_reply(channel, "\n".join(fallback_lines), interactive_payload=interactive)
                    
            elif channel.wa_bot_state == 'ask_agent':
                if text_body == '0' or text_body == 'any':
                    channel.wa_agent_id = False
                    channel.wa_bot_state = 'routed'
                    channel._wa_bot_route_chat()
                    self._send_bot_reply(channel, f"Your chat has been successfully transferred to the {channel.wa_department.name} department under any available agent. Your issue will be solved soon, and we will get back to you when done.")
                else:
                    employees = self.env['hr.employee'].sudo().search([('department_id', '=', channel.wa_department.id), ('user_id', '!=', False)])
                    wa_users = self.env['res.users'].sudo().search([('wa_department', '=', channel.wa_department.id)])
                    agents = (employees.mapped('user_id') | wa_users)
                    try:
                        idx = int(text_body) - 1
                        if 0 <= idx < len(agents):
                            channel.wa_agent_id = agents[idx].id
                            channel.wa_bot_state = 'routed'
                            channel._wa_bot_route_chat()
                            self._send_bot_reply(channel, f"Your chat has been successfully transferred to the {channel.wa_department.name} department under {agents[idx].name}. Your issue will be solved soon, and we will get back to you when done.")
                        else:
                            self._send_bot_reply(channel, "Invalid selection. Please select an individual or 0 for Any.")
                    except ValueError:
                        self._send_bot_reply(channel, "Invalid selection. Please reply with a number.")

    def _send_bot_reply(self, channel, body_text, interactive_payload=None):
        try:
            # Always post as a comment so Odoo doesn't automatically send a WhatsApp text message
            mail_msg = channel.sudo().message_post(
                body=body_text,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.ref('base.partner_root').id,
            )
            
            # Send via whatsapp api natively
            phone = channel.whatsapp_number or (channel.whatsapp_partner_id and channel.whatsapp_partner_id.phone)
            if phone:
                account = channel.wa_account_id
                if account.phone_uid and account.token:
                    import requests
                    url = f"https://graph.facebook.com/v19.0/{account.phone_uid}/messages"
                    headers = {
                        "Authorization": f"Bearer {account.token}",
                        "Content-Type": "application/json"
                    }
                    if interactive_payload:
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": phone,
                            "type": "interactive",
                            "interactive": interactive_payload
                        }
                    else:
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": phone,
                            "type": "text",
                            "text": {"body": body_text}
                        }
                    try:
                        requests.post(url, headers=headers, json=payload, timeout=5)
                    except Exception:
                        pass
                else:
                    wa_msg = self.env['whatsapp.message'].sudo().create({
                        'mobile_number': phone,
                        'wa_account_id': channel.wa_account_id.id,
                        'mail_message_id': mail_msg.id,
                        'state': 'outgoing',
                        'message_type': 'outbound',
                        'body': body_text,
                    })
                    wa_msg._send(force_send_by_cron=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Failed to send bot reply: %s", e)

    @api.model
    def clear_whatsapp_chat(self, channel_id):
        """ Clears all messages from a whatsapp chat but keeps the chat itself. """
        if not (self.env.is_admin() or self.env.user.has_group('whatsapp.group_whatsapp_admin')):
            return {'success': False, 'error': 'Only administrators can clear chats.'}
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if channel.exists():
                messages = self.env['mail.message'].sudo().search([
                    ('model', '=', 'discuss.channel'),
                    ('res_id', '=', channel.id)
                ])
                messages.unlink()
                return {'success': True}
            return {'success': False, 'error': 'Channel not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def delete_whatsapp_chat(self, channel_id):
        """ Deletes a whatsapp chat (discuss.channel) but preserves the contact (res.partner). """
        if not (self.env.is_admin() or self.env.user.has_group('whatsapp.group_whatsapp_admin')):
            return {'success': False, 'error': 'Only administrators can delete chats.'}
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if channel.exists():
                # Detach the partner reference BEFORE unlinking to prevent cascade deletion of res.partner
                channel.sudo().write({'whatsapp_partner_id': False})

                # Unlink all mail.messages in this channel
                messages = self.env['mail.message'].sudo().search([
                    ('model', '=', 'discuss.channel'),
                    ('res_id', '=', channel.id)
                ])
                messages.unlink()

                # Unlink the channel itself (partner is already detached — safe)
                channel.unlink()
                return {'success': True}
            return {'success': False, 'error': 'Channel not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def delete_whatsapp_message(self, message_id):
        """ Deletes a specific mail.message """
        if not (self.env.is_admin() or self.env.user.has_group('whatsapp.group_whatsapp_admin')):
            return {'success': False, 'error': 'Only administrators can delete messages.'}
        try:
            message = self.env['mail.message'].sudo().browse(int(message_id))
            if message.exists():
                message.unlink()
                return {'success': True}
            return {'success': False, 'error': 'Message not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def delete_message_for_me(self, message_id):
        """ Deletes a message locally in Odoo without retracting via WhatsApp Cloud API """
        if not (self.env.is_admin() or self.env.user.has_group('whatsapp.group_whatsapp_admin')):
            return {'success': False, 'error': 'Only administrators can delete messages.'}
        try:
            message = self.env['mail.message'].sudo().browse(int(message_id))
            if message.exists():
                message.unlink()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def delete_message_for_everyone(self, message_id):
        """ Deletes a message in Odoo AND attempts to retract it via WhatsApp Cloud API """
        if not (self.env.is_admin() or self.env.user.has_group('whatsapp.group_whatsapp_admin')):
            return {'success': False, 'error': 'Only administrators can delete messages.'}
        try:
            message = self.env['mail.message'].sudo().browse(int(message_id))
            if not message.exists():
                return {'success': False, 'error': 'Message not found'}

            # Try to retract via WhatsApp API if we have a wa_message_id
            wa_msg = self.env['whatsapp.message'].sudo().search([
                ('mail_message_id', '=', message.id)
            ], limit=1)

            if wa_msg and wa_msg.msg_uid:
                try:
                    channel = self.env['discuss.channel'].sudo().browse(message.res_id)
                    account = channel.wa_account_id
                    if account and account.token:
                        import requests as req
                        url = f"https://graph.facebook.com/v18.0/{account.phone_uid}/messages/{wa_msg.msg_uid}"
                        req.delete(url, headers={'Authorization': f'Bearer {account.token}'}, timeout=10)
                except Exception as api_err:
                    import logging
                    logging.getLogger(__name__).warning("WhatsApp retract API call failed: %s", api_err)

            message.unlink()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _compress_video_attachment(self, attachment):
        import subprocess
        import tempfile
        import os
        import base64
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            import shutil
            ffmpeg_exe = shutil.which('ffmpeg') or '/usr/bin/ffmpeg'
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                _logger.info("imageio-ffmpeg not installed. Using system ffmpeg.")
        except Exception:
            ffmpeg_exe = '/usr/bin/ffmpeg'

        try:
            raw_data = base64.b64decode(attachment.datas)
            # We MUST always re-encode to ensure H.264 / AAC. 
            # Modern phones use HEVC/H.265 (which is still video/mp4), and Meta API accepts the upload but silently drops the delivery.
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_in:
                temp_in.write(raw_data)
                temp_in_name = temp_in.name
                
            temp_out_name = temp_in_name + "_out.mp4"
            
            cmd = [
                ffmpeg_exe,
                '-y',
                '-i', temp_in_name,
                '-c:v', 'libx264',
                '-profile:v', 'baseline',
                '-level', '3.0',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                temp_out_name
            ]
            
            _logger.info(f"Running video conversion: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0 and os.path.exists(temp_out_name):
                with open(temp_out_name, 'rb') as f:
                    new_data = f.read()
                
                name = attachment.name or 'video'
                if not name.endswith('.mp4'):
                    if '.' in name:
                        name = name.rsplit('.', 1)[0] + '.mp4'
                    else:
                        name += '.mp4'

                attachment.sudo().write({
                    'datas': base64.b64encode(new_data),
                    'mimetype': 'video/mp4',
                    'name': name,
                })
                # Force the mimetype via SQL because Odoo's python-magic often incorrectly overrides it to video/quicktime
                self.env.cr.execute("UPDATE ir_attachment SET mimetype='video/mp4' WHERE id=%s", (attachment.id,))
                attachment.invalidate_recordset(['mimetype'])
                _logger.info(f"Successfully converted video attachment {attachment.id}")
            else:
                _logger.error(f"Video conversion failed: {result.stderr}")
                from odoo.exceptions import UserError
                raise UserError(f"Video compression failed. FFmpeg error: {result.stderr}")
            
            try:
                os.unlink(temp_in_name)
                if os.path.exists(temp_out_name):
                    os.unlink(temp_out_name)
            except OSError:
                pass
                
        except Exception as e:
            _logger.error("Exception during video compression: %s", e)

    def _compress_audio_attachment(self, attachment):
        import subprocess
        import tempfile
        import os
        import base64
        import shutil
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # ── Resolve ffmpeg path ─────────────────────────────────────────────────
            ffmpeg_exe = shutil.which('ffmpeg') or '/usr/bin/ffmpeg'
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                pass
            _logger.info("Audio compression: using ffmpeg at %s", ffmpeg_exe)

            # ── Write raw audio to a temp file ──────────────────────────────────────
            raw_data = base64.b64decode(attachment.datas)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_in:
                temp_in.write(raw_data)
                temp_in_path = temp_in.name

            temp_out_path = temp_in_path + '_out.ogg'
            mimetype = 'audio/ogg'
            ext = '.ogg'

            try:
                # ── Force AAC/m4a (Supported general audio format, bypasses strict Opus Voice Note rules) ──
                temp_out_m4a = temp_in_path + '_out.m4a'
                subprocess.run([
                    ffmpeg_exe, '-y', '-i', temp_in_path,
                    '-vn', '-c:a', 'aac', '-b:a', '64k',
                    temp_out_m4a
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                temp_out_path = temp_out_m4a
                mimetype = 'audio/mp4'
                ext = '.m4a'
                _logger.info("Audio compressed with aac successfully to avoid Opus rejection.")
                
                # ── Read the compressed file and update attachment ───────────────────
                with open(temp_out_path, 'rb') as f:
                    compressed_data = f.read()

                name = attachment.name or 'audio'
                if '.' in name:
                    name = name.rsplit('.', 1)[0] + ext
                else:
                    name += ext

                attachment.sudo().write({
                    'datas': base64.b64encode(compressed_data),
                    'mimetype': mimetype,
                    'name': name
                })
            except Exception as e:
                error_details = f"aac compression failed: {e}\nffmpeg: {ffmpeg_exe}"
                with open('/tmp/ffmpeg_error.log', 'w') as log_f:
                    log_f.write(error_details)
                raise Exception(error_details)
            finally:
                # ── Always clean up temp files ───────────────────────────────────────
                try:
                    if 'temp_in_path' in locals() and os.path.exists(temp_in_path):
                        os.unlink(temp_in_path)
                except Exception:
                    pass
                try:
                    if 'temp_out_path' in locals() and os.path.exists(temp_out_path):
                        os.unlink(temp_out_path)
                except Exception:
                    pass
        except Exception as e:
            _logger.error("Failed to compress audio attachment %s: %s", attachment.id, str(e))
            try:
                error_msg = str(e)
                self.env['mail.message'].create({
                    'body': '<p><b>Audio Processing Error:</b> %s</p>' % error_msg,
                    'message_type': 'comment',
                    'model': attachment.res_model,
                    'res_id': attachment.res_id,
                })
            except:
                pass
            raise UserError(f"Failed to process audio for WhatsApp: {str(e)}. Please check your ffmpeg installation.")

    @api.model
    def post_whatsapp_message(self, channel_id, **kwargs):
        """ Wrapper to allow standard users to post messages without discuss.channel record rules blocking them """
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if channel.exists():
                # Force attachment IDs to be integers to prevent ID type errors
                attachment_ids = [int(a) for a in kwargs.get('attachment_ids', []) if a]
                kwargs['attachment_ids'] = attachment_ids
                heavy_media_att_ids = []
            
                for att_id in attachment_ids:
                    att = self.env['ir.attachment'].sudo().browse(att_id)
                    if att.exists():
                        is_audio = att.mimetype and att.mimetype.startswith('audio/')
                        if att.mimetype == 'video/webm' and att.name and ('audio_message' in att.name or 'voice_' in att.name):
                            is_audio = True
                        
                        if is_audio or (att.mimetype and (att.mimetype.startswith('video/') or att.mimetype.startswith('image/'))):
                            heavy_media_att_ids.append(att.id)

                if 'author_id' not in kwargs:
                    kwargs['author_id'] = self.env.user.partner_id.id
            
                # Clean empty bodies to avoid 'text.body is required' API errors from Meta
                # But DO NOT set it to ' ' if there are attachments, otherwise Odoo splits it into 2 messages!
                body = kwargs.get('body', '')
                if not body or body == '<p><br></p>' or not str(body).strip():
                    # Only force a space if there are NO attachments (so it's a pure text message)
                    if not attachment_ids:
                        kwargs['body'] = ' '
                    else:
                        kwargs['body'] = ''
                
                import odoo
                msg_id = channel.with_user(odoo.SUPERUSER_ID).with_context(wa_web_chats_defer_send=True).message_post(**kwargs).id

                if heavy_media_att_ids:
                    dbname = self.env.cr.dbname
                    def background_process_media():
                        import threading
                        import odoo
                        def run_process():
                            try:
                                with odoo.registry(dbname).cursor() as new_cr:
                                    new_env = odoo.api.Environment(new_cr, odoo.SUPERUSER_ID, {})
                                    whatsapp_account = new_env['whatsapp.account']
                            
                                for att_id in heavy_media_att_ids:
                                    att = new_env['ir.attachment'].browse(att_id)
                                    if att.exists():
                                        is_audio = att.mimetype and att.mimetype.startswith('audio/')
                                        if att.mimetype == 'video/webm' and att.name and ('audio_message' in att.name or 'voice_' in att.name):
                                            is_audio = True
                                        if is_audio:
                                            whatsapp_account._compress_audio_attachment(att)
                                        elif att.mimetype and att.mimetype.startswith('video/'):
                                            whatsapp_account._compress_video_attachment(att)
                                        elif att.mimetype and att.mimetype.startswith('image/'):
                                            whatsapp_account._fix_image_attachment(att)
                            
                                wa_msgs = new_env['whatsapp.message'].search([
                                    ('mail_message_id', '=', msg_id),
                                    ('state', '=', 'outgoing')
                                ])
                                
                                # Fix Odoo core bug where it splits a message with attachment and body into multiple whatsapp.messages
                                if len(wa_msgs) > 1:
                                    _logger.info(f"Odoo split message {msg_id} into {len(wa_msgs)} whatsapp messages. Cancelling duplicates.")
                                    image_msg = wa_msgs.filtered(lambda w: w.attachment_id)
                                    text_msg = wa_msgs.filtered(lambda w: not w.attachment_id and w.body)
                                    if image_msg and text_msg:
                                        # Merge the body of the text message into the attachment message
                                        image_msg[0].write({'body': text_msg[0].body})
                                    wa_msgs[1:].write({'state': 'cancel'})
                                    wa_msgs = wa_msgs[0]

                                for wa_msg in wa_msgs:
                                    _logger.info(f"PRE-SEND WA MSG BACKGROUND {wa_msg.id}: type={wa_msg.message_type}, body='{wa_msg.body}'")
                                    try:
                                        wa_msg._send(force_send_by_cron=False)
                                    except Exception as send_err:
                                        _logger.warning("Could not send whatsapp message in background %s: %s", wa_msg.id, send_err)
                            except Exception as e:
                                _logger.error("Error in whatsapp background thread: %s", e)

                        thread = threading.Thread(target=run_process)
                        thread.start()

                    if hasattr(self.env.cr, 'postcommit'):
                        self.env.cr.postcommit.add(background_process_media)
                    elif hasattr(self.env.cr, 'after_commit'):
                        self.env.cr.after_commit(background_process_media)
                    else:
                        def delayed_run():
                            import time
                            time.sleep(1.5) # Wait for transaction to commit
                            background_process_media()
                        thread = threading.Thread(target=delayed_run)
                        thread.start()
                else:
                    # Immediately trigger sending of outbound WhatsApp messages so voice notes aren't delayed
                    wa_msgs = self.env['whatsapp.message'].sudo().search([
                        ('mail_message_id', '=', msg_id),
                        ('state', '=', 'outgoing')
                    ])
                    
                    if len(wa_msgs) > 1:
                        _logger.info(f"Odoo split message {msg_id} into {len(wa_msgs)} whatsapp messages. Cancelling duplicates.")
                        wa_msgs[1:].write({'state': 'cancel'})
                        wa_msgs = wa_msgs[0]
                        
                    for wa_msg in wa_msgs:
                        _logger.info(f"PRE-SEND WA MSG {wa_msg.id}: type={wa_msg.message_type}, body='{wa_msg.body}'")
                        try:
                            wa_msg._send(force_send_by_cron=False)
                        except Exception as send_err:
                            _logger.warning("Could not immediately send whatsapp message %s: %s", wa_msg.id, send_err)
                return msg_id
            return False

        except Exception as e:
            import logging
            logging.getLogger(__name__).error("post_whatsapp_message failed: %s", e, exc_info=True)
            raise
    @api.model
    def mark_whatsapp_web_messages_read(self, channel_id):
        channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
        if channel.exists() and channel.wa_is_unread_global:
            channel.write({'wa_is_unread_global': False})

        # Find the user's member record for this channel
        member = self.env['discuss.channel.member'].sudo().search([
            ('channel_id', '=', int(channel_id)),
            ('partner_id', '=', self.env.user.partner_id.id)
        ], limit=1)
        
        if member:
            # Find the last message in this channel
            last_message = self.env['mail.message'].sudo().search([
                ('res_id', '=', int(channel_id)),
                ('model', '=', 'discuss.channel'),
            ], order='id desc', limit=1)
            
            if last_message:
                # Mark as seen up to the last message, clearing the unread counter
                member._mark_as_read(last_message.id)
        
        return True

    @api.model
    def sync_device_contacts(self, contacts):
        """
        Receives a list of contacts from Flutter [{'name': '...', 'phone': '...'}].
        Creates res.partner records for those that don't exist by phone number.
        """
        Partner = self.env['res.partner'].sudo()
        results = []
        for contact in contacts:
            phone = contact.get('phone')
            name = contact.get('name')
            if not phone or not name:
                continue
                
            # Basic cleanup of phone number for searching
            clean_phone = ''.join([c for c in str(phone) if c.isdigit() or c == '+'])
            if not clean_phone:
                continue
                
            if not name:
                name = phone
                
            existing = Partner.search([
                ('phone', '=', phone)
            ], limit=1)
            
            if not existing:
                existing = Partner.search([
                    ('phone', 'ilike', clean_phone)
                ], limit=1)
            
            if existing:
                results.append({'id': existing.id, 'name': existing.name, 'phone': existing.phone, 'status': 'existing'})
            else:
                try:
                    new_partner = Partner.create({
                        'name': name,
                        'phone': phone,
                    })
                    results.append({'id': new_partner.id, 'name': new_partner.name, 'phone': new_partner.phone, 'status': 'created'})
                except Exception as e:
                    _logger.error(f"Failed to create partner {name}: {e}")
                    pass
                
        return {'success': True, 'contacts': results}

    @api.model
    def get_contacts_for_new_chat(self):
        """ Fetch all contacts that have a phone number to start a new chat with. """
        domain = [('phone', '!=', False)]
        contacts = self.env['res.partner'].sudo().search_read(
            domain, ['id', 'name', 'phone'], order='name asc'
        )
        import re
        for c in contacts:
            if c.get('name'):
                c['name'] = re.sub(r'\s*\(\s*School\s*\)', '', c['name'], flags=re.IGNORECASE).strip()
        return contacts

    @api.model
    def get_or_create_whatsapp_chat(self, partner_id, wa_account_id):
        """ Returns the existing whatsapp channel for a partner and account, or creates one. """
        partner = self.env['res.partner'].sudo().browse(int(partner_id))
        if not partner.exists():
            return {'success': False, 'error': 'Partner not found'}
            
        account = self.sudo().browse(int(wa_account_id))
        if not account.exists():
            return {'success': False, 'error': 'Account not found'}
            
        phone = partner.phone
        clean_phone = ''.join([c for c in str(phone) if c.isdigit()]) if phone else ''
        if clean_phone.startswith('0') and len(clean_phone) == 10:
            clean_phone = '263' + clean_phone[1:]
        
        domain = [
            ('channel_type', '=', 'whatsapp'),
            ('wa_account_id', '=', account.id),
            '|',
            ('whatsapp_partner_id', '=', partner.id),
            ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone])
        ]
        
        # If partner has no phone, we can only search by partner_id
        if not clean_phone:
            domain = [
                ('channel_type', '=', 'whatsapp'),
                ('whatsapp_partner_id', '=', partner.id),
                ('wa_account_id', '=', account.id)
            ]
            
        channel = self.env['discuss.channel'].sudo().search(domain, limit=1)
        
        if channel:
            # If we found it by number but it has no partner, link it now!
            if not channel.whatsapp_partner_id:
                channel.sudo().write({'whatsapp_partner_id': partner.id})
                
            # Ensure the current user is a member
            if not self.env.user.partner_id.id in channel.channel_member_ids.mapped('partner_id').ids:
                self.env['discuss.channel.member'].sudo().create({
                    'channel_id': channel.id,
                    'partner_id': self.env.user.partner_id.id
                })
            return {'success': True, 'channel_id': channel.id}
            
        # Create new channel
        members = [(0, 0, {'partner_id': self.env.user.partner_id.id})]
        if partner.id != self.env.user.partner_id.id:
            members.append((0, 0, {'partner_id': partner.id}))
            
        new_channel = self.env['discuss.channel'].sudo().create({
            'name': partner.name,
            'channel_type': 'whatsapp',
            'whatsapp_partner_id': partner.id,
            'whatsapp_number': '+' + clean_phone if clean_phone else '',
            'wa_account_id': account.id,
            'company_id': account.company_id.id if account.company_id else False,
            'channel_member_ids': members
        })
        
        return {'success': True, 'channel_id': new_channel.id}

    @api.model
    def create_chat_from_number(self, number, wa_account_id=False):
        if wa_account_id:
            try:
                account = self.sudo().browse(int(wa_account_id))
            except (ValueError, TypeError):
                account = self.sudo().search([], limit=1)
        else:
            account = self.sudo().search([], limit=1)
            
        if not account or not account.exists():
            return {'success': False, 'error': 'Account not found'}
            
        clean_phone = ''.join([c for c in str(number) if c.isdigit()])
        if clean_phone.startswith('0') and len(clean_phone) == 10:
            clean_phone = '263' + clean_phone[1:]
        number = '+' + clean_phone if clean_phone else ''
            
        if not clean_phone:
            return {'success': False, 'error': 'Invalid number'}
            
        # First check if a channel with this whatsapp_number already exists!
        # This prevents unique constraint violations if the partner phone is formatted differently.
        existing_channel = self.env['discuss.channel'].sudo().search([
            ('channel_type', '=', 'whatsapp'),
            ('whatsapp_number', 'in', [clean_phone, '+' + clean_phone]),
            ('wa_account_id', '=', account.id)
        ], limit=1)
        
        if existing_channel:
            return {'success': True, 'channel_id': existing_channel.id}
            
        partner = self.env['res.partner'].sudo().search([
            ('phone', '=', number)
        ], limit=1)
        
        if not partner:
            partner = self.env['res.partner'].sudo().search([
                ('phone', 'ilike', clean_phone)
            ], limit=1)
        
        if not partner:
            try:
                partner = self.env['res.partner'].sudo().create({
                    'name': number,
                    'phone': number,
                })
            except Exception as e:
                return {'success': False, 'error': f"Failed to create contact: {e}"}
            
        try:
            return self.get_or_create_whatsapp_chat(partner.id, wa_account_id)
        except Exception as e:
            return {'success': False, 'error': f"Failed to create chat: {e}"}

    @api.model
    def update_contact_name(self, channel_id, new_name, new_number=False):
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if not channel.exists():
                return {'success': False, 'error': 'Channel not found'}
                
            channel.name = new_name
            if new_number:
                channel.whatsapp_number = new_number
                
            if channel.whatsapp_partner_id:
                channel.whatsapp_partner_id.name = new_name
                if new_number:
                    channel.whatsapp_partner_id.mobile = new_number
                    channel.whatsapp_partner_id.phone = new_number
                
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def send_whatsapp_template(self, channel_id, template_id):
        try:
            channel = self.env['discuss.channel'].sudo().browse(int(channel_id))
            if not channel.exists():
                return {'success': False, 'error': 'Channel not found'}

            template = self.env['whatsapp.template'].sudo().browse(int(template_id))
            if not template.exists():
                return {'success': False, 'error': 'Template not found'}

            if template.status != 'approved':
                return {'success': False, 'error': f'Template is not approved (status: {template.status})'}

            partner = channel.whatsapp_partner_id
            phone = channel.whatsapp_number or (partner.phone if partner else False)

            if not partner and phone:
                partner = self.env['res.partner'].sudo().search([('phone', 'ilike', phone)], limit=1)
                if not partner:
                    partner = self.env['res.partner'].sudo().create({
                        'name': phone,
                        'phone': phone,
                    })
                channel.sudo().write({'whatsapp_partner_id': partner.id})

            if not partner:
                return {'success': False, 'error': 'Channel has no partner attached and no phone number to create one'}

            if not phone:
                return {'success': False, 'error': 'No phone number found for contact'}

            # Force international E.164 format (with '+') so Odoo's core whatsapp module doesn't fail on country fallback
            clean_phone = ''.join(filter(str.isdigit, phone))
            if clean_phone:
                phone = '+' + clean_phone
            else:
                return {'success': False, 'error': 'Phone number is invalid (no digits found)'}

            wa_account = channel.wa_account_id
            if not wa_account:
                wa_account = self.sudo().search([], limit=1)
            if not wa_account:
                return {'success': False, 'error': 'No WhatsApp account found'}

            # Build free_text_json to fill {{1}}, {{2}}... placeholders in the template body.
            # All templates have `field_type=free_text` variables — we default to the contact name.
            free_text_json = {}
            def get_var_index(v):
                try:
                    return v._extract_variable_index() or 0
                except AttributeError:
                    import re
                    match = re.search(r'\d+', v.name or '')
                    return int(match.group()) if match else 0

            free_text_vars = template.variable_ids.filtered(
                lambda v: v.line_type == 'body' and v.field_type == 'free_text'
            ).sorted(lambda v: get_var_index(v))
            contact_name = partner.name or ''
            for i, var in enumerate(free_text_vars, start=1):
                free_text_json[f'free_text_{i}'] = contact_name

            # Build the rendered template body to display in the chat
            import re as _re
            rendered_body = template.body or ''
            for i, var in enumerate(free_text_vars, start=1):
                rendered_body = _re.sub(r'\{\{' + str(i) + r'\}\}', contact_name, rendered_body)

            # Post the mail.message on res.partner — required by Odoo so that
            # mail_message_id.model matches the template's model field ('res.partner').
            mail_msg = partner.sudo().message_post(
                body=rendered_body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.user.partner_id.id,
            )

            # Record the highest channel message ID BEFORE _send so we can detect
            # any new message _send() auto-creates in the discuss.channel.
            existing_channel_msg = self.env['mail.message'].sudo().search(
                [('model', '=', 'discuss.channel'), ('res_id', '=', channel.id)],
                order='id desc', limit=1
            )
            last_channel_id_before = existing_channel_msg.id if existing_channel_msg else 0

            # Create the whatsapp.message that drives the actual Meta API call
            wa_msg = self.env['whatsapp.message'].sudo().create({
                'mobile_number': phone,
                'wa_template_id': template.id,
                'wa_account_id': wa_account.id,
                'mail_message_id': mail_msg.id,
                'state': 'outgoing',
                'message_type': 'outbound',
                'free_text_json': free_text_json,
            })

            # Send immediately (foreground)
            try:
                wa_msg._send(force_send_by_cron=False)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("Failed to send template immediately: %s", e)

            # After _send, look for a new discuss.channel message that _send created.
            # Odoo's core _send() posts to the channel as a side-effect.
            # If we return that channel msg ID (instead of the res.partner one),
            # the poller's query will find ONE message (same record) — no duplicate.
            new_channel_msgs = self.env['mail.message'].sudo().search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel.id),
                ('id', '>', last_channel_id_before),
            ], order='id asc', limit=5)

            final_msg = mail_msg  # fallback: res.partner message
            if new_channel_msgs:
                # Point wa_msg at the channel message so get_whatsapp_web_messages
                # returns it via wa_mail_ids — and no longer returns the res.partner orphan
                final_msg = new_channel_msgs[0]
                wa_msg.sudo().write({'mail_message_id': final_msg.id})

            sent_date = final_msg.date.strftime('%Y-%m-%d %H:%M:%S') if final_msg.date else False

            # Queue first auto follow-up rule if configured
            first_rule = wa_account.followup_rule_ids.sorted('sequence')
            if first_rule:
                first_rule = first_rule[0]
                self.env['whatsapp.scheduled.message'].sudo().create({
                    'channel_id': channel.id,
                    'scheduled_at': first_rule.get_scheduled_datetime(fields.Datetime.now()),
                    'message_type': 'template',
                    'template_id': first_rule.template_id.id,
                    'is_auto_followup': True,
                    'current_rule_id': first_rule.id,
                    'state': 'pending',
                })

            return {'success': True, 'body': rendered_body, 'sent_date': sent_date, 'msg_id': final_msg.id}
        except Exception as e:
            _logger.exception("Error in send_whatsapp_template")
            return {'success': False, 'error': str(e)}

    @api.model
    def get_profile_settings(self, account_id):
        account = self.sudo().browse(int(account_id))
        if account.exists():
            return {
                'name': account.name,
                'phone_uid': account.phone_uid if hasattr(account, 'phone_uid') else '',
                'phone': account.phone_number if hasattr(account, 'phone_number') and account.phone_number and account.phone_number.lower() != 'api' else (account.name if account.name and any(c.isdigit() for c in account.name) else (account.phone_uid if hasattr(account, 'phone_uid') else '')),
                'image_1920': account.image_1920 if hasattr(account, 'image_1920') else False,
            }
        return {}

    def _send_group_auto_message(self, channel):
        """Sends the group auto message to a single discuss.channel — EXACTLY ONCE.

        Uses an atomic SQL UPDATE to claim the 'right to send' before any API call,
        so even if two worker processes race on the same channel simultaneously,
        only one will actually deliver the message.
        """
        self.ensure_one()
        if not self.wa_group_auto_message_share or not self.phone_uid or not self.token:
            return False

        if not channel or channel.channel_type != 'whatsapp':
            return False

        # ── Atomic claim: only the first caller wins ──────────────────────────────
        # UPDATE ... WHERE wa_group_invite_sent = FALSE returns the number of rows
        # updated. If 0, another process already claimed it — bail out immediately.
        self.env.cr.execute(
            "UPDATE discuss_channel "
            "SET wa_group_invite_sent = TRUE "
            "WHERE id = %s AND wa_group_invite_sent = FALSE",
            (channel.id,)
        )
        if self.env.cr.rowcount == 0:
            # Already sent (or being sent right now by another process)
            return False
        # Invalidate ORM cache so subsequent reads see the committed value
        channel.invalidate_recordset(['wa_group_invite_sent'])

        text = (self.wa_group_auto_message_text or '').strip()
        link = (self.wa_group_auto_message_link or '').strip()
        if not text and not link:
            return False
        full_text = f"{text} {link}".strip() if (text and link) else (text or link)

        phone = channel.whatsapp_number or (channel.whatsapp_partner_id and channel.whatsapp_partner_id.phone)
        import re
        clean_phone = re.sub(r'\D', '', str(phone or ''))
        if not clean_phone:
            return False

        import requests
        url = f"https://graph.facebook.com/v19.0/{self.phone_uid}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": full_text
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            resp_data = resp.json()
            if 'messages' in resp_data:
                msg_uid = resp_data['messages'][0]['id']
                from odoo.tools import plaintext2html
                mail_msg = channel.sudo().with_context(skip_auto_invite=True).message_post(
                    body=plaintext2html(full_text),
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=self.env.ref('base.partner_admin').id
                )
                self.env['whatsapp.message'].sudo().create({
                    'mail_message_id': mail_msg.id,
                    'message_type': 'outbound',
                    'mobile_number': f'+{clean_phone}',
                    'wa_account_id': self.id,
                    'msg_uid': msg_uid,
                    'state': 'sent',
                    'body': full_text
                })
                _logger.info("Group auto message sent to channel %s (phone: %s)", channel.id, clean_phone)
                return True
            else:
                _logger.error("Meta API error sending group auto message to %s: %s", clean_phone, resp_data)
                return False
        except Exception as e:
            _logger.error("Exception sending group auto message to channel %s: %s", channel.id, str(e))
            return False

    def action_send_group_auto_message_to_all(self):
        """Sends group auto message ONLY to contacts we have already spoken to
        (i.e. channels with at least one existing message) that have not yet
        received the invite.  Never sends to brand-new / empty channels."""
        self.ensure_one()
        if not self.wa_group_auto_message_share:
            from odoo.exceptions import UserError
            raise UserError("Please enable WhatsApp Group Auto Message Share first.")

        text = (self.wa_group_auto_message_text or '').strip()
        link = (self.wa_group_auto_message_link or '').strip()
        if not text and not link:
            from odoo.exceptions import UserError
            raise UserError("Please configure the Auto Message Text and/or Link before sending.")

        # Pending channels for this account that haven't received the invite yet
        pending_channels = self.env['discuss.channel'].sudo().search([
            ('channel_type', '=', 'whatsapp'),
            ('wa_account_id', '=', self.id),
            ('wa_group_invite_sent', '=', False)
        ])

        count = 0
        import time
        for channel in pending_channels:
            if self._send_group_auto_message(channel):
                count += 1
                time.sleep(0.1)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Group Auto Message Sent',
                'message': f'Sent group invite to {count} out of {len(pending_channels)} existing conversations that had not yet received it.',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def _cron_send_group_auto_messages(self):
        """ Cron job to find pending channels in the database and send group auto messages """
        accounts = self.search([('wa_group_auto_message_share', '=', True)])
        import time
        for acc in accounts:
            pending_channels = self.env['discuss.channel'].sudo().search([
                ('channel_type', '=', 'whatsapp'),
                ('wa_account_id', '=', acc.id),
                ('wa_group_invite_sent', '=', False)
            ], limit=50)
            for ch in pending_channels:
                acc._send_group_auto_message(ch)
                time.sleep(0.1)

 
