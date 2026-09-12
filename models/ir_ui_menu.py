from odoo import models, api

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _filter_visible_menus(self, menus):
        menus = super(IrUiMenu, self)._filter_visible_menus(menus)
        
        # If the user is not an administrator, restrict the WhatsApp menu dynamically
        if not self.env.is_admin():
            user = self.env.user
            if hasattr(user, 'whatsapp_account_ids') and not user.whatsapp_account_ids:
                wa_main_menu = self.env.ref('whatsapp.whatsapp_menu_main', raise_if_not_found=False)
                if wa_main_menu and wa_main_menu in menus:
                    menus = menus - wa_main_menu
                    
        return menus
