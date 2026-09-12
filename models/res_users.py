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
        if request and hasattr(request, 'session'):
            is_wa_signup = request.session.get('is_whatsapp_signup')
            
        if is_wa_signup:
            # Create a new company
            company_name_from_req = request.params.get('company_name') if hasattr(request, 'params') else None
            company_name = company_name_from_req or (values.get('name', 'WhatsApp') + ' Company')
            new_company = self.env['res.company'].sudo().create({'name': company_name})
            
            # Make sure they are assigned to this company
            values['company_id'] = new_company.id
            values['company_ids'] = [(6, 0, [new_company.id])]
            
            # Pop the flag
            request.session.pop('is_whatsapp_signup', None)

        user = super(ResUsers, self)._signup_create_user(values)
        
        if is_wa_signup:
            # Replace portal group with internal user group
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            internal_group = self.env.ref('base.group_user', raise_if_not_found=False)
            wa_admin_group = self.env.ref('whatsapp.group_whatsapp_admin', raise_if_not_found=False)
            
            groups_to_add = []
            if internal_group:
                groups_to_add.append(internal_group.id)
            if wa_admin_group:
                groups_to_add.append(wa_admin_group.id)
                
            groups_to_remove = []
            if portal_group:
                groups_to_remove.append(portal_group.id)
                
            if groups_to_add or groups_to_remove:
                user.sudo().write({
                    'groups_id': [(3, gid) for gid in groups_to_remove] + [(4, gid) for gid in groups_to_add]
                })
                
        return user
