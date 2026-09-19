from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SendSchoolBalancesWizard(models.TransientModel):
    _name = 'send.school.balances.wizard'
    _description = 'Send School Balances Wizard'

    whatsapp_account_id = fields.Many2one('whatsapp.account', string="WhatsApp Account", required=True)
    integration_type = fields.Selection(related='whatsapp_account_id.school_integration_type', string="Integration Type")
    
    target_audience = fields.Selection([
        ('school', 'Whole School'),
        ('class', 'Specific Class'),
        ('section', 'Specific Section'),
        ('student', 'Specific Student')
    ], string="Send To", required=True, default='school')

    document_type = fields.Selection([
        ('statement', 'Student Statement'),
        ('billing', 'Billing (Invoice)'),
        ('receipt', 'Receipt (Payment)')
    ], string="Document to Send", required=True, default='statement')

    filter_date = fields.Date(string="Date Filter (Generated On)", default=fields.Date.context_today)

    # Search fields for both Local and Remote DB
    class_name = fields.Char(string="Class Name (Exact Match)")
    section_name = fields.Char(string="Section Name (Exact Match)")
    student_name = fields.Char(string="Student Name (Exact Match)")

    def action_send_balances(self):
        self.ensure_one()
        account = self.whatsapp_account_id
        if not account.allow_school_balances:
            raise UserError("School balances are not enabled for this WhatsApp account.")

        if account.school_integration_type == 'local':
            return self._send_local()
        else:
            return self._send_remote()
            
    def _check_duplicate(self, student_name, trigger_type, date_obj):
        # Checks if we already sent this exact document type to this student today
        start_of_day = fields.Datetime.to_datetime(date_obj)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        existing = self.env['whatsapp.school.balance.log'].search([
            ('whatsapp_account_id', '=', self.whatsapp_account_id.id),
            ('student_name', '=', student_name),
            ('trigger_type', '=', trigger_type),
            ('status', '=', 'sent'),
            ('create_date', '>=', start_of_day),
            ('create_date', '<=', end_of_day)
        ], limit=1)
        return bool(existing)

    def _send_local(self):
        account = self.whatsapp_account_id
        if 'havano.student' not in self.env:
            raise UserError("havano_schools_odoo is not installed on this database.")
            
        domain = []
        if self.document_type == 'statement':
            # Find all students with open invoices
            domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('amount_residual', '>', 0)]
        elif self.document_type == 'billing':
            # Find invoices generated on the filter_date
            domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '=', self.filter_date)]
        elif self.document_type == 'receipt':
            # Find payments generated on the filter_date
            domain = [('date', '=', self.filter_date), ('state', '=', 'posted')]

        # Apply audience filters by finding matching students and their partner_ids
        student_domain = []
        if self.target_audience == 'class' and self.class_name:
            student_domain.append(('havano_class_id.name', 'ilike', self.class_name))
        elif self.target_audience == 'section' and self.section_name:
            student_domain.append(('havano_section_id.name', 'ilike', self.section_name))
        elif self.target_audience == 'student' and self.student_name:
            student_domain.append(('name', 'ilike', self.student_name))
            
        if student_domain:
            students = self.env['havano.student'].search(student_domain)
            if not students:
                raise UserError("No students found matching the selected criteria.")
            partner_ids = students.mapped('partner_id').ids
            if not partner_ids:
                raise UserError("Found students, but they have no linked partner records.")
            domain.append(('partner_id', 'in', partner_ids))

        if self.document_type in ['statement', 'billing']:
            records = self.env['account.move'].search(domain, order='id desc')
        else:
            records = self.env['account.payment'].search(domain, order='id desc')

        if not records:
            raise UserError(f"No records found for the selected criteria ({self.document_type}).")

        template = account.school_balance_template or "Dear {parent_name}, please find attached the {doc_type} for {student_name} at {school}. Balance: {balance}."
        school_name = account.company_id.name or 'Our School'

        success_count = 0
        fail_count = 0


        import datetime
        today_date = datetime.date.today()

        for record in records:
            # record could be account.move or account.payment
            partner = record.partner_id
            if not partner:
                continue

            student = self.env['havano.student'].search([('partner_id', '=', partner.id)], limit=1)
            if not student:
                continue

            parent = self.env['havano.parent'].search([('student_ids', '=', student.id)], limit=1)
            parent_name = parent.name if parent else 'Unknown'
            
            parent_phone = False
            if parent:
                try:
                    parent_phone = parent.mobile or parent.phone or parent.partner_id.mobile or parent.partner_id.phone
                except AttributeError:
                    parent_phone = parent.phone or getattr(parent.partner_id, 'mobile', False) or parent.partner_id.phone
                    
            if not parent_phone:
                parent_phone = getattr(student, 'parent_phone', False) or getattr(student, 'guardian_1_phone', False)
                if getattr(student, 'parent_name', False):
                    parent_name = student.parent_name
                elif getattr(student, 'guardian_1_name', False):
                    parent_name = student.guardian_1_name

            if not parent_phone:
                fail_count += 1
                account._create_balance_log(student.name, parent_name, False, record.amount_residual if hasattr(record, 'amount_residual') else record.amount, record.id, self.document_type, 'failed', 'No parent found or missing phone.')
                continue

            # Check for duplicate dispatch today
            if self._check_duplicate(student.name, self.document_type, today_date):
                # We already sent this document type to this student today
                account._create_balance_log(student.name, parent.name, parent_phone, record.amount_residual if hasattr(record, 'amount_residual') else record.amount, record.id, self.document_type, 'failed', 'Skipped: Duplicate sent today.')
                continue

            try:
                phone = parent_phone.replace(' ', '').replace('+', '')
                attachment = False
                
                # Document PDF Generation
                try:
                    import base64
                    if self.document_type == 'statement':
                        from dateutil.relativedelta import relativedelta
                        start_date = today_date.replace(day=1) - relativedelta(months=1)
                        wizard = self.env['customer.statement.wizard'].create({
                            'partner_id': parent.partner_id.id if hasattr(parent, 'partner_id') and parent.partner_id else parent.id,
                            'start_date': start_date,
                            'end_date': today_date
                        })
                        report = self.env.ref('havano_schools_odoo.statement_receipt')
                        pdf_content, _ = report._render_qweb_pdf(wizard.id)
                        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                        attach_name = f"Statement_{student.name}_{today_date}.pdf"
                    
                    elif self.document_type == 'billing':
                        report = self.env.ref('account.account_invoices')
                        pdf_content, _ = report._render_qweb_pdf(record.id)
                        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                        attach_name = f"Invoice_{student.name}_{record.name.replace('/', '_')}.pdf"
                        
                    elif self.document_type == 'receipt':
                        report = self.env.ref('account.action_report_payment_receipt')
                        pdf_content, _ = report._render_qweb_pdf(record.id)
                        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                        attach_name = f"Receipt_{student.name}_{record.name.replace('/', '_')}.pdf"

                    attachment = self.env['ir.attachment'].create({
                        'name': attach_name,
                        'type': 'binary',
                        'datas': pdf_base64,
                        'res_model': 'whatsapp.message',
                        'mimetype': 'application/pdf'
                    })
                except Exception as e:
                    _logger.error(f"Failed to generate PDF for {student.name}: {e}")
                    attachment = False

                balance_val = record.amount_residual if hasattr(record, 'amount_residual') else record.amount
                message = template.format(
                    parent_name=parent.name,
                    student_name=student.name,
                    school=school_name,
                    balance=balance_val,
                    doc_type=dict(self._fields['document_type'].selection).get(self.document_type)
                )
                
                msg_vals = {
                    'wa_account_id': account.id,
                    'mobile_number': phone,
                    'body': message,
                    'state': 'outgoing',
                    'message_type': 'outbound'
                }
                if attachment:
                    msg_vals['attachment_id'] = attachment.id
                    
                wa_msg = self.env['whatsapp.message'].create(msg_vals)
                wa_msg._send(force_send_by_cron=False)
                
                if wa_msg.state == 'error':
                    error_msg = getattr(wa_msg, 'failure_reason', 'Failed to send (Meta API rejection)')
                    account._create_balance_log(student.name, parent.name, parent_phone, balance_val, record.id, self.document_type, 'failed', str(error_msg))
                    fail_count += 1
                else:
                    account._create_balance_log(student.name, parent.name, parent_phone, balance_val, record.id, self.document_type, 'sent', '')
                    success_count += 1
            except Exception as e:
                account._create_balance_log(student.name, parent.name, parent_phone, record.amount_residual if hasattr(record, 'amount_residual') else record.amount, record.id, self.document_type, 'failed', str(e))
                fail_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Manual Sync Complete',
                'message': f'Successfully sent {success_count} messages. Failed: {fail_count}. Check logs for details.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _send_remote(self):
        account = self.whatsapp_account_id
        import xmlrpc.client
        if not all([account.school_app_url, account.school_db_name, account.school_username, account.school_password]):
            raise UserError("Remote sync failed: Missing credentials.")

        url = account.school_app_url.rstrip('/')
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        try:
            uid = common.authenticate(account.school_db_name, account.school_username, account.school_password, {})
            if not uid:
                raise UserError("Authentication failed for remote school app.")
        except Exception as e:
            raise UserError(f"Failed to connect to remote school app: {e}")

        models_proxy = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        domain = []
        if self.document_type == 'statement':
            domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('amount_residual', '>', 0)]
        elif self.document_type == 'billing':
            domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_date', '=', self.filter_date)]
        elif self.document_type == 'receipt':
            domain = [('date', '=', self.filter_date), ('state', '=', 'posted')]
        
        # To apply filters remotely, we need to first find the matching students
        student_domain = []
        if self.target_audience == 'class' and self.class_name:
            student_domain.append(('havano_class_id.name', 'ilike', self.class_name))
        elif self.target_audience == 'section' and self.section_name:
            student_domain.append(('havano_section_id.name', 'ilike', self.section_name))
        elif self.target_audience == 'student' and self.student_name:
            student_domain.append(('name', 'ilike', self.student_name))
            
        if student_domain:
            student_ids = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.student', 'search', [student_domain])
            if not student_ids:
                raise UserError("No students found matching the criteria in the remote database.")
            students = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.student', 'read', [student_ids], {'fields': ['partner_id']})
            partner_ids = [s['partner_id'][0] for s in students if s.get('partner_id')]
            if not partner_ids:
                raise UserError("Found students in remote database, but they have no linked partner records.")
            domain.append(('partner_id', 'in', partner_ids))

        target_model = 'account.move' if self.document_type in ['statement', 'billing'] else 'account.payment'
        record_ids = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, target_model, 'search', [domain], {'order': 'id desc'})
        if not record_ids:
            raise UserError(f"No records found for the selected criteria ({self.document_type}).")

        read_fields = ['partner_id', 'amount_residual', 'name'] if self.document_type in ['statement', 'billing'] else ['partner_id', 'amount', 'name']
        records = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, target_model, 'read', [record_ids], {'fields': read_fields})
        
        template = account.school_balance_template or "Dear {parent_name}, please find attached the {doc_type} for {student_name} at {school}. Balance: {balance}."
        school_name = account.company_id.name or 'Our School'

        success_count = 0
        fail_count = 0
        
        import datetime
        today_date = datetime.date.today()

        for record in records:
            balance_val = record.get('amount_residual', 0) if self.document_type in ['statement', 'billing'] else record.get('amount', 0)
            if self.document_type == 'statement' and balance_val <= 0:
                continue

            partner_id = record['partner_id'][0] if record.get('partner_id') else False
            if not partner_id:
                continue

            # Find student
            student_ids = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.student', 'search', [[('partner_id', '=', partner_id)]], {'limit': 1})
            if not student_ids:
                continue
                
            student = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.student', 'read', [student_ids], {'fields': ['name']})
            student_name = student[0]['name']
            student_id = student_ids  # for parent search compat
            
            # Find parent
            parent_name = 'Unknown'
            parent_phone = False
            
            parent_ids = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.parent', 'search', [[('student_ids', '=', student_id[0])]], {'limit': 1})
            
            if parent_ids:
                parents = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.parent', 'read', [parent_ids], {'fields': ['name', 'mobile', 'phone', 'partner_id']})
                if parents:
                    parent = parents[0]
                    parent_name = parent.get('name', 'Unknown')
                    parent_phone = parent.get('mobile') or parent.get('phone')
                    if not parent_phone and parent.get('partner_id'):
                        parent_partners = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'res.partner', 'read', [[parent['partner_id'][0]]], {'fields': ['mobile', 'phone']})
                        if parent_partners:
                            parent_phone = parent_partners[0].get('mobile') or parent_partners[0].get('phone')

            if not parent_phone:
                # Fallback to student fields
                students = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.student', 'read', [student_id], {'fields': ['parent_name', 'guardian_1_name', 'parent_phone', 'guardian_1_phone']})
                if students:
                    stud = students[0]
                    parent_phone = stud.get('parent_phone') or stud.get('guardian_1_phone')
                    if stud.get('parent_name'):
                        parent_name = stud['parent_name']
                    elif stud.get('guardian_1_name'):
                        parent_name = stud['guardian_1_name']

            if not parent_phone:
                fail_count += 1
                account._create_balance_log(student_name, parent_name, False, balance_val, record['id'], self.document_type, 'failed', 'No parent found or missing phone.')
                continue

            # Check deduplication locally
            if self._check_duplicate(student_name, self.document_type, today_date):
                account._create_balance_log(student_name, parent_name, parent_phone, balance_val, record['id'], self.document_type, 'failed', 'Skipped: Duplicate sent today.')
                continue

            try:
                phone = parent_phone.replace(' ', '').replace('+', '')
                
                # Fetch PDF from Remote DB
                attachment = False
                try:
                    import base64
                    pdf_base64 = False
                    if self.document_type == 'statement':
                        report_proxy = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/report')
                        pdf_content, _ = report_proxy.render_qweb_pdf(account.school_db_name, uid, account.school_password, 'havano_schools_odoo.statement_receipt', [record['id']])
                        if pdf_content:
                            pdf_base64 = base64.b64encode(pdf_content.data).decode('utf-8')
                        attach_name = f"Statement_{student_name}_{today_date}.pdf"
                    
                    elif self.document_type == 'billing':
                        report_proxy = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/report')
                        pdf_content, _ = report_proxy.render_qweb_pdf(account.school_db_name, uid, account.school_password, 'account.account_invoices', [record['id']])
                        if pdf_content:
                            pdf_base64 = base64.b64encode(pdf_content.data).decode('utf-8')
                        attach_name = f"Invoice_{student_name}_{record.get('name', '').replace('/', '_')}.pdf"
                        
                    elif self.document_type == 'receipt':
                        report_proxy = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/report')
                        pdf_content, _ = report_proxy.render_qweb_pdf(account.school_db_name, uid, account.school_password, 'account.action_report_payment_receipt', [record['id']])
                        if pdf_content:
                            pdf_base64 = base64.b64encode(pdf_content.data).decode('utf-8')
                        attach_name = f"Receipt_{student_name}_{record.get('name', '').replace('/', '_')}.pdf"

                    if pdf_base64:
                        attachment = self.env['ir.attachment'].create({
                            'name': attach_name,
                            'type': 'binary',
                            'datas': pdf_base64,
                            'res_model': 'whatsapp.message',
                            'mimetype': 'application/pdf'
                        })
                except Exception as e:
                    _logger.error(f"Failed to fetch PDF remotely for {student_name}: {e}")
                    attachment = False

                message = template.format(
                    parent_name=parent_name,
                    student_name=student_name,
                    school=school_name,
                    balance=balance_val,
                    doc_type=dict(self._fields['document_type'].selection).get(self.document_type)
                )
                
                msg_vals = {
                    'wa_account_id': account.id,
                    'mobile_number': phone,
                    'body': message,
                    'state': 'outgoing',
                    'message_type': 'outbound'
                }
                if attachment:
                    msg_vals['attachment_id'] = attachment.id
                    
                wa_msg = self.env['whatsapp.message'].create(msg_vals)
                wa_msg._send(force_send_by_cron=False)
                
                if wa_msg.state == 'error':
                    error_msg = getattr(wa_msg, 'failure_reason', 'Failed to send (Meta API rejection)')
                    account._create_balance_log(student_name, parent_name, parent_phone, balance_val, record['id'], self.document_type, 'failed', str(error_msg))
                    fail_count += 1
                else:
                    account._create_balance_log(student_name, parent_name, parent_phone, balance_val, record['id'], self.document_type, 'sent', '')
                    success_count += 1
            except Exception as e:
                account._create_balance_log(student_name, parent_name, parent_phone, balance_val, record['id'], self.document_type, 'failed', str(e))
                fail_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Manual Sync Complete',
                'message': f'Successfully sent {success_count} messages. Failed: {fail_count}. Check logs for details.',
                'type': 'success',
                'sticky': False,
            }
        }
