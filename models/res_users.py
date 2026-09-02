from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    wa_department = fields.Many2one('hr.department', string='WhatsApp Department')
