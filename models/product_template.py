from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    show_in_catalogue = fields.Boolean(
        string='Show in WhatsApp Catalogue',
        default=False,
        help="Check this box to show this product in the WhatsApp Web Chats catalogue."
    )
