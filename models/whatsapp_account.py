from odoo import models, fields

class WhatsAppAccount(models.Model):
    _inherit = 'whatsapp.account'

    image_1920 = fields.Image(string="Profile Picture", max_width=1920, max_height=1920)

    def _process_messages(self, value):
        for message in value.get('messages', []):
            if message.get('type') == 'order':
                order = message.get('order', {})
                items = order.get('product_items', [])
                
                text_lines = ["🛒 *New Order Received!*"]
                if order.get('text'):
                    text_lines.append(f"Note: {order['text']}")
                text_lines.append("Items:")
                
                for item in items:
                    qty = item.get('quantity', 0)
                    price = item.get('item_price', '')
                    currency = item.get('currency', '')
                    product_id = item.get('product_retailer_id', 'Unknown Item')
                    
                    product = self.env['product.product'].sudo().search([
                        '|', ('default_code', '=', product_id), 
                        ('id', '=', int(product_id) if str(product_id).isdigit() else 0)
                    ], limit=1)
                    
                    product_name = product.name if product else product_id
                    text_lines.append(f"- {qty}x {product_name} ({currency} {price})")
                
                message['type'] = 'text'
                message['text'] = {'body': '\n'.join(text_lines)}
                
        return super()._process_messages(value)
