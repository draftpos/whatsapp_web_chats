/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillDestroy, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class WhatsAppChatsAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.messagesContainer = useRef("messagesContainer");
        this.chatList = useRef("chatList");
        
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
            chatFilter: "all",
            showLabels: true,
            availableTags: [],
            fullscreenMedia: null, // {id: att_id, type: 'image' | 'video'}
            isRecording: false,
            recordingSeconds: 0,
            recordingBlob: null,
            recordingBlobUrl: null,
        });
        
        this.myPartnerId = null;

        onWillStart(async () => {
            await this.loadChannels();
            await this.loadProducts();
            await this.loadTemplates();
            await this.loadTags();
        });
        
        onMounted(() => {
            this.pollInterval = setInterval(() => {
                this.pollMessages();
            }, 5000);

            // Close chat dropdown when clicking anywhere outside it
            this._onDocumentClick = (ev) => {
                if (this.state.showChatDropdownId !== null) {
                    const menu = document.querySelector('.chat-dropdown-menu');
                    const btn = document.querySelector('.chat-dropdown-btn');
                    if (menu && !menu.contains(ev.target) && btn && !btn.contains(ev.target)) {
                        this.state.showChatDropdownId = null;
                    } else if (!menu) {
                        this.state.showChatDropdownId = null;
                    }
                }
            };
            document.addEventListener('click', this._onDocumentClick, true);

            // Close chat dropdown when the chat list is scrolled
            this._onChatListScroll = () => {
                if (this.state.showChatDropdownId !== null) {
                    this.state.showChatDropdownId = null;
                }
            };
            if (this.chatList.el) {
                this.chatList.el.addEventListener('scroll', this._onChatListScroll);
            }
        });
        
        onWillDestroy(() => {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
            }
            if (this._onDocumentClick) {
                document.removeEventListener('click', this._onDocumentClick, true);
            }
            if (this._onChatListScroll && this.chatList.el) {
                this.chatList.el.removeEventListener('scroll', this._onChatListScroll);
            }
        });
    }

    async loadTags() {
        try {
            this.state.availableTags = await this.orm.call("whatsapp.account", "get_all_chat_tags", []);
        } catch (e) {
            console.error("Failed to load tags", e);
        }
    }

    async toggleChatTag(channelId, tagId, ev) {
        if (ev) ev.stopPropagation();
        // Close dropdown immediately after action
        this.state.showChatDropdownId = null;
        
        const channel = this.state.channels.find(c => c.id === channelId);
        if (!channel) return;
        
        if (!channel.wa_tags) channel.wa_tags = [];
        const hasTag = channel.wa_tags.some(t => t.id === tagId);
        
        if (hasTag) {
            channel.wa_tags = channel.wa_tags.filter(t => t.id !== tagId);
        } else {
            const tagDef = this.state.availableTags.find(t => t.id === tagId);
            if (tagDef) channel.wa_tags.push(tagDef);
        }
        
        try {
            await this.orm.call("whatsapp.account", "update_chat_tags", [channelId, channel.wa_tags.map(t => t.id)]);
        } catch (e) {
            console.error("Failed to update tags", e);
            this.loadChannels();
        }
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

    async openProfileSettings() {
        this.state.isProfileModalOpen = true;
        this.state.profileData = null;
        if (this.state.selectedAccount) {
            try {
                this.state.profileData = await this.orm.call(
                    "whatsapp.account",
                    "get_profile_settings",
                    [parseInt(this.state.selectedAccount)]
                );
            } catch (e) {
                console.error("Failed to fetch profile settings", e);
            }
        }
    }

    closeProfileSettings() {
        this.state.isProfileModalOpen = false;
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

        const response = await this.orm.call(
            "whatsapp.account",
            "get_whatsapp_web_channels",
            [],
            { wa_account_id: this.state.selectedAccount }
        );
        const channels = response.channels || [];
        this.state.showLabels = response.show_labels;
        
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
        validChannels.sort((a, b) => (b.write_date || '').localeCompare(a.write_date || ''));
        this.state.channels = validChannels;
        if (channels.length > 0) {
            if (this.state.selectedChannel) {
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

    async setChatState(channelId, field, value, ev) {
        if (ev) {
            ev.stopPropagation();
        }
        // Close dropdown immediately after action
        this.state.showChatDropdownId = null;
        try {
            await this.orm.call(
                "whatsapp.account",
                "set_whatsapp_chat_state",
                [channelId, field, value]
            );
            // Update local state
            const channel = this.state.channels.find(c => c.id === channelId);
            if (channel) {
                channel[field] = value;
                if (field === 'wa_is_done' && value) {
                    channel.wa_is_unread_global = false;
                }
            }
        } catch (e) {
            console.error("Failed to update chat state", e);
        }
    }

    setChatFilter(filterType) {
        this.state.chatFilter = filterType;
    }

    get filteredChannels() {
        if (!this.state.channels) return [];
        let filtered = this.state.channels;
        
        switch (this.state.chatFilter) {
            case 'unread':
                filtered = filtered.filter(c => c.wa_is_unread_global || (c.unread_count && c.unread_count > 0));
                break;
            case 'favourites':
                filtered = filtered.filter(c => c.wa_is_favourite);
                break;
            case 'done':
                filtered = filtered.filter(c => c.wa_is_done);
                break;
            case 'all':
            default:
                break;
        }
        
        return filtered;
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
        channel.wa_is_unread_global = false;
        
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
                let isSystem = msg.message_type === 'notification';
                
                let timeText = '';
                if (msg.date) {
                    try {
                        const dt = new Date(msg.date);
                        if (isNaN(dt)) {
                            timeText = msg.date;
                        } else {
                            timeText = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                        }
                    } catch (e) {
                        timeText = msg.date;
                    }
                }
                                let authorName = "";
                if (msg.author_id) {
                    authorName = msg.author_id[1];
                    let authorLower = authorName.toLowerCase();
                    if (authorLower.includes("bot") || authorLower === "odoobot" || authorLower === "system") {
                        authorName = "Bot";
                    }
                } else if (!isMe && this.state.selectedChannel) {
                    authorName = this.state.selectedChannel.name || "Customer";
                }
                
                return { ...msg, isMe, bodyText, timeText, authorName, isMenu, menuTitle, menuOptions, isSystem };
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
            if (this.state.selectedChannel && this.state.messages.length > 0) {
                const lastMsg = this.state.messages[this.state.messages.length - 1];
                let previewText = lastMsg.bodyText || "";
                if (!previewText.trim() && lastMsg.attachment_ids && lastMsg.attachment_ids.length > 0) {
                    previewText = "Attachment";
                }
                const timeStr = lastMsg.date ? lastMsg.date.replace(' ', 'T') + 'Z' : '';
                
                this.state.selectedChannel.last_message_preview = previewText;
                this.state.selectedChannel.last_message_body = previewText;
                this.state.selectedChannel.last_message_time = timeStr;
                
                const chanInList = this.state.channels.find(c => c.id === this.state.selectedChannel.id);
                if (chanInList) {
                    chanInList.last_message_preview = previewText;
                    chanInList.last_message_body = previewText;
                    chanInList.last_message_time = timeStr;
                }
            } else if (this.state.selectedChannel) {
                this.state.selectedChannel.last_message_preview = "";
                this.state.selectedChannel.last_message_body = "";
                const chanInList = this.state.channels.find(c => c.id === this.state.selectedChannel.id);
                if (chanInList) {
                    chanInList.last_message_preview = "";
                    chanInList.last_message_body = "";
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
                if (isNaN(dt)) return '';
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
    
    openMedia(attId, ev, type='image', filename='') {
        if (ev) ev.stopPropagation();
        this.state.fullscreenMedia = {
            id: attId,
            type: type,
            filename: filename || '',
            scale: 1,
            translateX: 0,
            translateY: 0,
        };
        // Bind drag handlers (stored so we can remove them)
        this._lbDragging = false;
        this._lbDragStartX = 0;
        this._lbDragStartY = 0;
        this._lbDragOriginX = 0;
        this._lbDragOriginY = 0;
    }
    
    closeMedia() {
        this.state.fullscreenMedia = null;
        this._lbDragging = false;
    }
    
    zoomIn(ev) {
        if (ev) ev.stopPropagation();
        if (!this.state.fullscreenMedia) return;
        let scale = this.state.fullscreenMedia.scale + 0.25;
        if (scale > 5) scale = 5;
        this.state.fullscreenMedia = { ...this.state.fullscreenMedia, scale };
    }

    zoomOut(ev) {
        if (ev) ev.stopPropagation();
        if (!this.state.fullscreenMedia) return;
        let scale = this.state.fullscreenMedia.scale - 0.25;
        if (scale < 0.25) scale = 0.25;
        // Reset pan if zoomed out to 1 or below
        const translateX = scale <= 1 ? 0 : this.state.fullscreenMedia.translateX;
        const translateY = scale <= 1 ? 0 : this.state.fullscreenMedia.translateY;
        this.state.fullscreenMedia = { ...this.state.fullscreenMedia, scale, translateX, translateY };
    }

    resetZoom(ev) {
        if (ev) ev.stopPropagation();
        if (!this.state.fullscreenMedia) return;
        this.state.fullscreenMedia = { ...this.state.fullscreenMedia, scale: 1, translateX: 0, translateY: 0 };
    }
    
    handleMediaWheel(ev) {
        if (!this.state.fullscreenMedia || this.state.fullscreenMedia.type !== 'image') return;
        ev.preventDefault();
        
        let scale = this.state.fullscreenMedia.scale;
        const delta = ev.deltaY < 0 ? 0.15 : -0.15;
        scale += delta;
        
        if (scale < 0.25) scale = 0.25;
        if (scale > 5) scale = 5;
        
        const translateX = scale <= 1 ? 0 : this.state.fullscreenMedia.translateX;
        const translateY = scale <= 1 ? 0 : this.state.fullscreenMedia.translateY;
        this.state.fullscreenMedia = { ...this.state.fullscreenMedia, scale, translateX, translateY };
    }

    startMediaDrag(ev) {
        if (!this.state.fullscreenMedia || this.state.fullscreenMedia.type !== 'image') return;
        if (this.state.fullscreenMedia.scale <= 1) return;
        ev.preventDefault();
        this._lbDragging = true;
        this._lbDragStartX = ev.clientX;
        this._lbDragStartY = ev.clientY;
        this._lbDragOriginX = this.state.fullscreenMedia.translateX;
        this._lbDragOriginY = this.state.fullscreenMedia.translateY;
    }

    onMediaDrag(ev) {
        if (!this._lbDragging || !this.state.fullscreenMedia) return;
        const dx = ev.clientX - this._lbDragStartX;
        const dy = ev.clientY - this._lbDragStartY;
        this.state.fullscreenMedia = {
            ...this.state.fullscreenMedia,
            translateX: this._lbDragOriginX + dx,
            translateY: this._lbDragOriginY + dy,
        };
    }

    stopMediaDrag(ev) {
        this._lbDragging = false;
    }

    getMediaDownloadUrl() {
        if (!this.state.fullscreenMedia) return '#';
        if (this.state.fullscreenMedia.type === 'video') {
            return `/web/content/${this.state.fullscreenMedia.id}?download=true`;
        }
        return `/web/image/${this.state.fullscreenMedia.id}?download=true`;
    }

    getZoomPercent() {
        if (!this.state.fullscreenMedia) return '100%';
        return Math.round(this.state.fullscreenMedia.scale * 100) + '%';
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

        this.state.pendingFile = {
            name: file.name,
            type: file.type,
            size: file.size,
            file: file,
            dataUrl: URL.createObjectURL(file)
        };
        ev.target.value = ""; // reset input
    }
    
    removePendingFile() {
        this.state.pendingFile = null;
    }

    async startRecording() {
        if (this.state.isRecording) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this._mediaStream = stream;
            this._audioChunks = [];

            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
                    ? 'audio/ogg;codecs=opus'
                    : 'audio/webm';

            this._mediaRecorder = new MediaRecorder(stream, { mimeType });
            this._mediaRecorder.ondataavailable = (ev) => {
                if (ev.data && ev.data.size > 0) {
                    this._audioChunks.push(ev.data);
                }
            };
            this._mediaRecorder.onstop = () => {
                const blob = new Blob(this._audioChunks, { type: mimeType });
                const url = URL.createObjectURL(blob);
                this.state.recordingBlob = blob;
                this.state.recordingBlobUrl = url;
                this.state.isRecording = false;
                clearInterval(this._recordingTimer);
            };

            this._mediaRecorder.start();
            this.state.isRecording = true;
            this.state.recordingSeconds = 0;
            this.state.recordingBlob = null;
            this.state.recordingBlobUrl = null;
            this._recordingTimer = setInterval(() => {
                this.state.recordingSeconds++;
            }, 1000);
        } catch (e) {
            console.error('Microphone access denied or error:', e);
            alert('Could not access microphone. Please allow microphone access and try again.');
        }
    }

    stopRecording() {
        if (this._mediaRecorder && this._mediaRecorder.state !== 'inactive') {
            this._mediaRecorder.stop();
        }
        if (this._mediaStream) {
            this._mediaStream.getTracks().forEach(t => t.stop());
            this._mediaStream = null;
        }
        clearInterval(this._recordingTimer);
        this.state.isRecording = false;
    }

    cancelRecording() {
        this.stopRecording();
        this.state.recordingBlob = null;
        this.state.recordingBlobUrl = null;
        this.state.recordingSeconds = 0;
    }

    formatRecordingTime(seconds) {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }

    async sendAudioMessage() {
        if (!this.state.recordingBlob || !this.state.selectedChannel) return;
        const blob = this.state.recordingBlob;
        const ext = blob.type.includes('ogg') ? 'ogg' : 'webm';
        const filename = `voice_${Date.now()}.${ext}`;

        try {
            const formData = new window.FormData();
            formData.append('csrf_token', window.odoo?.csrf_token || '');
            formData.append('name', filename);
            formData.append('ufile', blob, filename);
            formData.append('model', 'discuss.channel');
            formData.append('id', this.state.selectedChannel.id);

            const response = await window.fetch('/web/binary/upload_attachment', {
                method: 'POST',
                body: formData,
            });
            const responseText = await response.text();
            let attachmentId = null;
            const match = responseText.match(/\[.*?\]|\{.*?\}/);
            if (match) {
                const result = JSON.parse(match[0]);
                if (Array.isArray(result) && result.length > 0) {
                    attachmentId = result[0].id;
                } else if (result.id) {
                    attachmentId = result.id;
                }
            }

            if (!attachmentId) {
                throw new Error("Failed to parse attachment ID");
            }

            await this.orm.call(
                'discuss.channel',
                'message_post',
                [this.state.selectedChannel.id],
                {
                    body: '',
                    message_type: 'whatsapp_message',
                    subtype_xmlid: 'mail.mt_comment',
                    attachment_ids: Array.isArray(attachmentId) ? attachmentId : [attachmentId],
                }
            );

            this.state.recordingBlob = null;
            this.state.recordingBlobUrl = null;
            this.state.recordingSeconds = 0;
            await new Promise(resolve => setTimeout(resolve, 400));
            await this.loadMessages();
            this.scrollToBottom();
            await this.pollMessages();
        } catch (e) {
            console.error('Failed to send audio message:', e);
            alert('Failed to send voice message.');
        }
    }

    async sendMenuReply(optionText) {
        this.state.newMessage = optionText;
        await this.sendMessage();
    }

    async sendMessage() {
        if ((!this.state.newMessage.trim() && !this.state.pendingFile) || !this.state.selectedChannel) return;
        
        const messageBody = this.state.newMessage;
        const pendingFile = this.state.pendingFile;
        this.state.newMessage = "";
        this.state.pendingFile = null;

        let attachment_ids = [];
        if (pendingFile) {
            try {
                const formData = new window.FormData();
                formData.append('csrf_token', window.odoo?.csrf_token || '');
                formData.append('name', pendingFile.name);
                formData.append('ufile', pendingFile.file);
                formData.append('model', 'discuss.channel');
                formData.append('id', this.state.selectedChannel.id);

                const response = await window.fetch('/web/binary/upload_attachment', {
                    method: 'POST',
                    body: formData,
                });
                const responseText = await response.text();
                const match = responseText.match(/\[.*?\]|\{.*?\}/);
                if (match) {
                    const result = JSON.parse(match[0]);
                    if (Array.isArray(result)) {
                        attachment_ids = result.map(a => a.id);
                    } else if (result.id) {
                        attachment_ids = [result.id];
                    }
                }
            } catch (e) {
                console.error("Attachment upload failed", e);
            }
        }
        
        await this.orm.call(
            "discuss.channel",
            "message_post",
            [this.state.selectedChannel.id],
            {
                body: messageBody,
                message_type: "whatsapp_message",
                subtype_xmlid: "mail.mt_comment",
                attachment_ids: attachment_ids
            }
        );
        
        // Small delay to allow Odoo to commit the message before fetching
        await new Promise(resolve => setTimeout(resolve, 400));
        await this.loadMessages();
        this.scrollToBottom();
        await this.pollMessages();
    }
    
    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    onInputResize(ev) {
        const el = ev.target;
        el.style.height = 'auto';
        el.style.height = (el.scrollHeight) + 'px';
        if (el.scrollHeight > 150) {
            el.style.overflowY = 'auto';
        } else {
            el.style.overflowY = 'hidden';
        }
    }

    closeChat() {
        this.state.selectedChannel = null;
        this.state.messages = [];
        this.state.showContactInfo = false;
    }

    selectAllContacts() {
        if (!this.state.contacts) return;
        this.state.selectedContacts = this.state.contacts.map(c => c.id);
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

    openCatalogueModal() {
        this.state.showCatalogueModal = true;
    }

    closeCatalogueModal() {
        this.state.showCatalogueModal = false;
    }

    async sendProduct(product) {
        if (!this.state.selectedChannel) return;
        
        try {
            let attachment_ids = [];
            // If the product has an image, create an attachment for it
            if (product.image_128) {
                const attachmentId = await this.orm.create("ir.attachment", [{
                    name: product.name + ".jpg",
                    datas: product.image_128,
                    res_model: "discuss.channel",
                    res_id: this.state.selectedChannel.id,
                    type: "binary"
                }]);
                if (attachmentId && attachmentId.length > 0) {
                    attachment_ids.push(attachmentId[0]);
                }
            }
            
            const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
            // Fallback to simple price format if formatting fails, though this should work
            const price = product.list_price ? currencyFormatter.format(product.list_price) : '$0.00';
            const body = `📦 *${product.name}*\nPrice: ${price}`;
            
            await this.orm.call(
                "discuss.channel",
                "message_post",
                [this.state.selectedChannel.id],
                {
                    body: body,
                    message_type: "whatsapp_message",
                    subtype_xmlid: "mail.mt_comment",
                    attachment_ids: attachment_ids
                }
            );
            
            this.closeCatalogueModal();
            // Small delay to allow Odoo to commit the message before fetching
            await new Promise(resolve => setTimeout(resolve, 400));
            await this.loadMessages();
            this.scrollToBottom();
            await this.pollMessages();
        } catch (e) {
            console.error("Failed to send product message", e);
            alert("Failed to send the product catalogue message.");
        }
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
                    isSystem: false,
                    attachment_ids: [],
                }];
                this.scrollToBottom();
                
                // Also reload from server after a short delay to get the real message IDs
                await new Promise(resolve => setTimeout(resolve, 1500));
                await this.loadMessages(this.state.selectedChannel.id);
                this.scrollToBottom();
                await this.pollMessages();
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
