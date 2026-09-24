from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    wa_contact_sharing_mode = fields.Selection([
        ('all', 'Share Across All Numbers'),
        ('isolated', 'Isolated (Each number sees own contacts)'),
        ('specific', 'Specific Sharing')
    ], string="Contact Sharing Mode", default='all')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    wa_contact_sharing_mode = fields.Selection(
        related='company_id.wa_contact_sharing_mode', 
        readonly=False
    )


class WhatsappAccount(models.Model):
    _inherit = 'whatsapp.account'
    
    wa_contact_sharing_mode = fields.Selection(related='company_id.wa_contact_sharing_mode')
    
    shared_contact_account_ids = fields.Many2many(
        'whatsapp.account',
        'whatsapp_account_contact_share_rel',
        'account_id',
        'shared_id',
        string="Share Contacts With",
        help="If mode is Specific, this account shares its contacts with these accounts."
    )

    @api.model
    def get_contacts_for_new_chat(self):
        """ Override to fetch contacts based on sharing mode while strictly enforcing tenant boundaries. """
        mode = self.env.company.wa_contact_sharing_mode or 'all'
        
        # Always enforce tenant boundaries when using sudo()
        domain = [
            ('phone', '!=', False),
            '|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)
        ]
        
        # Admin or 'all' mode just gets the tenant-filtered domain above
        if not self.env.is_admin() and mode != 'all':
            allowed_accounts = self.env.user.whatsapp_account_ids
            
            if mode == 'isolated':
                domain.extend([
                    '|', ('wa_account_id', '=', False),
                         ('wa_account_id', 'in', allowed_accounts.ids)
                ])
            elif mode == 'specific':
                shared_accounts = allowed_accounts.mapped('shared_contact_account_ids')
                all_allowed = allowed_accounts | shared_accounts
                domain.extend([
                    '|', ('wa_account_id', '=', False),
                         ('wa_account_id', 'in', all_allowed.ids)
                ])
            
        contacts = self.env['res.partner'].sudo().search_read(
            domain, ['id', 'name', 'phone'], order='name asc'
        )
        return contacts

    def sync_device_contacts(self, contacts):
        res = super().sync_device_contacts(contacts)
        if hasattr(self.env.user, 'whatsapp_account_ids') and self.env.user.whatsapp_account_ids:
            wa_acc = self.env.user.whatsapp_account_ids[0]
            for c in res.get('contacts', []):
                if c.get('status') == 'created':
                    partner = self.env['res.partner'].sudo().browse(c.get('id'))
                    if not partner.wa_account_id:
                        partner.wa_account_id = wa_acc.id
        return res


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    wa_account_id = fields.Many2one(
        'whatsapp.account', 
        string="Source WhatsApp Account",
        help="The WhatsApp Account this contact belongs to (for sharing rules)."
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        # Check if created within a whatsapp account context (like _create_chat_from_number)
        if hasattr(self.env.user, 'whatsapp_account_ids') and self.env.user.whatsapp_account_ids:
            wa_acc = self.env.user.whatsapp_account_ids[0]
            for partner in res:
                if not partner.wa_account_id:
                    partner.wa_account_id = wa_acc.id
        return res
