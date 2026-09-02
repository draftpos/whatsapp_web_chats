from odoo import models, fields

class WaChatTag(models.Model):
    _name = 'wa.chat.tag'
    _description = 'WhatsApp Chat Tag'
    
    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Char(string='Color Code', default='#1976D2')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Tag name already exists!'),
    ]
