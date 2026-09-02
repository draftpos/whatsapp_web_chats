from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    wa_show_labels = fields.Boolean("Show WhatsApp Chat Labels", config_parameter='whatsapp_web_chats.wa_show_labels', default=True)
