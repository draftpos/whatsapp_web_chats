/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { WhatsAppChatsAction } from "@whatsapp_web_chats/js/chats";

export class CrmWhatsappChatWidget extends Component {
    setup() {
        // We reuse the WhatsAppChatsAction component but pass hideSidebar as true
    }
}
CrmWhatsappChatWidget.template = "whatsapp_web_chats.CrmChatWidget";
CrmWhatsappChatWidget.components = { WhatsAppChatsAction };
CrmWhatsappChatWidget.props = {
    ...standardFieldProps,
};

registry.category("fields").add("crm_whatsapp_chat_widget", {
    component: CrmWhatsappChatWidget,
    supportedTypes: ["many2one", "integer"],
});
