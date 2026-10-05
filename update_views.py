import re

with open('crm_view_source.xml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

title_content = "".join(lines[51:99])
group_content = "".join(lines[99:252])

new_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="crm_lead_view_form_whatsapp" model="ir.ui.view">
        <field name="name">crm.lead.view.form.whatsapp</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="crm.crm_lead_view_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='name']" position="attributes">
                <attribute name="invisible">1</attribute>
            </xpath>
            <xpath expr="//field[@name='name']" position="after">
                <field name="project_category" placeholder="Select Project Category..." class="text-break"/>
            </xpath>
            
            <xpath expr="//div[hasclass('oe_title')]" position="replace">
                <notebook>
                    <page name="lead_page" string="Lead">
{title_content}
{group_content}
                    </page>
                    <page name="wa_chats" string="WA Chats" style="padding: 0 !important;">
                        <field name="id" widget="crm_whatsapp_chat_widget" nolabel="1"/>
                    </page>
                </notebook>
            </xpath>

            <xpath expr="//sheet/group[1]" position="replace">
                <!-- Removed because it is now inside the Lead tab -->
            </xpath>
        </field>
    </record>

    <!-- Inherit Tree View to add the message counting column -->
    <record id="crm_lead_view_tree_whatsapp" model="ir.ui.view">
        <field name="name">crm.lead.view.tree.whatsapp</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="crm.crm_case_tree_view_leads"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='name']" position="after">
                <field name="wa_unread_messages_count" string="New WA Messages" optional="show"/>
            </xpath>
        </field>
    </record>
    
    <!-- Also inherit the opportunities tree view just in case -->
    <record id="crm_case_tree_view_oppor_whatsapp" model="ir.ui.view">
        <field name="name">crm.lead.view.tree.oppor.whatsapp</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="crm.crm_case_tree_view_oppor"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='name']" position="after">
                <field name="wa_unread_messages_count" string="New WA Messages" optional="show"/>
            </xpath>
        </field>
    </record>
</odoo>
"""

with open('views/crm_lead_views.xml', 'w', encoding='utf-8') as f:
    f.write(new_xml)

print("Updated views/crm_lead_views.xml")
