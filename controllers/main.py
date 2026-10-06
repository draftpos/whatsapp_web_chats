from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request, route

class WhatsAppSignup(AuthSignupHome):

    @route()
    def web_auth_signup(self, *args, **kw):
        response = super(WhatsAppSignup, self).web_auth_signup(*args, **kw)
        
        # If the response is a redirect to /web (successful login)
        if hasattr(response, 'status_code') and response.status_code in (301, 302, 303):
            location = response.headers.get('Location', '')
            if location == '/web' or location.startswith('/web?'):
                # Check if it's a whatsapp signup
                if kw.get('is_whatsapp_signup'):
                    # Redirect to WhatsApp Chats action
                    response.headers['Location'] = '/web#action=whatsapp_web_chats.action_whatsapp_web_chats'
                    
        return response

from odoo import http

class WhatsAppWebhookOverride(http.Controller):
    @http.route('/whatsapp/webhook/', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def webhookpost(self, **kwargs):
        import logging
        import traceback
        _logger = logging.getLogger(__name__)
        _logger.error(f"CRITICAL WEBHOOK OVERRIDE HIT: method={request.httprequest.method}, kwargs={kwargs}")
        try:
            if request.httprequest.method == 'GET':
                return request.make_response(kwargs.get('hub.challenge', ''), status=200)
            if request.httprequest.method == 'POST':
                data = request.get_json_data()
                _logger.error(f"CRITICAL WEBHOOK PAYLOAD: {data}")
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        request.env['whatsapp.account'].sudo()._process_messages(value)
                return request.make_response("success", status=200)
        except Exception as e:
            _logger.error(f"CRITICAL WEBHOOK EXCEPTION: {e}")
            _logger.error(traceback.format_exc())
            return request.make_response("success", status=200)
