from odoo import models, api

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _filter_visible_menus(self):
        menus = super(IrUiMenu, self)._filter_visible_menus()
        
        # If the user is not a system administrator AND not a WhatsApp admin, restrict the WhatsApp menu dynamically
        if not self.env.is_admin() and not self.env.user.has_group('whatsapp.group_whatsapp_admin'):
            user = self.env.user
            if hasattr(user, 'whatsapp_account_ids') and not user.whatsapp_account_ids:
                wa_main_menu = self.env.ref('whatsapp.whatsapp_menu_main', raise_if_not_found=False)
                if wa_main_menu and wa_main_menu in menus:
                    menus = menus - wa_main_menu
                    
        return menus
