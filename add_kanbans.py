import os

views_to_add = [
    {
        'file': r'c:\odoo19\addons\whatsapp\views\whatsapp_message_views.xml',
        'model': 'whatsapp.message',
        'id': 'whatsapp_message_view_kanban',
        'fields': ['body', 'state', 'mobile_number', 'create_date'],
        'title': 'mobile_number',
        'subtitle': 'create_date',
        'action_file': r'c:\odoo19\addons\whatsapp\views\whatsapp_message_views.xml',
        'action_id': 'whatsapp_message_action'
    },
    {
        'file': r'c:\odoo19\addons\whatsapp\views\whatsapp_account_views.xml',
        'model': 'whatsapp.account',
        'id': 'whatsapp_account_view_kanban',
        'fields': ['name'],
        'title': 'name',
        'subtitle': '',
        'action_file': r'c:\odoo19\addons\whatsapp\views\whatsapp_account_views.xml',
        'action_id': 'whatsapp_account_action'
    },
    {
        'file': r'c:\odoo19\addons\whatsapp_web_chats\views\whatsapp_quick_reply_views.xml',
        'model': 'whatsapp.quick.reply',
        'id': 'whatsapp_quick_reply_view_kanban',
        'fields': ['name', 'message'],
        'title': 'name',
        'subtitle': 'message',
        'action_file': r'c:\odoo19\addons\whatsapp_web_chats\views\whatsapp_quick_reply_views.xml',
        'action_id': 'whatsapp_quick_reply_action'
    },
    {
        'file': r'c:\odoo19\addons\dev_whatsapp_chatbot_ent\views\wa_chatbot_flow_views.xml',
        'model': 'wa.chatbot.flow',
        'id': 'wa_chatbot_flow_view_kanban',
        'fields': ['name', 'chatbot_id'],
        'title': 'name',
        'subtitle': 'chatbot_id',
        'action_file': r'c:\odoo19\addons\dev_whatsapp_chatbot_ent\views\menu.xml',
        'action_id': 'action_wa_chatbot_flow'
    },
    {
        'file': r'c:\odoo19\addons\dev_whatsapp_chatbot_ent\views\wa_chatbot_session_views.xml',
        'model': 'wa.chatbot.session',
        'id': 'wa_chatbot_session_view_kanban',
        'fields': ['display_name', 'state'],
        'title': 'display_name',
        'subtitle': 'state',
        'action_file': r'c:\odoo19\addons\dev_whatsapp_chatbot_ent\views\menu.xml',
        'action_id': 'action_wa_chatbot_session'
    },
    {
        'file': r'c:\odoo19\addons\dev_whatsapp_chatbot_ent\views\wa_chatbot_keyword_views.xml',
        'model': 'wa.chatbot.keyword',
        'id': 'wa_chatbot_keyword_view_kanban',
        'fields': ['name', 'chatbot_id'],
        'title': 'name',
        'subtitle': 'chatbot_id',
        'action_file': r'c:\odoo19\addons\dev_whatsapp_chatbot_ent\views\menu.xml',
        'action_id': 'action_wa_chatbot_keyword'
    }
]

for v in views_to_add:
    if os.path.exists(v['file']):
        with open(v['file'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        if v['id'] not in content:
            fields_xml = '\n'.join([f'                        <field name="{f}"/>' for f in v['fields']])
            
            # Use 'if True:' so we don't insert a literal t-if if it's empty
            subtitle_xml = f"""
                            <div class="row">
                                <div class="col-12 text-muted">
                                    <field name="{v['subtitle']}"/>
                                </div>
                            </div>""" if v['subtitle'] else ""

            kanban_xml = f"""
    <record id="{v['id']}" model="ir.ui.view">
        <field name="name">{v['model']}.kanban</field>
        <field name="model">{v['model']}</field>
        <field name="arch" type="xml">
            <kanban class="o_kanban_mobile">
{fields_xml}
                <templates>
                    <t t-name="kanban-box">
                        <div t-attf-class="oe_kanban_global_click">
                            <div class="row">
                                <div class="col-12">
                                    <strong><field name="{v['title']}"/></strong>
                                </div>
                            </div>{subtitle_xml}
                        </div>
                    </t>
                </templates>
            </kanban>
        </field>
    </record>
</odoo>"""
            content = content.replace('</odoo>', kanban_xml)
            with open(v['file'], 'w', encoding='utf-8') as f:
                f.write(content)
                
    if os.path.exists(v['action_file']):
        with open(v['action_file'], 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        in_action = False
        for i, line in enumerate(lines):
            if f'id="{v["action_id"]}"' in line or f"id='{v['action_id']}'" in line:
                in_action = True
            if in_action and 'name="view_mode"' in line:
                if 'kanban' not in line:
                    lines[i] = line.replace('list,form', 'kanban,list,form').replace('tree,form', 'kanban,tree,form')
                in_action = False
            if in_action and '</record>' in line:
                in_action = False
                
        with open(v['action_file'], 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
chats_action_file = r'c:\odoo19\addons\whatsapp_web_chats\views\chats_action.xml'
if os.path.exists(chats_action_file):
    with open(chats_action_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    in_action = False
    for i, line in enumerate(lines):
        if 'id="whatsapp_quick_reply_config_action"' in line:
            in_action = True
        if in_action and 'name="view_mode"' in line:
            if 'kanban' not in line:
                lines[i] = line.replace('list,form', 'kanban,list,form').replace('tree,form', 'kanban,tree,form')
            in_action = False
        if in_action and '</record>' in line:
            in_action = False
    with open(chats_action_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

print("Added kanban views successfully!")
