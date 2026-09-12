from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    tenant_id = fields.Many2one('res.company', string='Tenant', default=lambda self: self.env.company)
    wa_department = fields.Many2one('hr.department', string='WhatsApp Department')
    whatsapp_account_ids = fields.Many2many('whatsapp.account', 'wa_account_res_users_rel', 'user_id', 'account_id', string='WhatsApp Accounts')

    @api.model
    def _signup_create_user(self, values):
        from odoo.http import request
        
        is_wa_signup = False
        company_name_from_req = None
        if request and hasattr(request, 'params'):
            is_wa_signup = bool(request.params.get('is_whatsapp_signup'))
            company_name_from_req = request.params.get('company_name')

        user = super(ResUsers, self)._signup_create_user(values)
        
        if is_wa_signup:
            company_name = company_name_from_req or (user.name + ' Company')
            new_company = self.env['res.company'].sudo().create({'name': company_name})
            
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            internal_group = self.env.ref('base.group_user', raise_if_not_found=False)
            wa_admin_group = self.env.ref('whatsapp.group_whatsapp_admin', raise_if_not_found=False)
            
            if internal_group:
                internal_group.sudo().write({'users': [(4, user.id)]})
            if wa_admin_group:
                wa_admin_group.sudo().write({'users': [(4, user.id)]})
            if portal_group:
                portal_group.sudo().write({'users': [(3, user.id)]})
                
            user.sudo().write({
                'company_ids': [(4, new_company.id)],
                'company_id': new_company.id,
            })
                
        return user
