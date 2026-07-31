from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    show_in_catalogue = fields.Boolean(
        string='Show in WhatsApp Catalogue',
        default=False,
        help="Check this box to show this product in the WhatsApp Web Chats catalogue."
    )
