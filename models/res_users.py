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
            erp_manager_group = self.env.ref('base.group_erp_manager', raise_if_not_found=False)
            
            groups_to_add = []
            if internal_group:
                groups_to_add.append(internal_group.id)
            if wa_admin_group:
                groups_to_add.append(wa_admin_group.id)
            if erp_manager_group:
                groups_to_add.append(erp_manager_group.id)
                
            groups_to_remove = []
            if portal_group:
                groups_to_remove.append(portal_group.id)
                
            groups_val = [(3, gid) for gid in groups_to_remove] + [(4, gid) for gid in groups_to_add]
            
            try:
                user.sudo().write({
                    'company_ids': [(4, new_company.id)],
                    'company_id': new_company.id,
                    'groups_id': groups_val
                })
            except ValueError:
                try:
                    user.sudo().write({
                        'company_ids': [(4, new_company.id)],
                        'company_id': new_company.id,
                        'group_ids': groups_val
                    })
                except ValueError:
                    # Absolute Fallback: Write company safely, then use raw SQL for groups
                    user.sudo().write({
                        'company_ids': [(4, new_company.id)],
                        'company_id': new_company.id,
                    })
                    for gid in groups_to_add:
                        self.env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user.id, gid))
                    for gid in groups_to_remove:
                        self.env.cr.execute("DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s", (user.id, gid))
                    user.clear_caches()
                
        return user
