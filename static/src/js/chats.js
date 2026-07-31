/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillDestroy, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class WhatsAppChatsAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.messagesContainer = useRef("messagesContainer");
        
        this.state = useState({
            channels: [],
            selectedChannel: null,
            messages: [],
            newMessage: "",
            pendingFile: null,
            accounts: [],
            selectedAccount: null,
            products: [],
            showCatalogue: false,
            wa_templates: [],
            showTemplatesModal: false,
        });
        
        this.myPartnerId = null;

        onWillStart(async () => {
            await this.loadChannels();
            await this.loadProducts();
            await this.loadTemplates();
        });
        
        onMounted(() => {
            this.pollInterval = setInterval(() => {
                this.pollMessages();
            }, 5000);
        });
        
        onWillDestroy(() => {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
            }
        });
    }

    async loadProducts() {
        try {
            // Load all saleable products from product.template
            const results = await this.orm.searchRead(
                "product.template",
                [["sale_ok", "=", true]],
                ["id", "name", "list_price", "image_128"],
                { limit: 80, order: "name asc" }
            );
            this.state.products = results;
        } catch (e) {
            console.error("Error loading products", e);
            this.state.products = [];
        }
    }

    async loadTemplates() {
        try {
            this.state.wa_templates = await this.orm.searchRead(
                "whatsapp.template",
                [], 
                ["id", "template_name", "body"]
            );
        } catch (e) {
            console.error("Error loading templates", e);
        }
    }

    async loadChannels() {
        if (!this.myPartnerId && session.uid) {
            const users = await this.orm.searchRead("res.users", [["id", "=", session.uid]], ["partner_id"]);
            if (users.length > 0 && users[0].partner_id) {
                this.myPartnerId = users[0].partner_id[0];
            }
        }
        
        if (this.state.accounts.length === 0) {
            this.state.accounts = await this.orm.searchRead("whatsapp.account", [], ["id", "name", "image_1920"]);
            if (this.state.accounts.length > 0) {
                this.state.selectedAccount = this.state.accounts[0].id.toString();
            }
        }

        const domain = [["channel_type", "=", "whatsapp"]];
        if (this.state.selectedAccount) {
            domain.push(["wa_account_id", "=", parseInt(this.state.selectedAccount)]);
        }

        const channels = await this.orm.searchRead(
            "discuss.channel",
            domain,
            ["id", "name", "channel_type", "whatsapp_partner_id", "wa_account_id"]
        );
        
        if (channels.length > 0 && this.myPartnerId) {
            const members = await this.orm.searchRead(
                "discuss.channel.member",
                [["partner_id", "=", this.myPartnerId], ["channel_id", "in", channels.map(c => c.id)]],
                ["channel_id", "message_unread_counter"]
            );
            const unreadMap = {};
            for (const m of members) {
                if (m.channel_id && m.channel_id[0]) {
                    unreadMap[m.channel_id[0]] = m.message_unread_counter;
                }
            }
            for (const c of channels) {
                c.unread_count = unreadMap[c.id] || 0;
            }
        }
        
        // Fallback: if empty, try fetching 'chat' or just everything
        if (channels.length === 0) {
            const allChannels = await this.orm.searchRead(
                "discuss.channel",
                [], 
                ["id", "name", "channel_type", "whatsapp_partner_id", "wa_account_id"]
            );
            channels.push(...allChannels);
        }
        
        const partnerIds = channels.map(c => c.whatsapp_partner_id && c.whatsapp_partner_id[0]).filter(id => id);
        if (partnerIds.length > 0) {
            const partners = await this.orm.searchRead("res.partner", [["id", "in", partnerIds]], ["id", "avatar_128", "phone"]);
            const partnerMap = {};
            for (const p of partners) {
                partnerMap[p.id] = { image: p.avatar_128, phone: p.phone };
            }
            for (const c of channels) {
                if (c.whatsapp_partner_id) {
                    const pData = partnerMap[c.whatsapp_partner_id[0]];
                    if (pData) {
                        c.customer_image = pData.image;
                        c.customer_phone = pData.phone;
                    }
                }
                if (c.wa_account_id) {
                    c.wa_account_id = c.wa_account_id[0];
                }
            }
        }
        
        this.state.channels = channels;
        if (channels.length > 0 && !this.state.selectedChannel) {
            this.selectChannel(channels[0]);
        }
    }

    async changeChatAccount(ev) {
        if (!this.state.selectedChannel) return;
        const newAccountId = parseInt(ev.target.value);
        this.state.selectedChannel.wa_account_id = newAccountId;
        // The UI updates automatically via reactivity.
        // We could also attempt to update the backend channel record here if needed.
    }

    async selectChannel(channel) {
        this.state.selectedChannel = channel;
        await this.loadMessages(channel.id);
    }

    async loadMessages(channelId = null) {
        const id = channelId || (this.state.selectedChannel ? this.state.selectedChannel.id : null);
        if (!id) return;
        const messages = await this.orm.searchRead(
            "mail.message",
            [["res_id", "=", id], ["model", "=", "discuss.channel"]],
            ["id", "body", "author_id", "date", "attachment_ids"],
            { limit: 100, order: "date asc" }
        );
        
        this.state.messages = messages.map(msg => {
            let isMe = true;
            if (msg.author_id && this.state.selectedChannel && this.state.selectedChannel.whatsapp_partner_id) {
                isMe = (msg.author_id[0] !== this.state.selectedChannel.whatsapp_partner_id[0]);
            }
            
            let tmp = document.createElement("DIV");
            tmp.innerHTML = msg.body || "";
            let bodyText = tmp.textContent || tmp.innerText || "";
            
            let timeText = msg.date;
            if (msg.date) {
                try {
                    let dStr = msg.date.replace(" ", "T");
                    if (!dStr.endsWith("Z")) dStr += "Z";
                    let dt = new Date(dStr);
                    let hours = dt.getHours();
                    let minutes = dt.getMinutes();
                    let ampm = hours >= 12 ? 'PM' : 'AM';
                    hours = hours % 12;
                    hours = hours ? hours : 12;
                    minutes = minutes < 10 ? '0' + minutes : minutes;
                    timeText = hours + ':' + minutes + ' ' + ampm;
                } catch (e) {
                    timeText = msg.date;
                }
            }
            
            return {
                ...msg,
                isMe: isMe,
                bodyText: bodyText,
                timeText: timeText
            };
        });
        
        this.scrollToBottom();
    }
    
    async pollMessages() {
        if (this.state.selectedChannel) {
            await this.loadMessages(this.state.selectedChannel.id);
        }
    }

    onFileSelect(ev) {
        const file = ev.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            this.state.pendingFile = {
                name: file.name,
                type: file.type,
                size: file.size,
                dataUrl: e.target.result,
                data: e.target.result.split(',')[1]
            };
        };
        reader.readAsDataURL(file);
        ev.target.value = ""; // reset input
    }
    
    removePendingFile() {
        this.state.pendingFile = null;
    }

    async sendMessage() {
        if ((!this.state.newMessage.trim() && !this.state.pendingFile) || !this.state.selectedChannel) return;
        
        let attachment_ids = [];
        if (this.state.pendingFile) {
            const attachment = await this.orm.call("ir.attachment", "create", [{
                name: this.state.pendingFile.name,
                type: 'binary',
                datas: this.state.pendingFile.data,
                res_model: "discuss.channel",
                res_id: this.state.selectedChannel.id,
            }]);
            
            if (Array.isArray(attachment)) {
                attachment_ids = attachment;
            } else {
                attachment_ids = [attachment];
            }
        }
        
        await this.orm.call(
            "discuss.channel",
            "message_post",
            [this.state.selectedChannel.id],
            {
                body: this.state.newMessage,
                message_type: "whatsapp_message",
                subtype_xmlid: "mail.mt_comment",
                attachment_ids: attachment_ids
            }
        );
        
        this.state.newMessage = "";
        this.state.pendingFile = null;
        await this.loadMessages();
        this.scrollToBottom();
    }
    
    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    openCatalogue() {
        this.state.showCatalogue = true;
    }

    closeCatalogue() {
        this.state.showCatalogue = false;
    }

    selectProduct(product) {
        this.state.newMessage = `Check out this product: ${product.name} for $${product.list_price.toFixed(2)}`;
        this.closeCatalogue();
    }

    callCustomer() {
        if (this.state.selectedChannel && this.state.selectedChannel.customer_phone) {
            window.location.href = `tel:${this.state.selectedChannel.customer_phone}`;
        } else {
            console.warn("No phone number found for this customer.");
        }
    }

    openTemplatesModal() {
        this.state.showTemplatesModal = true;
    }

    closeTemplatesModal() {
        this.state.showTemplatesModal = false;
    }

    selectTemplate(tmpl) {
        let text = tmpl.body || "";
        this.state.newMessage = text.replace(/\{\{\d+\}\}/g, "");
        this.closeTemplatesModal();
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.messagesContainer.el) {
                this.messagesContainer.el.scrollTop = this.messagesContainer.el.scrollHeight;
            }
        }, 100);
    }
}

WhatsAppChatsAction.template = "whatsapp_web_chats.ChatsAction";

registry.category("actions").add("whatsapp_web_chats.chats_client_action", WhatsAppChatsAction);
