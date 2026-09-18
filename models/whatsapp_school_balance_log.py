from odoo import models, fields

class WhatsappSchoolBalanceLog(models.Model):
    _name = 'whatsapp.school.balance.log'
    _description = 'School Balance Sending Log'
    _order = 'create_date desc'

    whatsapp_account_id = fields.Many2one('whatsapp.account', string='WhatsApp Account', required=True, ondelete='cascade')
    student_name = fields.Char(string='Student Name')
    parent_name = fields.Char(string='Parent Name')
    parent_number = fields.Char(string='Parent Number')
    balance_amount = fields.Float(string='Balance Sent')
    move_id_ref = fields.Integer(string='Invoice/Receipt ID (Local or Remote)')
    trigger_type = fields.Selection([
        ('billing', 'Billing (Invoice)'),
        ('receipting', 'Receipting (Payment)')
    ], string='Triggered By')
    status = fields.Selection([
        ('sent', 'Sent Successfully'),
        ('failed', 'Failed')
    ], string='Status', default='failed')
    error_message = fields.Text(string='Error Message')
