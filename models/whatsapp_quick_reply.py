from odoo import api, fields, models

class WhatsAppQuickReply(models.Model):
    _name = 'whatsapp.quick.reply'
    _description = 'WhatsApp Quick Reply'
    _order = 'shortcut asc, id desc'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    shortcut = fields.Char(string="Shortcut", help="Optional shortcut to easily find the quick reply (e.g. greeting)")
    body = fields.Text(string="Message Body", required=True)
    account_id = fields.Many2one('whatsapp.account', string="WhatsApp Account", help="Leave blank if applicable to all accounts")
    
    @api.model
    def get_quick_replies(self, account_id=None):
        domain = [('account_id', '=', False)]
        if account_id:
            domain = ['|', ('account_id', '=', account_id), ('account_id', '=', False)]
        
        replies = self.search(domain)
        return [{'id': r.id, 'shortcut': r.shortcut or '', 'body': r.body} for r in replies]
