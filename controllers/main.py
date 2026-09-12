from odoo import http
from odoo.http import request

class WhatsAppSignupController(http.Controller):
    
    @http.route('/web/whatsapp/signup', type='http', auth='public')
    def web_whatsapp_signup(self, **kw):
        # Set a flag in the session to indicate this is a WhatsApp SaaS signup
        request.session['is_whatsapp_signup'] = True
        
        # Redirect to the standard signup page
        return request.redirect('/web/signup')
