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
            
    def _send_local(self):
        account = self.whatsapp_account_id
        if 'havano.student' not in self.env:
            raise UserError("havano_schools_odoo is not installed on this database.")
            
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('amount_residual', '>', 0)
        ]
        
        # Apply filters
        if self.target_audience == 'class':
            if self.class_name:
                domain.append(('havano_student_id.havano_class_id.name', 'ilike', self.class_name))
        elif self.target_audience == 'section':
            if self.section_name:
                domain.append(('havano_student_id.havano_section_id.name', 'ilike', self.section_name))
        elif self.target_audience == 'student':
            if self.student_name:
                domain.append(('havano_student_id.name', 'ilike', self.student_name))

        moves = self.env['account.move'].search(domain, order='id desc')
        if not moves:
            raise UserError("No outstanding balances found for the selected criteria.")

        template = account.school_balance_template or "Dear {parent_name}, the outstanding balance for {student_name} at {school} is {balance}."
        school_name = account.company_id.name or 'Our School'

        success_count = 0
        fail_count = 0

        for move in moves:
            student = move.havano_student_id
            if not student:
                continue

            parent = self.env['havano.parent'].search([('student_ids', 'in', student.id)], limit=1)
            if not parent:
                fail_count += 1
                account._create_balance_log(student.name, 'Unknown', False, move.amount_residual, move.id, 'manual', 'failed', 'No parent found.')
                continue

            try:
                parent_phone = parent.mobile or parent.phone or parent.partner_id.mobile or parent.partner_id.phone
            except AttributeError:
                parent_phone = parent.phone or getattr(parent.partner_id, 'mobile', False) or parent.partner_id.phone
                
            if not parent_phone:
                fail_count += 1
                account._create_balance_log(student.name, parent.name, False, move.amount_residual, move.id, 'manual', 'failed', 'Parent has no phone number.')
                continue

            try:
                phone = parent_phone.replace(' ', '').replace('+', '')
                
                # PDF Generation
                attachment = False
                try:
                    import base64
                    from datetime import date
                    from dateutil.relativedelta import relativedelta
                    
                    start_date = date.today().replace(day=1) - relativedelta(months=1)
                    end_date = date.today()
                    
                    wizard = self.env['customer.statement.wizard'].create({
                        'partner_id': parent.partner_id.id if hasattr(parent, 'partner_id') and parent.partner_id else parent.id,
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

                message = template.format(
                    parent_name=parent.name,
                    student_name=student.name,
                    school=school_name,
                    balance=move.amount_residual
                )
                
                msg_vals = {
                    'wa_account_id': account.id,
                    'mobile_number': phone,
                    'body': message,
                    'state': 'sent'
                }
                if attachment:
                    msg_vals['attachment_id'] = attachment.id
                    
                self.env['whatsapp.message'].create(msg_vals)
                account._create_balance_log(student.name, parent.name, parent_phone, move.amount_residual, move.id, 'manual', 'sent', '')
                success_count += 1
            except Exception as e:
                account._create_balance_log(student.name, parent.name, parent_phone, move.amount_residual, move.id, 'manual', 'failed', str(e))
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
        
        domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]
        
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
            domain.append(('havano_student_id', 'in', student_ids))

        move_ids = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'account.move', 'search', [domain], {'order': 'id desc'})
        if not move_ids:
            raise UserError("No outstanding balances found for the selected criteria.")

        moves = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'account.move', 'read', [move_ids], {'fields': ['partner_id', 'amount_residual', 'havano_student_id']})
        
        template = account.school_balance_template or "Dear {parent_name}, the outstanding balance for {student_name} at {school} is {balance}."
        school_name = account.company_id.name or 'Our School'

        success_count = 0
        fail_count = 0

        for move in moves:
            if move.get('amount_residual', 0) <= 0:
                continue

            partner_id = move['partner_id'][0] if move.get('partner_id') else False
            if not partner_id:
                continue

            # Find student
            student_id = move.get('havano_student_id')
            if not student_id:
                continue
                
            student_name = student_id[1]
            
            # Find parent
            parent_ids = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.parent', 'search', [[('student_ids', 'in', student_id[0])]], {'limit': 1})
            if not parent_ids:
                fail_count += 1
                account._create_balance_log(student_name, 'Unknown', False, move['amount_residual'], move['id'], 'manual', 'failed', 'No parent found.')
                continue
                
            parents = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'havano.parent', 'read', [parent_ids], {'fields': ['name', 'phone', 'partner_id']})
            parent = parents[0] if parents else None
            if not parent:
                continue
            parent_phone = parent.get('phone')
            
            if not parent_phone:
                fail_count += 1
                account._create_balance_log(student_name, parent['name'], False, move['amount_residual'], move['id'], 'manual', 'failed', 'Parent has no phone number.')
                continue

            try:
                phone = parent_phone.replace(' ', '').replace('+', '')
                
                # Generate PDF Remotely
                attachment = False
                try:
                    import base64
                    from datetime import date
                    from dateutil.relativedelta import relativedelta
                    
                    start_date = date.today().replace(day=1) - relativedelta(months=1)
                    end_date = date.today()
                    
                    parent_partner_id = parent.get('partner_id', [False])[0] or False
                    if parent_partner_id:
                        wizard_id = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'customer.statement.wizard', 'create', [{
                            'partner_id': parent_partner_id,
                            'start_date': str(start_date),
                            'end_date': str(end_date)
                        }])
                        
                        pdf_content = models_proxy.execute_kw(account.school_db_name, uid, account.school_password, 'ir.actions.report', '_render_qweb_pdf', ['havano_schools_odoo.statement_receipt', [wizard_id]])
                        if pdf_content and len(pdf_content) > 0:
                            pdf_base64 = base64.b64encode(base64.b64decode(pdf_content[0])).decode('utf-8') if isinstance(pdf_content[0], str) else base64.b64encode(pdf_content[0]).decode('utf-8')
                            attachment = self.env['ir.attachment'].create({
                                'name': f"Statement_{student_name}_{date.today()}.pdf",
                                'type': 'binary',
                                'datas': pdf_base64,
                                'res_model': 'whatsapp.message',
                                'mimetype': 'application/pdf'
                            })
                except Exception as e:
                    _logger.error(f"Failed to generate remote PDF for {student_name}: {e}")

                message = template.format(
                    parent_name=parent['name'],
                    student_name=student_name,
                    school=school_name,
                    balance=move['amount_residual']
                )
                
                msg_vals = {
                    'wa_account_id': account.id,
                    'mobile_number': phone,
                    'body': message,
                    'state': 'sent'
                }
                if attachment:
                    msg_vals['attachment_id'] = attachment.id
                    
                self.env['whatsapp.message'].create(msg_vals)
                account._create_balance_log(student_name, parent['name'], parent_phone, move['amount_residual'], move['id'], 'manual', 'sent', '')
                success_count += 1
            except Exception as e:
                account._create_balance_log(student_name, parent['name'], parent_phone, move['amount_residual'], move['id'], 'manual', 'failed', str(e))
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
