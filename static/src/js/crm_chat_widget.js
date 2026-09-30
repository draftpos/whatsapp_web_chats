/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { WhatsAppChatsAction } from "@whatsapp_web_chats/js/chats";

export class CrmWhatsappChatWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({ channelId: null, loading: true });

        onWillStart(async () => {
            await this._loadChannel();
        });
    }

    async _loadChannel() {
        const leadId = this.props.record.resId;
        if (!leadId) {
            this.state.loading = false;
            return;
        }
        try {
            // Call the Python method that already knows how to find the right channel
            const result = await this.orm.call(
                "crm.lead",
                "get_whatsapp_channel_id_for_widget",
                [[leadId]],
                {},
                { silent: true }
            );
            this.state.channelId = result || null;
        } catch (e) {
            console.warn("Could not get WA channel for lead", e);
            this.state.channelId = null;
        }
        this.state.loading = false;
    }

    async openChat() {
        const leadId = this.props.record.resId;
        if (!leadId) return;
        try {
            // This creates the channel if it doesn't exist, then returns its ID
            const result = await this.orm.call(
                "crm.lead",
                "get_whatsapp_channel_id_for_widget",
                [[leadId]],
                { create_if_missing: true },
                { silent: true }
            );
            if (result) {
                this.state.channelId = result;
            }
        } catch (e) {
            console.warn("Failed to open WA chat", e);
        }
    }
}
CrmWhatsappChatWidget.template = "whatsapp_web_chats.CrmChatWidget";
CrmWhatsappChatWidget.components = { WhatsAppChatsAction };
CrmWhatsappChatWidget.props = {
    ...standardFieldProps,
};

registry.category("fields").add("crm_whatsapp_chat_widget", {
    component: CrmWhatsappChatWidget,
    supportedTypes: ["many2one", "integer", "char"],
});
