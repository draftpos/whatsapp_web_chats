from odoo import models, fields

class WhatsAppTemplate(models.Model):
    _inherit = 'whatsapp.template'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
