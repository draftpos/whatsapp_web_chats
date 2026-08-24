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
            isAccountDropdownOpen: false,
            isNewChatModalOpen: false,
            contacts: [],
            filteredContacts: [],
            selectedChannels: [],
            selectedMessages: [],
            selectedContacts: [],
            newNumberQuery: null,
            showContactInfo: false,
            contactMedia: [],
            isEditingContactName: false,
            editingContactNameValue: "",
            transferModalOpen: false,
            transferChannelId: null,
            transferDepartments: [],
            transferAgents: [],
            selectedTransferDeptId: null,
            selectedTransferAgentId: "any",
            showChatDropdownId: null,
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

    get isWithin24hWindow() {
        if (!this.state.selectedChannel) return false;
        
        // If it's a new chat, we must use a template
        if (this.state.selectedChannel.id === 'new' || this.state.selectedChannel.id === 'new_contact') return false;
        
        if (!this.state.messages || this.state.messages.length === 0) return false;
        
        // Find the last CUSTOMER message time
        let lastMessageTime = null;
        for (let i = this.state.messages.length - 1; i >= 0; i--) {
            const msg = this.state.messages[i];
            // Meta 24-hour window ONLY opens if the customer initiates/replies
            if (msg.isMe === false && msg.date) {
                lastMessageTime = msg.date;
                break;
            }
        }
        
        if (!lastMessageTime) return false;
        
        try {
            let msgDate;
            if (lastMessageTime.includes('T') && lastMessageTime.endsWith('Z')) {
                // It is already a valid ISO string from the backend (e.g. 2026-08-18T09:27:00Z)
                msgDate = new Date(lastMessageTime);
            } else {
                // It is a standard Odoo date string (e.g. 2026-08-18 09:27:00)
                const dateStr = lastMessageTime.replace(' ', 'T') + 'Z';
                msgDate = new Date(dateStr);
            }
            const now = new Date();
            const diffHours = (now - msgDate) / (1000 * 60 * 60);
            return diffHours <= 24;
        } catch (e) {
            return false;
        }
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

    toggleAccountDropdown() {
        this.state.isAccountDropdownOpen = !this.state.isAccountDropdownOpen;
    }

    async selectAccount(accountId) {
        this.state.selectedAccount = accountId.toString();
        this.state.isAccountDropdownOpen = false;
        await this.loadChannels();
    }

    async openNewChatModal() {
        this.state.isNewChatModalOpen = true;
        this.state.filteredContacts = [];
        try {
            const contacts = await this.orm.call(
                "whatsapp.account",
                "get_contacts_for_new_chat",
                []
            );
            this.state.contacts = contacts;
            this.state.filteredContacts = contacts;
        } catch (e) {
            console.error("Failed to load contacts for new chat", e);
        }
    }

    closeNewChatModal() {
        this.state.isNewChatModalOpen = false;
    }

    onContactSearch(ev) {
        const query = ev.target.value.toLowerCase();
        if (!query) {
            this.state.filteredContacts = this.state.contacts;
            this.state.newNumberQuery = null;
        } else {
            this.state.filteredContacts = this.state.contacts.filter(c => 
                (c.name && c.name.toLowerCase().includes(query)) ||
                (c.phone && c.phone.toLowerCase().includes(query)) ||
                (c.mobile && c.mobile.toLowerCase().includes(query))
            );
            
            const isNumber = /^\+?\d+$/.test(query.replace(/\s+/g, ''));
            if (isNumber) {
                this.state.newNumberQuery = query;
            } else {
                this.state.newNumberQuery = null;
            }
        }
    }

    async startChatWithNumber(number) {
        if (!this.state.selectedAccount) return;
        
        try {
            const result = await this.orm.call(
                "whatsapp.account",
                "create_chat_from_number",
                [number, parseInt(this.state.selectedAccount)]
            );
            
            if (result.success && result.channel_id) {
                this.closeNewChatModal();
                await this.loadChannels();
                
                const newChannel = this.state.channels.find(c => c.id === result.channel_id);
                if (newChannel) {
                    await this.selectChannel(newChannel);
                }
            } else {
                console.error("Failed to start chat with number:", result.error);
                alert("Failed to start chat: " + (result.error || "Unknown error"));
            }
        } catch (e) {
            console.error("Failed to start new chat", e);
        }
    }

    async startNewChat(partnerId) {
        if (!this.state.selectedAccount) return;
        
        try {
            const result = await this.orm.call(
                "whatsapp.account",
                "get_or_create_whatsapp_chat",
                [partnerId, parseInt(this.state.selectedAccount)]
            );
            
            if (result.success && result.channel_id) {
                this.closeNewChatModal();
                await this.loadChannels();
                
                // Select the new channel
                const newChannel = this.state.channels.find(c => c.id === result.channel_id);
                if (newChannel) {
                    await this.selectChannel(newChannel);
                }
            }
        } catch (e) {
            console.error("Failed to start new chat", e);
        }
    }

    async loadChannels() {
        if (!this.myPartnerId) {
            try {
                // Attempt to get the current user's partner ID directly from the server
                const user_data = await this.orm.call("res.users", "read", [session.uid || session.user_context?.uid || 2], { fields: ["partner_id"] });
                if (user_data && user_data.length > 0 && user_data[0].partner_id) {
                    this.myPartnerId = user_data[0].partner_id[0];
                }
            } catch (e) {
                console.warn("Could not load myPartnerId", e);
            }
        }
        
        if (this.state.accounts.length === 0) {
            this.state.accounts = await this.orm.searchRead("whatsapp.account", [], ["id", "name", "image_1920", "wa_bot_active"]);
            if (this.state.accounts.length > 0) {
                this.state.selectedAccount = this.state.accounts[0].id.toString();
            }
        }

        const domain = [["channel_type", "=", "whatsapp"]];
        if (this.state.selectedAccount) {
            domain.push(["wa_account_id", "=", parseInt(this.state.selectedAccount)]);
        }

        const channels = await this.orm.call(
            "whatsapp.account",
            "get_whatsapp_web_channels",
            [],
            { wa_account_id: this.state.selectedAccount }
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
        
        // Do NOT fallback to all channels — this causes ghost chats to appear.
        // If no WhatsApp channels exist, simply show an empty list.


        
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
        
        // Filter out ghost/empty channels that have no partner and no phone number
        const validChannels = channels.filter(c => c.whatsapp_partner_id || c.whatsapp_number || c.name);
        this.state.channels = validChannels;
        if (channels.length > 0) {
            if (!this.state.selectedChannel) {
                this.selectChannel(channels[0]);
            } else {
                const currentId = this.state.selectedChannel.id;
                const updated = channels.find(c => c.id === currentId);
                if (updated) {
                    this.state.selectedChannel = updated;
                } else {
                    this.state.selectedChannel = null;
                }
            }
        } else {
            this.state.selectedChannel = null;
        }
    }

    async changeChatAccount(ev) {
        if (!this.state.selectedChannel) return;
        const newAccountId = parseInt(ev.target.value);
        this.state.selectedChannel.wa_account_id = newAccountId;
        // The UI updates automatically via reactivity.
        // We could also attempt to update the backend channel record here if needed.
    }

    async selectChannel(channel, event) {
        if (event && this.state.selectedChannels.length > 0) {
            this.toggleChannelSelection(channel.id, event);
            return;
        }

        this.state.selectedChannel = channel;
        this.state.selectedMessages = [];
        
        // Fetch media for the channel if the panel is open
        if (this.state.showContactInfo) {
            this.fetchContactMedia(channel.id);
        }
        
        try {
            await this.orm.call("whatsapp.account", "mark_whatsapp_web_messages_read", [channel.id]);
        } catch (e) {
            console.warn("Failed to mark messages as read", e);
        }
        // Mark as read locally immediately for responsiveness
        channel.unread_count = 0;
        
        await this.loadMessages(channel.id);
    }

    toggleChannelSelection(channelId, event) {
        if (event) {
            event.stopPropagation();
        }
        const idx = this.state.selectedChannels.indexOf(channelId);
        if (idx === -1) {
            this.state.selectedChannels.push(channelId);
        } else {
            this.state.selectedChannels.splice(idx, 1);
        }
    }

    toggleMessageSelection(messageId, event) {
        if (event) {
            event.stopPropagation();
        }
        const idx = this.state.selectedMessages.indexOf(messageId);
        if (idx === -1) {
            this.state.selectedMessages.push(messageId);
        } else {
            this.state.selectedMessages.splice(idx, 1);
        }
    }

    toggleContactSelection(contactId, event) {
        if (event) {
            event.stopPropagation();
        }
        const idx = this.state.selectedContacts.indexOf(contactId);
        if (idx === -1) {
            this.state.selectedContacts.push(contactId);
        } else {
            this.state.selectedContacts.splice(idx, 1);
        }
    }

    async deleteSelectedChannels() {
        if (this.state.selectedChannels.length === 0) return;
        if (!confirm(`Are you sure you want to permanently delete ${this.state.selectedChannels.length} chat(s) and all their messages?`)) return;

        try {
            for (const channelId of this.state.selectedChannels) {
                await this.orm.call("whatsapp.account", "delete_whatsapp_chat", [channelId]);
                if (this.state.selectedChannel && this.state.selectedChannel.id === channelId) {
                    this.state.selectedChannel = null;
                    this.state.messages = [];
                }
            }
            this.state.selectedChannels = [];
            await this.loadChannels();
        } catch (e) {
            console.error("Failed to delete selected chats", e);
            alert("Failed to delete some chats.");
        }
    }

    async deleteSelectedMessages() {
        if (this.state.selectedMessages.length === 0) return;
        if (!confirm(`Are you sure you want to permanently delete ${this.state.selectedMessages.length} message(s)?`)) return;

        try {
            for (const messageId of this.state.selectedMessages) {
                await this.orm.call("whatsapp.account", "delete_whatsapp_message", [messageId]);
            }
            this.state.selectedMessages = [];
            await this.loadMessages();
        } catch (e) {
            console.error("Failed to delete selected messages", e);
            alert("Failed to delete some messages.");
        }
    }

    async deleteSelectedContacts() {
        if (this.state.selectedContacts.length === 0) return;
        if (!confirm(`Are you sure you want to permanently delete ${this.state.selectedContacts.length} contact(s)?`)) return;

        try {
            await this.orm.call("res.partner", "unlink", [this.state.selectedContacts]);
            this.state.selectedContacts = [];
            // refresh contacts
            const contacts = await this.orm.call(
                "whatsapp.account",
                "get_contacts_for_new_chat",
                []
            );
            this.state.contacts = contacts;
            this.state.filteredContacts = contacts;
        } catch (e) {
            console.error("Failed to delete selected contacts", e);
            alert("Failed to delete some contacts.");
        }
    }

    async loadMessages(channelId = null) {
        const id = channelId || (this.state.selectedChannel ? this.state.selectedChannel.id : null);
        if (!id) return;
        try {
            const messages = await this.orm.call(
                "whatsapp.account",
                "get_whatsapp_web_messages",
                [id]
            );
            
            this.state.messages = messages.map(msg => {
                let isMe = msg.is_me !== undefined ? msg.is_me : false;
                
                // Fallback for older messages or if is_me is missing
                if (msg.is_me === undefined) {
                    if (msg.author_id) {
                        let authorName = (msg.author_id[1] || "").toLowerCase();
                        if (this.myPartnerId && msg.author_id[0] === this.myPartnerId) {
                            isMe = true;
                        } else if (authorName.includes("bot") || authorName === "odoobot" || authorName === "system") {
                            isMe = true;
                        }
                    }
                    
                    let rawBody = msg.body || "";
                    if (rawBody.includes(">Bot: ") || rawBody.startsWith("Bot: ")) {
                        isMe = true;
                    } else if (rawBody.includes(">Customer: ") || rawBody.startsWith("Customer: ")) {
                        isMe = false;
                    }
                }
                
                let tmp = document.createElement("DIV");
                tmp.innerHTML = msg.body || "";
                let bodyText = tmp.textContent || tmp.innerText || "";
                
                // --- Menu Detection Logic ---
                let isMenu = false;
                let menuTitle = "";
                let menuOptions = [];
                let lines = bodyText.trim().split('\n');
                let optLines = [];
                let txtLines = [];
                
                for (let line of lines) {
                    if (/^\d+\.\s+(.+)$/.test(line.trim())) {
                        optLines.push(line.trim());
                    } else if (line.trim() !== '') {
                        txtLines.push(line.trim());
                    }
                }
                
                if (optLines.length >= 2 && txtLines.length > 0) {
                    isMenu = true;
                    menuTitle = txtLines.join('\n');
                    menuOptions = optLines.map(opt => {
                        let match = opt.match(/^\d+\.\s+(.+)$/);
                        return match ? match[1] : opt;
                    });
                }
                // --- End Menu Detection ---
                
                let timeText = '';
                if (msg.date) {
                    try {
                        const dt = new Date(msg.date);
                        timeText = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                    } catch (e) {
                        timeText = msg.date;
                    }
                }
                
                let authorName = "";
                if (msg.author_id && Array.isArray(msg.author_id) && msg.author_id.length > 1) {
                    authorName = msg.author_id[1];
                    let authorLower = authorName.toLowerCase();
                    if (authorLower.includes("bot") || authorLower === "system") {
                        authorName = "Bot";
                    }
                }
                
                return { ...msg, isMe, bodyText, timeText, authorName, isMenu, menuTitle, menuOptions };
            });
            
            // Check for newly failed messages and alert the user
            window.seenWaErrors = window.seenWaErrors || new Set();
            for (const msg of this.state.messages) {
                if (msg.wa_error) {
                    const errorId = msg.wa_error_msg_id || msg.id;
                    if (!window.seenWaErrors.has(errorId)) {
                        window.seenWaErrors.add(errorId);
                        
                        // Only alert if the message was sent recently (last 2 mins)
                        // so we don't spam alerts for old errors on page reload
                        try {
                            const msgDate = new Date(msg.date ? (msg.date.includes('T') ? msg.date : msg.date.replace(' ', 'T') + 'Z') : 0);
                            const diffMins = (new Date() - msgDate) / 60000;
                            if (diffMins < 2) {
                                alert("WhatsApp Delivery Failed:\n\n" + msg.wa_error);
                            }
                        } catch(e) {}
                    }
                }
            }
            
            this.scrollToBottom();
        } catch(e) {
            console.error("Failed to load messages:", e);
        }
    }
    
    formatChatTime(isoStr) {
        if (!isoStr) return '';
        try {
            const dt = new Date(isoStr);
            const now = new Date();
            const isToday = dt.toDateString() === now.toDateString();
            if (isToday) {
                return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
            } else {
                return dt.toLocaleDateString([], { day: '2-digit', month: '2-digit', year: '2-digit' });
            }
        } catch (e) {
            return '';
        }
    }

    async pollMessages() {
        // Only reload channels in background to check for NEW channels/messages
        // but do NOT call loadChannels() as it overwrites locally-cleared unread counts.
        // Instead, fetch fresh channel data and merge carefully.
        try {
            const freshChannels = await this.orm.call(
                "whatsapp.account",
                "get_whatsapp_web_channels",
                [],
                { wa_account_id: this.state.selectedAccount }
            );

            if (freshChannels && this.myPartnerId) {
                const members = await this.orm.searchRead(
                    "discuss.channel.member",
                    [["partner_id", "=", this.myPartnerId], ["channel_id", "in", freshChannels.map(c => c.id)]],
                    ["channel_id", "message_unread_counter"]
                );
                const unreadMap = {};
                for (const m of members) {
                    if (m.channel_id && m.channel_id[0]) {
                        unreadMap[m.channel_id[0]] = m.message_unread_counter;
                    }
                }
                for (const c of freshChannels) {
                    c.unread_count = unreadMap[c.id] || 0;
                }
            }

            // Filter ghost channels
            const validFresh = (freshChannels || []).filter(c => c.whatsapp_partner_id || c.whatsapp_number || c.name);
            validFresh.sort((a, b) => (b.write_date || '').localeCompare(a.write_date || ''));
            this.state.channels = validFresh;

            // Keep selected channel in sync
            if (this.state.selectedChannel) {
                const found = validFresh.find(c => c.id === this.state.selectedChannel.id);
                if (found) {
                    found.unread_count = 0; // always keep selected as read
                    this.state.selectedChannel = found;
                }
            }
        } catch(e) {
            console.warn("Poll error", e);
        }

        // Reload messages for the current open chat
        if (this.state.selectedChannel) {
            try {
                await this.loadMessages(this.state.selectedChannel.id);
            } catch(e) {
                console.warn("Failed to reload messages in poll:", e);
            }
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

    async sendMenuReply(optionText) {
        this.state.newMessage = optionText;
        await this.sendMessage();
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
        // Small delay to allow Odoo to commit the message before fetching
        await new Promise(resolve => setTimeout(resolve, 400));
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
    
    async onBotToggle(ev) {
        const active = ev.target.checked;
        const accountId = this.state.selectedAccount;
        await this.toggleAccountBot(accountId, active);
    }
    
    async toggleAccountBot(accountId, active) {
        await this.orm.call("whatsapp.account", "toggle_account_bot", [parseInt(accountId), active]);
        const account = this.state.accounts.find(a => a.id.toString() === accountId.toString());
        if (account) {
            account.wa_bot_active = active;
        }
    }

    openTemplatesModal() {
        this.state.showTemplatesModal = true;
    }

    closeTemplatesModal() {
        this.state.showTemplatesModal = false;
    }
    
    async toggleContactInfo() {
        this.state.showContactInfo = !this.state.showContactInfo;
        if (this.state.showContactInfo && this.state.selectedChannel) {
            await this.fetchContactMedia(this.state.selectedChannel.id);
        }
    }
    
    async fetchContactMedia(channelId) {
        try {
            const domain = [
                ["res_model", "=", "discuss.channel"],
                ["res_id", "=", channelId]
            ];
            const attachments = await this.orm.searchRead(
                "ir.attachment",
                domain,
                ["id", "name", "mimetype", "create_date"],
                { order: "id desc", limit: 50 }
            );
            this.state.contactMedia = attachments;
        } catch(e) {
            console.warn("Failed to fetch media", e);
            this.state.contactMedia = [];
        }
    }

    async selectTemplate(tmpl) {
        if (!this.state.selectedChannel) return;
        
        this.closeTemplatesModal();
        try {
            const result = await this.orm.call(
                "whatsapp.account",
                "send_whatsapp_template",
                [this.state.selectedChannel.id, tmpl.id]
            );
            
            if (result && result.success) {
                // Immediately add the rendered message to the chat so the user sees it
                const now = new Date();
                const timeText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                const sentDate = result.sent_date || now.toISOString().slice(0, 19).replace('T', ' ');
                const renderedBody = result.body || `[Template: ${tmpl.template_name}]`;
                
                this.state.messages = [...this.state.messages, {
                    id: `temp_${Date.now()}`,
                    body: renderedBody,
                    bodyText: renderedBody,
                    isMe: true,
                    timeText: timeText,
                    date: sentDate,
                    attachment_ids: [],
                }];
                this.scrollToBottom();
                
                // Also reload from server after a short delay to get the real message IDs
                await new Promise(resolve => setTimeout(resolve, 1500));
                await this.loadMessages(this.state.selectedChannel.id);
                this.scrollToBottom();
            } else {
                console.error("Failed to send template:", result.error);
                alert("Failed to send template: " + (result.error || "Unknown error"));
            }
        } catch (e) {
            console.error("Error sending template:", e);
            alert("Error sending template: " + e.message);
        }
    }

    async deleteChat(channelId) {
        if (!confirm("Are you sure you want to completely delete this chat and all its messages?")) {
            return;
        }
        
        const result = await this.orm.call("whatsapp.account", "delete_whatsapp_chat", [parseInt(channelId)]);
        if (result && result.success) {
            // Remove from state
            this.state.channels = this.state.channels.filter(c => c.id !== channelId);
            if (this.state.selectedChannel && this.state.selectedChannel.id === channelId) {
                this.state.selectedChannel = null;
                this.state.messages = [];
            }
        } else {
            console.error("Failed to delete chat", result);
            alert("Failed to delete chat: " + (result.error || "Unknown error"));
        }
    }
    
    async deleteMessage(messageId) {
        if (!confirm("Delete this message?")) {
            return;
        }
        
        const result = await this.orm.call("whatsapp.account", "delete_whatsapp_message", [parseInt(messageId)]);
        if (result && result.success) {
            // Remove from state
            this.state.messages = this.state.messages.filter(m => m.id !== messageId);
            // Optionally, update the chat preview if it was the last message
            if (this.state.selectedChannel && this.state.messages.length > 0) {
                this.state.selectedChannel.last_message_preview = this.state.messages[this.state.messages.length - 1].body;
            } else if (this.state.selectedChannel) {
                this.state.selectedChannel.last_message_preview = "";
            }
        } else {
            console.error("Failed to delete message", result);
            alert("Failed to delete message: " + (result.error || "Unknown error"));
        }
    }

    toggleEditContactName() {
        this.state.isEditingContactName = !this.state.isEditingContactName;
        if (this.state.isEditingContactName && this.state.selectedChannel) {
            this.state.editingContactNameValue = this.state.selectedChannel.name || "";
        }
    }

    onContactNameKeydown(ev) {
        if (ev.key === 'Enter') {
            this.saveContactName();
        } else if (ev.key === 'Escape') {
            this.toggleEditContactName();
        }
    }

    async saveContactName() {
        if (!this.state.selectedChannel || !this.state.editingContactNameValue) return;
        
        const newName = this.state.editingContactNameValue.trim();
        if (!newName) return;

        try {
            const result = await this.orm.call("whatsapp.account", "update_contact_name", [this.state.selectedChannel.id, newName]);
            if (result && result.success) {
                this.state.selectedChannel.name = newName;
                this.state.isEditingContactName = false;
                
                // Update in the channels list
                const channelIndex = this.state.channels.findIndex(c => c.id === this.state.selectedChannel.id);
                if (channelIndex !== -1) {
                    this.state.channels[channelIndex].name = newName;
                }
            } else {
                alert("Failed to update name: " + (result ? result.error : "Unknown error"));
            }
        } catch (e) {
            console.error("Error updating name", e);
            alert("Error updating name: " + e.message);
        }
    }

    async openTransferModal(channelId, ev) {
        if (ev) {
            ev.stopPropagation();
        }
        this.state.transferChannelId = channelId;
        this.state.transferModalOpen = true;
        this.state.showChatDropdownId = null;
        
        try {
            const depts = await this.orm.searchRead("hr.department", [], ["id", "name"]);
            this.state.transferDepartments = depts;
            this.state.selectedTransferDeptId = null;
            this.state.transferAgents = [];
            this.state.selectedTransferAgentId = "any";
        } catch (e) {
            console.error("Failed to load departments", e);
        }
    }
    
    closeTransferModal() {
        this.state.transferModalOpen = false;
        this.state.transferChannelId = null;
    }
    
    async onTransferDeptChange(ev) {
        const deptId = parseInt(ev.target.value);
        this.state.selectedTransferDeptId = deptId;
        this.state.selectedTransferAgentId = "any";
        
        if (deptId) {
            try {
                const agents = await this.orm.searchRead("res.users", [["wa_department", "=", deptId]], ["id", "name"]);
                this.state.transferAgents = agents;
            } catch (e) {
                console.error("Failed to load agents", e);
                this.state.transferAgents = [];
            }
        } else {
            this.state.transferAgents = [];
        }
    }
    
    async submitTransfer() {
        if (!this.state.transferChannelId || !this.state.selectedTransferDeptId) {
            alert("Please select a department.");
            return;
        }
        
        const agentId = this.state.selectedTransferAgentId === "any" ? false : parseInt(this.state.selectedTransferAgentId);
        
        try {
            const result = await this.orm.call("discuss.channel", "transfer_whatsapp_chat", [
                this.state.transferChannelId,
                this.state.selectedTransferDeptId,
                agentId
            ]);
            
            if (result) {
                this.closeTransferModal();
                // Optionally reload channels or messages if it's the active one
                await this.loadChannels();
            } else {
                alert("Failed to transfer chat.");
            }
        } catch (e) {
            console.error("Transfer error", e);
            alert("Error transferring chat.");
        }
    }
    
    toggleChatDropdown(channelId, ev) {
        if (ev) ev.stopPropagation();
        if (this.state.showChatDropdownId === channelId) {
            this.state.showChatDropdownId = null;
        } else {
            this.state.showChatDropdownId = channelId;
        }
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
