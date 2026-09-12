from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

class WhatsAppSignupController(AuthSignupHome):
    
    @http.route('/web/whatsapp/signup', type='http', auth='public', website=True, sitemap=False)
    def web_whatsapp_signup(self, *args, **kw):
        # Set a flag in the session to indicate this is a WhatsApp SaaS signup
        request.session['is_whatsapp_signup'] = True
        
        # We need to make sure we render the signup template
        # The easiest way is to set the token or just call web_auth_signup
        # But we must ensure the form POSTs back to either here or /web/signup with the session intact
        return self.web_auth_signup(*args, **kw)
