from odoo import api, fields, models

class WhatsAppQuickReply(models.Model):
    _name = 'whatsapp.quick.reply'
    _description = 'WhatsApp Quick Reply'
    _order = 'sequence asc, is_pinned desc, is_favorite desc, shortcut asc, id desc'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)

    shortcut = fields.Char(string="Shortcut", help="Optional shortcut to easily find the quick reply (e.g. greeting)")
    body = fields.Text(string="Message Body", required=True)
    account_id = fields.Many2one('whatsapp.account', string="WhatsApp Account", help="Leave blank if applicable to all accounts")
    is_pinned = fields.Boolean(string="Pinned", default=False)
    is_favorite = fields.Boolean(string="Favorite", default=False)
    sequence = fields.Integer(string="Sequence", default=10)

    @api.model_create_multi
    def create(self, vals_list):
        from odoo.exceptions import ValidationError
        for vals in vals_list:
            if vals.get('body'):
                duplicate = self.search([('body', '=ilike', str(vals.get('body')).strip())], limit=1)
                if duplicate:
                    raise ValidationError("A Quick Reply with this exact message already exists!")
            if vals.get('shortcut'):
                duplicate = self.search([('shortcut', '=ilike', str(vals.get('shortcut')).strip())], limit=1)
                if duplicate:
                    raise ValidationError("A Quick Reply with this shortcut already exists!")
        return super(WhatsAppQuickReply, self).create(vals_list)

    def write(self, vals):
        from odoo.exceptions import ValidationError
        for record in self:
            body = vals.get('body', record.body)
            shortcut = vals.get('shortcut', record.shortcut)
            if 'body' in vals and body:
                duplicate = self.search([('body', '=ilike', str(body).strip()), ('id', '!=', record.id)], limit=1)
                if duplicate:
                    raise ValidationError("A Quick Reply with this exact message already exists!")
            if 'shortcut' in vals and shortcut:
                duplicate = self.search([('shortcut', '=ilike', str(shortcut).strip()), ('id', '!=', record.id)], limit=1)
                if duplicate:
                    raise ValidationError("A Quick Reply with this shortcut already exists!")
        return super(WhatsAppQuickReply, self).write(vals)
    
    @api.model
    def get_quick_replies(self, account_id=None):
        current_company = self.env.company
        # Show replies for this company OR unassigned legacy replies (tenant_id = False)
        tenant_filter = ['|', ('tenant_id', '=', False), ('tenant_id', '=', current_company.id)]
        domain = [('account_id', '=', False)] + tenant_filter
        if account_id:
            domain = ['|', ('account_id', '=', account_id), ('account_id', '=', False)] + tenant_filter
        
        replies = self.search(domain)
        return [{'id': r.id, 'shortcut': r.shortcut or '', 'body': r.body, 'is_pinned': r.is_pinned, 'is_favorite': r.is_favorite} for r in replies]

    def toggle_pin(self):
        for record in self:
            record.is_pinned = not record.is_pinned

    def toggle_favorite(self):
        for record in self:
            record.is_favorite = not record.is_favorite
