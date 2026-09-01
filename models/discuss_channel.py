from odoo import models, fields, api

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    wa_is_done = fields.Boolean(string="WhatsApp Chat Done", default=False)
    wa_is_unread_global = fields.Boolean(string="WhatsApp Chat Unread (Global)", default=False)
    wa_is_favourite = fields.Boolean(string="WhatsApp Chat Favourite", default=False)
    wa_is_urgent = fields.Boolean(string="WhatsApp Chat Urgent", default=False)
    wa_tag_ids = fields.Many2many('wa.chat.tag', string='WhatsApp Tags')

    wa_bot_state = fields.Selection([
        ('ask_department', 'Asking Department'),
        ('ask_agent', 'Asking Agent'),
        ('routed', 'Routed')
    ], string='WhatsApp Bot State')
    
    wa_department = fields.Many2one('hr.department', string='Selected Department')
    
    wa_agent_id = fields.Many2one('res.users', string='Selected Agent')


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('channel_type') == 'whatsapp' and not vals.get('whatsapp_partner_id'):
                number = vals.get('whatsapp_number')
                if number:
                    partner = self.env['res.partner'].search([('phone', 'ilike', number)], limit=1)
                    if not partner:
                        partner = self.env['res.partner'].create({'name': number, 'phone': number})
                    vals['whatsapp_partner_id'] = partner.id
        return super().create(vals_list)

    def _wa_bot_route_chat(self):
        self.ensure_one()
        # Admin user
        admin_user = self.env.ref('base.user_admin')
        
        # Determine who should be in the channel
        users_to_add = [admin_user.id]
        
        if self.wa_agent_id:
            users_to_add.append(self.wa_agent_id.id)
        elif self.wa_department:
            # Add all agents in this department
            department_users = self.env['res.users'].sudo().search([
                ('wa_department', '=', self.wa_department.id)
            ])
            department_employees = self.env['hr.employee'].sudo().search([
                ('department_id', '=', self.wa_department.id), ('user_id', '!=', False)
            ])
            users_to_add.extend(department_users.ids)
            users_to_add.extend(department_employees.mapped('user_id').ids)
            
        # Ensure the user sending messages (if they have a user) or public user is handled?
        # Typically discuss.channel members are res.partner
        partners_to_add = self.env['res.users'].sudo().browse(users_to_add).mapped('partner_id').ids
        
        # Also ensure the customer's partner is added if applicable
        if self.whatsapp_partner_id:
            partners_to_add.append(self.whatsapp_partner_id.id)
            
        # Get current members
        current_members = self.channel_member_ids.mapped('partner_id').ids
        
        # Partners to remove
        partners_to_remove = [p for p in current_members if p not in partners_to_add]
        
        # Partners to add
        partners_to_add_new = [p for p in partners_to_add if p not in current_members]
        
        # Remove old members
        if partners_to_remove:
            self.channel_member_ids.filtered(lambda m: m.partner_id.id in partners_to_remove).unlink()
            
        # Add new members
        if partners_to_add_new:
            new_members = [(0, 0, {'partner_id': pid}) for pid in partners_to_add_new]
            self.write({'channel_member_ids': new_members})

    @api.model
    def transfer_whatsapp_chat(self, channel_id, department_id, agent_id=False):
        channel = self.browse(channel_id)
        if not channel.exists():
            return False
            
        channel.write({
            'wa_department': department_id,
            'wa_agent_id': agent_id,
            'wa_bot_state': 'routed',
        })
        
        channel._wa_bot_route_chat()
        
        # Post a message noting the transfer internally
        dept = self.env['hr.department'].browse(department_id)
        agent = self.env['res.users'].browse(agent_id) if agent_id else False
        
        msg = f"Chat transferred to {dept.name} department"
        if agent:
            msg += f", agent {agent.name}"
            
        channel.message_post(body=msg, message_type='notification')
        
        # Send automated message to the customer via WhatsApp API
        customer_msg = f"Your chat has been successfully transferred to the {dept.name} department under {agent.name if agent else 'any available agent'}. Your issue will be solved soon, and we will get back to you when done."
        if channel.wa_account_id:
            channel.wa_account_id._send_bot_reply(channel, customer_msg)
        else:
            channel.message_post(body=customer_msg, message_type='comment', subtype_xmlid='mail.mt_comment')
        return True
