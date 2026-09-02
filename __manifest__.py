{
    'name': 'WhatsApp Web Chats',
    'version': '1.0',
    'category': 'Discuss',
    'summary': 'Provides a WhatsApp Web-like interface for managing WhatsApp chats.',
    'depends': ['mail', 'base', 'web', 'whatsapp', 'product', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/ir_rule.xml',
        'data/wa_chat_tag_data.xml',
        'views/whatsapp_account_views.xml',
        'views/chats_action.xml',
        'views/product_template_views.xml',
        'views/res_users_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'whatsapp_web_chats/static/src/css/chats.css',
            'whatsapp_web_chats/static/src/xml/chats_template.xml',
            'whatsapp_web_chats/static/src/js/chats.js',
        ],
    },
    'installable': True,
    'application': True,
}
