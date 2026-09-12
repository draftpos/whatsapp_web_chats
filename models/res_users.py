from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    wa_department = fields.Many2one('hr.department', string='WhatsApp Department')
    whatsapp_account_ids = fields.Many2many('whatsapp.account', 'wa_account_res_users_rel', 'user_id', 'account_id', string='WhatsApp Accounts')
