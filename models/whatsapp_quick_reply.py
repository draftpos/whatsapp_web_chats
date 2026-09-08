from odoo import api, fields, models

class WhatsAppQuickReply(models.Model):
    _name = 'whatsapp.quick.reply'
    _description = 'WhatsApp Quick Reply'
    _order = 'is_pinned desc, is_favorite desc, shortcut asc, id desc'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    shortcut = fields.Char(string="Shortcut", help="Optional shortcut to easily find the quick reply (e.g. greeting)")
    body = fields.Text(string="Message Body", required=True)
    account_id = fields.Many2one('whatsapp.account', string="WhatsApp Account", help="Leave blank if applicable to all accounts")
    is_pinned = fields.Boolean(string="Pinned", default=False)
    is_favorite = fields.Boolean(string="Favorite", default=False)
    
    @api.model
    def get_quick_replies(self, account_id=None):
        current_company = self.env.company
        domain = [('account_id', '=', False), ('tenant_id', '=', current_company.id)]
        if account_id:
            domain = ['|', ('account_id', '=', account_id), ('account_id', '=', False)]
            domain.append(('tenant_id', '=', current_company.id))
        
        replies = self.search(domain)
        return [{'id': r.id, 'shortcut': r.shortcut or '', 'body': r.body, 'is_pinned': r.is_pinned, 'is_favorite': r.is_favorite} for r in replies]

    def toggle_pin(self):
        for record in self:
            record.is_pinned = not record.is_pinned

    def toggle_favorite(self):
        for record in self:
            record.is_favorite = not record.is_favorite
