# -*- coding: utf-8 -*-
from odoo import fields, models, api

class WhatsAppProduct(models.Model):
    _name = "whatsapp.product"
    _description = "WhatsApp Business Catalogue Product"

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    name = fields.Char(string="Name", required=True, translate=True)
    list_price = fields.Float(string="Price", digits="Product Price")
    description = fields.Text(string="Description", translate=True)
    url = fields.Char(string="Link")
    item_code = fields.Char(string="Item Code")
    image_1920 = fields.Binary(string="Image", attachment=True)
    image_128 = fields.Binary(string="Small Image", related="image_1920", store=True)
    show_in_catalogue = fields.Boolean(string="Show in catalogue", default=True)

    @api.model
    def sync_from_meta(self):
        # Placeholder: later integration with Meta Business API
        return True
