from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    wa_department = fields.Selection([
        ('accounting', 'Accounting'),
        ('operations', 'Operations'),
        ('tech', 'Tech'),
        ('sales', 'Sales'),
        ('marketing', 'Marketing')
    ], string='WhatsApp Department')
