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
        this.messageCache = {};
        
        this.state = useState({
            channels: [],
            selectedChannel: null,
            messages: [],
            newMessage: "",
            pendingFiles: [],
            accounts: [],
            selectedAccount: null,
            products: [],
            showCatalogue: false,
            showAddProductModal: false,
            newProduct: null,
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
            contactLinks: [],
            contactMediaTab: 'media',
            showMediaTabsView: false,
            isEditingContactName: false,
            editingContactNameValue: "",
            transferModalOpen: false,
            agentsToTransfer: [],
            selectedAgentToTransfer: null,
            availableTags: [],
            showFilterDropdown: false,
            transferChannelId: null,
            transferDepartments: [],
            transferAgents: [],
            selectedTransferDeptId: null,
            selectedTransferAgentId: "any",
            showChatDropdownId: null,
            showHeaderDropdown: false,
            showMessageDropdownId: null,
            chatFilter: "all",
            showLabels: true,
            availableTags: [],
            fullscreenMedia: null, // {id: att_id, type: 'image' | 'video'}
            isRecording: false,
            recordingSeconds: 0,
            recordingBlob: null,
            recordingBlobUrl: null,
            isSending: false,
            chatSearch: "",
            deleteChatConfirmId: null,
            dropdownUpwards: false,
            replyingToMessage: null,
            showPlusMenu: false,
            showAttachMenu: false,
            // Quick Replies & Templates
            wa_quick_replies: [],
            quickReplyTab: 'quick',
            quickReplySearch: '',
            quickReplyFilter: 'all',
            showAddQuickReplyModal: false,
            newQuickReply: { shortcut: '', body: '' },
            // Emoji Picker
            emojiPickerMsgId: null,
            emojiPickerX: 0,
            emojiPickerY: 0,
            // Forward
            forwardMessageId: null,
            forwardSearch: '',
            // Disappearing Messages
            showDisappearingModal: false,
            // Deletion
            deleteMessageId: null,
            // Audio player
            activeAudioId: null,
            audioProgress: {},
            // Message editing
            editingMessageId: null,
            editingMessageOriginal: '',
            // Send Phone Number modal
            showPhoneModal: false,
            phoneModalName: '',
            phoneModalNumber: '',
            phoneModalSearch: '',
            phoneModalContacts: [],
        });
        
        this.myPartnerId = null;
        this.isAdmin = session.is_admin || session.is_superuser || false;

        onWillStart(async () => {
            await this.loadChannels();
            await this.loadProducts();
            await this.loadTemplates();
            await this.loadTags();
            await this.loadQuickReplies();
        });
        
        onMounted(() => {
            this.pollInterval = setInterval(() => {
                this.pollMessages();
            }, 5000);

            // Close dropdowns when clicking anywhere outside
            this._onDocumentClick = (ev) => {
                let changed = false;
                if (this.state.showChatDropdownId !== null) {
                    const menu = document.querySelector('.chat-dropdown-menu');
                    const btn = document.querySelector('.chat-dropdown-btn');
                    if ((menu && !menu.contains(ev.target) && btn && !btn.contains(ev.target)) || !menu) {
                        this.state.showChatDropdownId = null;
                        changed = true;
                    }
                }
                if (this.state.showHeaderDropdown) {
                    const headerMenu = document.querySelector('.header-dropdown-menu');
                    const headerBtn = document.querySelector('.header-dropdown-btn');
                    if ((headerMenu && !headerMenu.contains(ev.target) && headerBtn && !headerBtn.contains(ev.target)) || !headerMenu) {
                        this.state.showHeaderDropdown = false;
                        changed = true;
                    }
                }
                if (this.state.showMessageDropdownId !== null) {
                    const msgMenu = document.querySelector('.msg-dropdown-menu');
                    const msgBtn = document.querySelector('.msg-dropdown-btn');
                    if ((msgMenu && !msgMenu.contains(ev.target) && msgBtn && !msgBtn.contains(ev.target)) || !msgMenu) {
                        this.state.showMessageDropdownId = null;
                        changed = true;
                    }
                }
                if (this.state.showAttachMenu) {
                    const attachMenu = document.querySelector('.attach-dropdown-menu');
                    const attachBtn = document.querySelector('.whatsapp-attach-btn');
                    if ((attachMenu && !attachMenu.contains(ev.target) && attachBtn && !attachBtn.contains(ev.target)) || !attachMenu) {
                        this.state.showAttachMenu = false;
                        changed = true;
                    }
                }
                if (this.state.showPlusMenu) {
                    const plusMenu = document.querySelector('.attach-dropdown-menu');
                    const plusBtn = document.querySelector('.whatsapp-attach-btn');
                    if (!plusMenu || (plusMenu && !plusMenu.contains(ev.target) && plusBtn && !plusBtn.contains(ev.target))) {
                        this.state.showPlusMenu = false;
                        changed = true;
                    }
                }
                if (this.state.showFilterDropdown) {
                    const filterMenu = document.querySelector('.filter-dropdown-menu');
                    const filterPill = document.querySelector('.chat-filter-dropdown-container');
                    if (!filterMenu || (filterMenu && !filterMenu.contains(ev.target) && filterPill && !filterPill.contains(ev.target))) {
                        this.state.showFilterDropdown = false;
                        changed = true;
                    }
                }
            };
            document.addEventListener('click', this._onDocumentClick, true);

            // Close chat dropdown when the chat list is scrolled
            this._onChatListScroll = () => {
                if (this.state.showChatDropdownId !== null) {
                    this.state.showChatDropdownId = null;
                }
                if (this.state.showMessageDropdownId !== null) {
                    this.state.showMessageDropdownId = null;
                }
                if (this.state.showAttachMenu) {
                    this.state.showAttachMenu = false;
                }
                if (this.state.showPlusMenu) {
                    this.state.showPlusMenu = false;
                }
                if (this.state.showHeaderDropdown) {
                    this.state.showHeaderDropdown = false;
                }
                if (this.state.showFilterDropdown) {
                    this.state.showFilterDropdown = false;
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
            this.state.availableTags = await this.orm.call("whatsapp.account", "get_all_chat_tags", [], {}, { silent: true });
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
        
        // Find the last message time regardless of sender
        let lastMessageTime = null;
        for (let i = this.state.messages.length - 1; i >= 0; i--) {
            const msg = this.state.messages[i];
            // Meta 24-hour window: user wants to see it open if THEY or CUSTOMER sent a msg in last 24h
            if (msg.date) {
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

    getAvatarColor(name) {
        if (!name) return '#dfe5e7';
        const colors = [
            '#e57373', '#f06292', '#ba68c8', '#9575cd', '#7986cb', 
            '#64b5f6', '#4fc3f7', '#4dd0e1', '#4db6ac', '#81c784', 
            '#aed581', '#ff8a65', '#d4e157', '#ffd54f', '#ffb74d', '#a1887f', '#90a4ae'
        ];
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        hash = Math.abs(hash);
        return colors[hash % colors.length];
    }

    async loadProducts() {
        try {
            const results = await this.orm.searchRead(
                "whatsapp.product",
                [["show_in_catalogue", "=", true]],
                ["id", "name", "list_price", "description", "url", "item_code", "image_1920"],
                { order: "name asc" }
            );
            this.state.products = results;
        } catch (e) {
            console.error("Error loading products", e);
            this.state.products = [];
        }
    }

    openAddProductModal() {
        this.state.newProduct = {
            name: "",
            list_price: 0,
            description: "",
            url: "",
            item_code: "",
            image_1920: null,
            imagePreview: null
        };
        this.state.showAddProductModal = true;
    }

    closeAddProductModal() {
        this.state.showAddProductModal = false;
        this.state.newProduct = null;
    }

    handleProductImageUpload(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64 = e.target.result.split(',')[1];
            this.state.newProduct.image_1920 = base64;
            this.state.newProduct.imagePreview = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    async saveCatalogueProduct() {
        const prod = this.state.newProduct;
        if (!prod.name || !prod.name.trim()) {
            alert("Product name is required.");
            return;
        }
        try {
            const vals = {
                name: prod.name.trim(),
                list_price: parseFloat(prod.list_price) || 0,
                description: prod.description || "",
                url: prod.url || "",
                item_code: prod.item_code || "",
                show_in_catalogue: true,
            };
            if (prod.image_1920) {
                vals.image_1920 = prod.image_1920;
            }
            await this.orm.create("whatsapp.product", [vals]);
            await this.loadProducts();
            this.closeAddProductModal();
        } catch (e) {
            console.error("Failed to add catalogue product", e);
            alert("Failed to add product: " + e.message);
        }
    }

    async removeCatalogueProduct(productId, ev) {
        if (ev) ev.stopPropagation();
        if (!confirm("Remove this product from the catalogue?")) return;
        try {
            await this.orm.unlink("whatsapp.product", [productId]);
            await this.loadProducts();
        } catch (e) {
            console.error("Failed to remove catalogue product", e);
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
            this.state.accounts = await this.orm.call(
                "whatsapp.account",
                "get_whatsapp_web_accounts",
                [],
                {},
                { silent: true }
            );
            if (this.state.accounts.length > 0) {
                this.state.selectedAccount = this.state.accounts[0].id.toString();
            }
        }

        const domain = [["channel_type", "=", "whatsapp"]];
        if (this.state.selectedAccount) {
            domain.push(["wa_account_id", "=", parseInt(this.state.selectedAccount)]);
        }

        const cacheKey = 'wa_channels_' + (this.state.selectedAccount || '');
        try {
            const cached = localStorage.getItem(cacheKey);
            if (cached) {
                const parsed = JSON.parse(cached);
                if (parsed && parsed.length > 0 && this.state.channels.length === 0) {
                    this.state.channels = parsed;
                }
            }
        } catch (e) {
            console.warn("Failed to load cached channels", e);
        }

        let response = { channels: [], show_labels: false };
        try {
            response = await this.orm.call(
                "whatsapp.account",
                "get_whatsapp_web_channels",
                [],
                { wa_account_id: this.state.selectedAccount },
                { silent: true }
            );
        } catch (e) {
            console.warn("Offline or failed to fetch channels", e);
        }
        const channels = response.channels || [];
        if (response.show_labels !== undefined) {
            this.state.showLabels = response.show_labels;
        }
        
        if (channels.length > 0) {
            const partnerIds = channels.map(c => c.whatsapp_partner_id && c.whatsapp_partner_id[0]).filter(id => id);
            if (partnerIds.length > 0) {
                const partners = await this.orm.searchRead("res.partner", [["id", "in", partnerIds]], ["id", "phone"]);
                const partnerMap = {};
                for (const p of partners) {
                    partnerMap[p.id] = { phone: p.phone };
                }
                for (const c of channels) {
                    if (c.whatsapp_partner_id) {
                        const pData = partnerMap[c.whatsapp_partner_id[0]];
                        if (pData) {
                            c.customer_phone = pData.phone;
                        }
                    }
                    if (c.wa_account_id) {
                        c.wa_account_id = c.wa_account_id[0];
                    }
                }
            } else {
                for (const c of channels) {
                    if (c.wa_account_id) {
                        c.wa_account_id = c.wa_account_id[0];
                    }
                }
            }
            
            const validChannels = channels.filter(c => c.whatsapp_partner_id || c.whatsapp_number || c.name);
            validChannels.sort((a, b) => {
                if (a.wa_is_favourite && !b.wa_is_favourite) return -1;
                if (!a.wa_is_favourite && b.wa_is_favourite) return 1;
                return (b.write_date || '').localeCompare(a.write_date || '');
            });

            if (this.state.selectedChannel) {
                const currentId = this.state.selectedChannel.id;
                const updated = validChannels.find(c => c.id === currentId);
                if (updated) {
                    updated.unread_count = 0;
                    updated.wa_is_unread_global = false;
                    updated.message_needaction_counter = 0;
                    this.state.selectedChannel = updated;
                } else {
                    this.state.selectedChannel = null;
                }
            }

            this.state.channels = validChannels;
            
            try {
                localStorage.setItem(cacheKey, JSON.stringify(validChannels));
            } catch (e) {}
        } else if (!this.state.channels || this.state.channels.length === 0) {
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

    setChatState(channelId, field, value, ev) {
        if (ev) {
            ev.stopPropagation();
        }
        // Close dropdown immediately after action
        this.state.showChatDropdownId = null;
        
        // Update local state immediately for instant UI feedback
        const channel = this.state.channels.find(c => c.id === channelId);
        if (channel) {
            channel[field] = value;
            if (field === 'wa_is_done' && value) {
                channel.wa_is_unread_global = false;
            }
        }

        // Run database update in the background
        this.orm.call(
            "whatsapp.account",
            "set_whatsapp_chat_state",
            [channelId, field, value],
            {},
            { silent: true }
        ).catch(e => {
            console.error("Failed to update chat state", e);
        });
    }

    setChatFilter(filterType) {
        this.state.chatFilter = filterType;
        this.state.chatSearch = '';
    }

    get totalUnreadChannels() {
        const selectedId = this.state.selectedChannel?.id;
        return (this.state.channels || []).filter(c =>
            c.id !== selectedId &&
            (c.unread_count > 0 || c.message_needaction_counter > 0 || c.wa_is_unread_global)
        ).length;
    }

    get searchQuery() {
        return (this.state.chatSearch || "").toLowerCase().trim();
    }

    get filteredChannels() {
        if (!this.state.channels) return [];
        let filtered = this.state.channels;
        
        switch (this.state.chatFilter) {
            case 'unread':
                filtered = filtered.filter(c => c.wa_is_unread_global || (c.unread_count && c.unread_count > 0) || (c.message_needaction_counter && c.message_needaction_counter > 0));
                break;
            case 'favourites':
                filtered = filtered.filter(c => c.wa_is_favourite);
                break;
            case 'done':
                filtered = filtered.filter(c => c.wa_is_done && !c.wa_is_blocked);
                break;
            case 'archived':
                filtered = filtered.filter(c => c.wa_is_done && !c.wa_is_blocked);
                break;
            case 'urgent':
                filtered = filtered.filter(c => c.wa_is_urgent && !c.wa_is_blocked);
                break;
            case 'all':
            default:
                if (this.state.chatFilter && this.state.chatFilter.startsWith('tag_')) {
                    const tagId = parseInt(this.state.chatFilter.replace('tag_', ''));
                    filtered = filtered.filter(c => !c.wa_is_blocked && c.wa_tags && c.wa_tags.some(t => t.id === tagId));
                } else {
                    // Inbox view: hide archived and blocked chats
                    filtered = filtered.filter(c => !c.wa_is_done && !c.wa_is_blocked);
                }
                break;
        }

        // Apply search query
        if (this.searchQuery) {
            filtered = filtered.filter(c => {
                const name = (c.name || "").toLowerCase();
                const phone = (c.whatsapp_number || c.customer_phone || "").toLowerCase();
                const preview = (c.last_message_preview || "").toLowerCase();
                return name.includes(this.searchQuery) || phone.includes(this.searchQuery) || preview.includes(this.searchQuery);
            });
        }
        
        return filtered;
    }

    get groupedMessages() {
        if (!this.state.messages || this.state.messages.length === 0) return [];
        const groups = [];
        let currentGroup = null;

        for (let i = 0; i < this.state.messages.length; i++) {
            const msg = this.state.messages[i];
            const hasNoText = !msg.bodyText || msg.bodyText.trim() === '';
            const isMedia = msg.attachment_ids && msg.attachment_ids.length === 1 && 
                            msg.attachment_ids[0].mimetype && 
                            (msg.attachment_ids[0].mimetype.startsWith('image/') || msg.attachment_ids[0].mimetype.startsWith('video/'));

            if (isMedia && hasNoText) {
                if (currentGroup && currentGroup.isAlbum && currentGroup.isMe === msg.isMe) {
                    currentGroup.messages.push(msg);
                    currentGroup.wa_state = msg.wa_state; // Keep the state of the last message in the album
                } else {
                    if (currentGroup) {
                        if (currentGroup.isAlbum && currentGroup.messages.length === 1) {
                            groups.push({ isAlbum: false, isMe: currentGroup.isMe, message: currentGroup.messages[0], id: 'msg_' + currentGroup.messages[0].id });
                        } else {
                            groups.push(currentGroup);
                        }
                    }
                    currentGroup = {
                        isAlbum: true,
                        isMe: msg.isMe,
                        messages: [msg],
                        id: 'album_' + msg.id,
                        timeText: msg.timeText,
                        dateText: msg.dateText,
                        wa_state: msg.wa_state,
                    };
                }
            } else {
                if (currentGroup) {
                    if (currentGroup.isAlbum && currentGroup.messages.length === 1) {
                        groups.push({ isAlbum: false, isMe: currentGroup.isMe, message: currentGroup.messages[0], id: 'msg_' + currentGroup.messages[0].id });
                    } else {
                        groups.push(currentGroup);
                    }
                    currentGroup = null;
                }
                groups.push({
                    isAlbum: false,
                    isMe: msg.isMe,
                    message: msg,
                    id: 'msg_' + msg.id,
                });
            }
        }
        if (currentGroup) {
            if (currentGroup.isAlbum && currentGroup.messages.length === 1) {
                groups.push({ isAlbum: false, isMe: currentGroup.isMe, message: currentGroup.messages[0], id: 'msg_' + currentGroup.messages[0].id });
            } else {
                groups.push(currentGroup);
            }
        }
        return groups;
    }

    async clearChat(channelId) {
        if (!confirm("Are you sure you want to clear this chat? All messages will be deleted, but the contact will remain.")) {
            return;
        }
        this.state.showChatDropdownId = null;
        this.state.showHeaderDropdown = false;
        try {
            const res = await this.orm.call("whatsapp.account", "clear_whatsapp_chat", [channelId]);
            if (res.success) {
                if (this.state.selectedChannel && this.state.selectedChannel.id === channelId) {
                    this.state.messages = [];
                    this.state.selectedChannel.last_message_preview = "";
                }
                const chan = this.state.channels.find(c => c.id === channelId);
                if (chan) chan.last_message_preview = "";
                this.messageCache[channelId] = [];
            } else {
                alert(res.error || "Failed to clear chat");
            }
        } catch(e) {
            console.error("Failed to clear chat:", e);
        }
    }

    openDeleteChatModal(channelId, ev) {
        if (ev) ev.stopPropagation();
        // Close any open dropdown first
        this.state.showChatDropdownId = null;
        this.state.showHeaderDropdown = false;
        this.state.deleteChatConfirmId = channelId;
    }

    closeDeleteModal() {
        this.state.deleteMessageConfirmId = null;
    }

    // ─── Custom Audio Player ────────────────────────────────────────────────────

    /** Toggle play/pause for a message audio attachment */
    toggleAudioPlay(attId, url, mimetype) {
        const audioId = String(attId);
        const current = this.state.activeAudioId;

        // Stop any currently playing audio
        if (this._currentAudio) {
            this._currentAudio.pause();
            this._currentAudio.currentTime = 0;
            this._currentAudio = null;
        }

        // If we clicked the already-active one, just stop it
        if (current === audioId) {
            this.state.activeAudioId = null;
            return;
        }

        // Create a new Audio element
        const audio = new Audio(url);
        audio.preload = 'metadata';
        this._currentAudio = audio;
        this.state.activeAudioId = audioId;

        if (!this.state.audioProgress[audioId]) {
            this.state.audioProgress[audioId] = { current: 0, duration: 0 };
        }

        audio.addEventListener('loadedmetadata', () => {
            this.state.audioProgress[audioId] = {
                ...this.state.audioProgress[audioId],
                duration: audio.duration || 0,
            };
        });

        audio.addEventListener('timeupdate', () => {
            if (this.state.activeAudioId === audioId) {
                this.state.audioProgress[audioId] = {
                    current: audio.currentTime,
                    duration: audio.duration || this.state.audioProgress[audioId]?.duration || 0,
                };
            }
        });

        audio.addEventListener('ended', () => {
            this.state.activeAudioId = null;
            this.state.audioProgress[audioId] = {
                current: 0,
                duration: this.state.audioProgress[audioId]?.duration || 0,
            };
            this._currentAudio = null;
        });

        audio.play().catch(() => {
            this.state.activeAudioId = null;
            this._currentAudio = null;
        });
    }

    /** Seek the current audio to a position (0-100 range from progress bar click) */
    seekAudio(attId, ev) {
        const audioId = String(attId);
        if (this.state.activeAudioId !== audioId || !this._currentAudio) return;
        const bar = ev.currentTarget;
        const rect = bar.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
        this._currentAudio.currentTime = ratio * (this._currentAudio.duration || 0);
    }

    /** Format seconds as m:ss */
    formatAudioTime(secs) {
        if (!secs || isNaN(secs)) return '0:00';
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }

    /** Get progress percentage for waveform */
    getAudioProgress(attId) {
        const p = this.state.audioProgress[String(attId)];
        if (!p || !p.duration) return 0;
        return Math.min(100, (p.current / p.duration) * 100);
    }

    /** Play/pause the recording preview blob */
    onPreviewPlayPause() {
        if (this.state.activeAudioId === '__preview__') {
            if (this._currentAudio) {
                this._currentAudio.pause();
                this._currentAudio = null;
            }
            this.state.activeAudioId = null;
            return;
        }
        if (this._currentAudio) {
            this._currentAudio.pause();
            this._currentAudio = null;
        }
        if (!this.state.recordingBlobUrl) return;
        const audio = new Audio(this.state.recordingBlobUrl);
        this._currentAudio = audio;
        this.state.activeAudioId = '__preview__';
        if (!this.state.audioProgress['__preview__']) {
            this.state.audioProgress['__preview__'] = { current: 0, duration: 0 };
        }
        audio.addEventListener('loadedmetadata', () => {
            this.state.audioProgress['__preview__'] = { ...this.state.audioProgress['__preview__'], duration: audio.duration || 0 };
        });
        audio.addEventListener('timeupdate', () => {
            if (this.state.activeAudioId === '__preview__') {
                this.state.audioProgress['__preview__'] = { current: audio.currentTime, duration: audio.duration || 0 };
            }
        });
        audio.addEventListener('ended', () => {
            this.state.activeAudioId = null;
            this.state.audioProgress['__preview__'] = { current: 0, duration: this.state.audioProgress['__preview__']?.duration || 0 };
            this._currentAudio = null;
        });
        audio.play().catch(() => { this.state.activeAudioId = null; this._currentAudio = null; });
    }

    seekPreviewAudio(ev) {
        if (this.state.activeAudioId !== '__preview__' || !this._currentAudio) return;
        const bar = ev.currentTarget;
        const rect = bar.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
        this._currentAudio.currentTime = ratio * (this._currentAudio.duration || 0);
    }


    onLightboxReply() {
        if (this.state.fullscreenMedia && this.state.fullscreenMedia.msg) {
            this.openReply(this.state.fullscreenMedia.msg);
            this.closeMedia();
        }
    }

    openReply(msg) {
        this.state.replyingToMessage = msg;
        this.state.showMessageDropdownId = null;
        this.state.showAttachMenu = false;
        // Focus the chat input
        setTimeout(() => {
            const input = document.querySelector('.chat-input');
            if (input) input.focus();
        }, 50);
    }

    closeReply() {
        this.state.replyingToMessage = null;
    }

    startEditMessage(msg) {
        this.state.editingMessageId = msg.id;
        this.state.editingMessageOriginal = msg.bodyText;
        this.state.newMessage = msg.bodyText;
        this.state.showMessageDropdownId = null;
        this.state.replyingToMessage = null; // close reply if open
        setTimeout(() => {
            const input = document.querySelector('.whatsapp-input');
            if (input) {
                input.focus();
                // Place cursor at end
                input.setSelectionRange(input.value.length, input.value.length);
                // Trigger resize
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            }
        }, 50);
    }

    cancelEdit() {
        this.state.editingMessageId = null;
        this.state.editingMessageOriginal = '';
        this.state.newMessage = '';
        setTimeout(() => {
            const input = document.querySelector('.whatsapp-input');
            if (input) { input.style.height = 'auto'; input.focus(); }
        }, 50);
    }

    async submitMessageEdit() {
        const msgId = this.state.editingMessageId;
        const newBody = this.state.newMessage.trim();
        if (!msgId || !newBody) {
            this.cancelEdit();
            return;
        }
        // Optimistic update in local state
        const msg = this.state.messages.find(m => m.id === msgId);
        if (msg) {
            msg.bodyText = newBody;
            msg.is_edited = true;
        }
        // Clear edit state immediately
        this.state.editingMessageId = null;
        this.state.editingMessageOriginal = '';
        this.state.newMessage = '';

        try {
            await this.orm.call(
                'whatsapp.account',
                'edit_whatsapp_message',
                [],
                { message_id: msgId, new_body: newBody }
            );
        } catch (e) {
            console.error('Failed to edit message:', e);
            // Revert on failure
            if (msg) {
                msg.bodyText = this.state.editingMessageOriginal || msg.bodyText;
                msg.is_edited = false;
            }
        }
    }

    toggleAttachMenu() {
        this.state.showAttachMenu = !this.state.showAttachMenu;
        this.state.showMessageDropdownId = null;
    }

    async confirmDeleteMessage() {
        const messageId = this.state.deleteMessageConfirmId;
        if (!messageId) return;
        this.state.deleteMessageConfirmId = null;
        await this.deleteMessage(messageId);
    }

    closeDeleteChatModal() {
        this.state.deleteChatConfirmId = null;
    }

    async confirmDeleteChat() {
        const channelId = this.state.deleteChatConfirmId;
        if (!channelId) return;
        this.state.deleteChatConfirmId = null;
        await this.deleteChat(channelId);
    }

    selectChannel(channel, event) {
        if (event && this.state.selectedChannels.length > 0) {
            this.toggleChannelSelection(channel.id, event);
            return;
        }

        this.state.selectedChannel = channel;
        this.state.selectedMessages = [];
        this.state.chatSearch = '';
        this.state.messages = this.messageCache[channel.id] || [];

        const loadId = Symbol();
        this.currentLoadId = loadId;
        
        // Fetch media for the channel if the panel is open
        if (this.state.showContactInfo) {
            this.fetchContactMedia(channel.id);
        }
        
        // Mark as read locally immediately for responsiveness
        channel.unread_count = 0;
        channel.wa_is_unread_global = false;
        channel.message_needaction_counter = 0;

        // Force reactivity update in case proxy tracking missed the direct mutation
        const idx = this.state.channels.findIndex(c => c.id === channel.id);
        if (idx !== -1) {
            this.state.channels[idx].unread_count = 0;
            this.state.channels[idx].wa_is_unread_global = false;
            this.state.channels[idx].message_needaction_counter = 0;
        }

        setTimeout(() => {
            try {
                this.orm.call("whatsapp.account", "mark_whatsapp_web_messages_read", [channel.id], {}, { silent: true }).catch(e => {
                    console.warn("Failed to mark messages as read silently, queuing for offline retry");
                    try {
                        const readQueue = JSON.parse(localStorage.getItem('wa_offline_read_queue') || '[]');
                        if (!readQueue.includes(channel.id)) {
                            readQueue.push(channel.id);
                            localStorage.setItem('wa_offline_read_queue', JSON.stringify(readQueue));
                        }
                    } catch(err) {}
                });
            } catch (e) {
                console.warn("Failed to mark messages as read", e);
            }
        }, 50);
        
        // Load messages asynchronously without blocking the UI
        this.loadMessages(channel.id, loadId).catch(e => console.warn("Failed to load messages:", e));
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

    async loadMessages(channelId = null, loadId = null) {
        const id = channelId || (this.state.selectedChannel ? this.state.selectedChannel.id : null);
        if (!id) return;

        // Capture scroll state before loading new messages
        let wasAtBottom = true; // default to true so initial loads snap to bottom
        if (this.messagesContainer && this.messagesContainer.el) {
            const el = this.messagesContainer.el;
            wasAtBottom = (el.scrollHeight - el.scrollTop - el.clientHeight) < 100;
        }
        if (loadId) {
            wasAtBottom = true;
        }

        const cacheKey = 'wa_messages_' + id;
        if (!loadId) {
            try {
                const cached = localStorage.getItem(cacheKey);
                if (cached) {
                    const parsed = JSON.parse(cached);
                    if (parsed && parsed.length > 0 && (!this.state.messages || this.state.messages.length === 0)) {
                        this.state.messages = parsed;
                    }
                }
            } catch (e) {}
        }

        try {
            let messages = [];
            try {
                messages = await this.orm.call(
                    "whatsapp.account",
                    "get_whatsapp_web_messages",
                    [id],
                    {},
                    { silent: true }
                );
            } catch (e) {
                console.warn("Offline or failed to fetch messages");
            }

            // Race condition check: if a new channel was selected while we were loading, abort.
            if (loadId && this.currentLoadId !== loadId) {
                return;
            }
            if (this.state.selectedChannel && this.state.selectedChannel.id !== id) {
                return;
            }
            
            const oldMessages = [...this.state.messages];
            
            if (messages.length > 0) {
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
                
                let isForwarded = false;
                if (bodyText.startsWith("↩ Forwarded:")) {
                    isForwarded = true;
                    bodyText = bodyText.substring("↩ Forwarded:".length).trim();
                } else if (bodyText.startsWith("↩ Forwarded")) {
                    isForwarded = true;
                    bodyText = bodyText.substring("↩ Forwarded".length).trim();
                }
                
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
                let isSystem = msg.message_type === 'notification' && !msg.wa_state;

                let isContactCard = false;
                let contactCardName = "";
                let contactCardPhone = "";
                let contactCardCleanPhone = "";
                const contactCardMatch = bodyText.match(/^📋\s*\*(.+?)\*\n📞\s*(.+)$/);
                if (contactCardMatch) {
                    isContactCard = true;
                    contactCardName = contactCardMatch[1].trim();
                    contactCardPhone = contactCardMatch[2].trim();
                    contactCardCleanPhone = contactCardPhone.replace(/\D/g, '');
                }
                
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
                    authorName = msg.author_id[1] || "";
                    let authorLower = authorName.toLowerCase();
                    if (authorLower.includes("bot") || authorLower === "odoobot" || authorLower === "system") {
                        authorName = "Bot";
                    }
                } else if (!isMe && this.state.selectedChannel) {
                    authorName = this.state.selectedChannel.name || "Customer";
                }
                
                return { ...msg, isMe, bodyText, timeText, authorName, isMenu, menuTitle, menuOptions, isSystem, isForwarded, isContactCard, contactCardName, contactCardPhone, contactCardCleanPhone };
            });
            } // end if messages.length > 0
            
            // --- Merge pending/recently sent messages ---
            const now = Date.now();

            // ── Audio-specific: carry over localBlobUrl from temp audio attachment ──
            // When the server message arrives, preserve the blob URL so the player
            // keeps working without any disruption to the UI.
            const tempAudioMsgs = oldMessages.filter(m =>
                m.id && m.id.toString().startsWith('temp_audio_') &&
                m.attachment_ids && m.attachment_ids.some(a => a.localBlobUrl)
            );
            if (tempAudioMsgs.length > 0) {
                for (const serverMsg of this.state.messages) {
                    if (!serverMsg.isMe) continue;
                    if (!serverMsg.attachment_ids || serverMsg.attachment_ids.length === 0) continue;
                    const serverAtt = serverMsg.attachment_ids.find(a => a.mimetype && a.mimetype.startsWith('audio/'));
                    if (!serverAtt) continue;
                    // Match against a temp audio message (same channel, recent, audio attachment)
                    const matchingTemp = tempAudioMsgs.find(t => {
                        const tAtt = t.attachment_ids.find(a => a.localBlobUrl);
                        return tAtt && !serverAtt.localBlobUrl;
                    });
                    if (matchingTemp) {
                        const tempAtt = matchingTemp.attachment_ids.find(a => a.localBlobUrl);
                        // Preserve localBlobUrl on the real server attachment
                        serverAtt.localBlobUrl = tempAtt.localBlobUrl;
                        // Migrate audio player state from temp ID to real server ID
                        const tempId = String(tempAtt.id);
                        const realId = String(serverAtt.id);
                        if (this.state.activeAudioId === tempId) {
                            this.state.activeAudioId = realId;
                        }
                        if (this.state.audioProgress[tempId]) {
                            this.state.audioProgress[realId] = this.state.audioProgress[tempId];
                            delete this.state.audioProgress[tempId];
                        }
                    }
                }
            }

            const recentTempMsgs = oldMessages.filter(m => {
                if (m.id && m.id.toString().startsWith('temp_')) {
                    const parts = m.id.toString().split('_');
                    // Find the timestamp (e.g. temp_17000, temp_17000_0, temp_audio_17000)
                    const tempTime = parseInt(parts[1]) || parseInt(parts[2]) || 0;
                    // Keep if it was created less than 15 seconds ago
                    if (now - tempTime < 15000) {
                        // For audio temp messages: check if a server audio msg already exists
                        const hasLocalAudio = m.attachment_ids && m.attachment_ids.some(a => a.localBlobUrl);
                        if (hasLocalAudio) {
                            // Audio already merged into server message above — discard temp
                            const alreadyMerged = this.state.messages.some(serverMsg =>
                                serverMsg.isMe &&
                                serverMsg.attachment_ids &&
                                serverMsg.attachment_ids.some(a => a.localBlobUrl)
                            );
                            return !alreadyMerged;
                        }
                        // Check if the server already returned a message with the same body sent by me
                        const alreadyReceived = this.state.messages.some(serverMsg => 
                            serverMsg.isMe === true && 
                            serverMsg.bodyText === m.bodyText
                        );
                        return !alreadyReceived;
                    }
                }
                return false;
            });
            
            // Also add ANY offline queue items that haven't even been attempted yet
            const offlineQueue = JSON.parse(localStorage.getItem('wa_offline_queue') || '[]');
            const pendingQueueMsgs = offlineQueue.filter(q => q.channelId === id).map(q => {
                return {
                    id: q.tempId,
                    bodyText: q.body,
                    isMe: true,
                    isSystem: false,
                    timeText: new Date(q.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }),
                    wa_state: 'pending',
                    attachment_ids: q.file ? [{
                        id: 'temp_att',
                        name: q.file.name,
                        mimetype: q.file.type,
                        dataUrl: q.file.dataUrl
                    }] : []
                };
            });
            
            // Filter pendingQueueMsgs to avoid duplicating what we already have in recentTempMsgs
            const queueToAdd = pendingQueueMsgs.filter(q => !recentTempMsgs.find(r => r.id === q.id));
            
            if (recentTempMsgs.length > 0 || queueToAdd.length > 0) {
                this.state.messages = [...this.state.messages, ...recentTempMsgs, ...queueToAdd];
            }
            
            this.messageCache[id] = this.state.messages;
            
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
                const timeStr = lastMsg.date ? (lastMsg.date.includes('T') ? lastMsg.date : lastMsg.date.replace(' ', 'T') + 'Z') : '';
                
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
            
            if (messages.length > 0) {
                this.messageCache[id] = this.state.messages;
                try {
                    localStorage.setItem(cacheKey, JSON.stringify(this.state.messages));
                } catch(e) {}
            }
            
            // Scroll to bottom if this is an explicit chat load (loadId),
            // or if it's a background poll but the user is already at the bottom.
            if (loadId || wasAtBottom) {
                this.scrollToBottom();
            }
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
                const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                const startOfTarget = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
                const diffCalendarDays = Math.round((startOfToday - startOfTarget) / (1000 * 3600 * 24));
                
                if (diffCalendarDays === 0) {
                    return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                } else if (diffCalendarDays === 1) {
                    return 'Yesterday';
                } else if (diffCalendarDays > 1 && diffCalendarDays < 7) {
                    return dt.toLocaleDateString([], { weekday: 'long' });
                } else {
                    return dt.toLocaleDateString([], { day: '2-digit', month: '2-digit', year: '2-digit' });
                }
            } catch (e) {
                return '';
            }
        }
    
    openMedia(attId, ev, type='image', filename='', accessToken='', albumMessages=null, msg=null) {
        if (ev) ev.stopPropagation();

        let activeIndex = 0;
        let currentMsg = msg;
        if (albumMessages && albumMessages.length > 0) {
            activeIndex = albumMessages.findIndex(m => m.attachment_ids && m.attachment_ids[0].id === attId);
            if (activeIndex === -1) activeIndex = 0;
            currentMsg = albumMessages[activeIndex];
        }

        this.state.fullscreenMedia = {
            id: attId,
            type: type,
            filename: filename || '',
            accessToken: accessToken || '',
            scale: 1,
            translateX: 0,
            translateY: 0,
            albumMessages: albumMessages,
            activeIndex: activeIndex,
            msg: currentMsg
        };
        // Bind drag handlers (stored so we can remove them)
        this._lbDragging = false;
        this._lbDragStartX = 0;
        this._lbDragStartY = 0;
        this._lbDragOriginX = 0;
        this._lbDragOriginY = 0;
    }
    
    nextMedia(ev) {
        if (ev) ev.stopPropagation();
        const m = this.state.fullscreenMedia;
        if (m && m.albumMessages && m.activeIndex < m.albumMessages.length - 1) {
            const nextMsg = m.albumMessages[m.activeIndex + 1];
            const att = nextMsg.attachment_ids[0];
            this.openMedia(att.id, null, att.mimetype.startsWith('video/') ? 'video' : 'image', att.name, att.access_token, m.albumMessages, nextMsg);
        }
    }

    prevMedia(ev) {
        if (ev) ev.stopPropagation();
        const m = this.state.fullscreenMedia;
        if (m && m.albumMessages && m.activeIndex > 0) {
            const prevMsg = m.albumMessages[m.activeIndex - 1];
            const att = prevMsg.attachment_ids[0];
            this.openMedia(att.id, null, att.mimetype.startsWith('video/') ? 'video' : 'image', att.name, att.access_token, m.albumMessages, prevMsg);
        }
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
        let url = '';
        if (this.state.fullscreenMedia.type === 'video') {
            url = `/web/content/${this.state.fullscreenMedia.id}?download=true`;
        } else {
            url = `/web/image/${this.state.fullscreenMedia.id}?download=true`;
        }
        if (this.state.fullscreenMedia.accessToken) {
            url += `&access_token=${this.state.fullscreenMedia.accessToken}`;
        }
        return url;
    }

    getZoomPercent() {
        if (!this.state.fullscreenMedia) return '100%';
        return Math.round(this.state.fullscreenMedia.scale * 100) + '%';
    }

    async pollMessages() {
        this.flushOfflineQueue();
        // Only reload channels in background to check for NEW channels/messages
        // but do NOT call loadChannels() as it overwrites locally-cleared unread counts.
        // Instead, fetch fresh channel data and merge carefully.
        try {
            const response = await this.orm.call(
                "whatsapp.account",
                "get_whatsapp_web_channels",
                [],
                { wa_account_id: this.state.selectedAccount },
                { silent: true }
            );
            const freshChannels = response.channels || [];

            if (freshChannels && this.myPartnerId) {
                // unread_count is already populated by get_whatsapp_web_channels
            }

            // Filter ghost channels
            const validFresh = (freshChannels || []).filter(c => c.whatsapp_partner_id || c.whatsapp_number || c.name);
            validFresh.sort((a, b) => {
                if (a.wa_is_favourite && !b.wa_is_favourite) return -1;
                if (!a.wa_is_favourite && b.wa_is_favourite) return 1;
                return (b.write_date || '').localeCompare(a.write_date || '');
            });

            // Keep selected channel in sync and clear unread BEFORE updating this.state.channels to prevent UI flicker
            if (this.state.selectedChannel) {
                const found = validFresh.find(c => c.id === this.state.selectedChannel.id);
                if (found) {
                    found.unread_count = 0; // always keep selected as read
                    found.wa_is_unread_global = false;
                    found.message_needaction_counter = 0;
                    this.state.selectedChannel = found;
                }
            }

            this.state.channels = validFresh;
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

    async compressImage(file, maxWidth = 1600, maxHeight = 1600, quality = 0.7) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = event => {
                const img = new Image();
                img.src = event.target.result;
                img.onload = () => {
                    let width = img.width;
                    let height = img.height;

                    if (width > height) {
                        if (width > maxWidth) {
                            height = Math.round(height * maxWidth / width);
                            width = maxWidth;
                        }
                    } else {
                        if (height > maxHeight) {
                            width = Math.round(width * maxHeight / height);
                            height = maxHeight;
                        }
                    }

                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    
                    // Force WhatsApp-supported formats. Convert webp/bmp to jpeg.
                    let outputType = file.type;
                    if (outputType !== 'image/jpeg' && outputType !== 'image/png') {
                        outputType = 'image/jpeg';
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillRect(0, 0, width, height);
                    }
                    
                    ctx.drawImage(img, 0, 0, width, height);

                    canvas.toBlob(blob => {
                        let filename = file.name;
                        if (outputType === 'image/jpeg' && !filename.toLowerCase().match(/\.jpe?g$/)) {
                            filename = filename.replace(/\.[^/.]+$/, "") + ".jpg";
                        }
                        const compressedFile = new File([blob], filename, {
                            type: outputType,
                            lastModified: Date.now()
                        });
                        resolve(compressedFile);
                    }, outputType, quality);
                };
            };
        });
    }

    togglePlusMenu() {
        this.state.showPlusMenu = !this.state.showPlusMenu;
    }

    // ─── Send Phone Number / Contact ────────────────────────────────────────────

    async openSendPhoneModal() {
        this.state.showPlusMenu = false;
        this.state.phoneModalName = '';
        this.state.phoneModalNumber = '';
        this.state.phoneModalSearch = '';
        this.state.phoneModalContacts = [];
        this.state.allPhoneModalContacts = [];
        this.state.showPhoneModal = true;
        
        try {
            const contacts = await this.orm.call(
                "whatsapp.account",
                "get_contacts_for_new_chat",
                []
            );
            this.state.allPhoneModalContacts = contacts;
            this.state.phoneModalContacts = contacts;
        } catch (e) {
            console.error("Failed to load contacts for phone modal", e);
        }
    }

    closeSendPhoneModal() {
        this.state.showPhoneModal = false;
        this.state.phoneModalName = '';
        this.state.phoneModalNumber = '';
        this.state.phoneModalSearch = '';
        this.state.phoneModalContacts = [];
    }

    onPhoneModalSearch() {
        const q = (this.state.phoneModalSearch || '').trim().toLowerCase();
        if (!q) {
            this.state.phoneModalContacts = this.state.allPhoneModalContacts || [];
            return;
        }
        
        this.state.phoneModalContacts = (this.state.allPhoneModalContacts || []).filter(c => 
            (c.name && c.name.toLowerCase().includes(q)) ||
            (c.phone && c.phone.toLowerCase().includes(q)) ||
            (c.mobile && c.mobile.toLowerCase().includes(q))
        );
    }

    selectPhoneContact(contact) {
        this.state.phoneModalName = contact.name || '';
        this.state.phoneModalNumber = contact.phone || contact.mobile || '';
        this.state.phoneModalSearch = '';
        this.state.phoneModalContacts = [];
    }

    async sendPhoneNumber() {
        const name = (this.state.phoneModalName || '').trim();
        const number = (this.state.phoneModalNumber || '').trim();
        if (!number || !this.state.selectedChannel) return;

        // Build a nicely formatted contact card message
        const body = `📋 *${name || 'Contact'}*\n📞 ${number}`;

        // Reuse the existing text-send path
        const prevMsg = this.state.newMessage;
        this.state.newMessage = body;
        this.closeSendPhoneModal();
        await this.sendMessage();
        // sendMessage clears state.newMessage itself, nothing extra needed
    }

    triggerFileInput(acceptType, mode) {
        this.state.showPlusMenu = false;
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = acceptType;
        if (mode !== 'sticker') {
            fileInput.multiple = true;
        }
        fileInput.onchange = (e) => {
            if (mode === 'sticker') {
                this.onStickerSelect(e);
            } else {
                this.onFileSelect(e);
            }
        };
        fileInput.click();
    }

    async onStickerSelect(ev) {
        let file = ev.target.files[0];
        if (!file || !this.state.selectedChannel) return;

        // Upload to Odoo as attachment
        const formData = new window.FormData();
        formData.append('csrf_token', window.odoo?.csrf_token || '');
        formData.append('name', file.name);
        formData.append('ufile', file, file.name);
        formData.append('model', 'discuss.channel');
        formData.append('id', this.state.selectedChannel.id);

        try {
            const response = await window.fetch('/web/binary/upload_attachment', {
                method: 'POST',
                body: formData,
            });
            const responseText = await response.text();
            const match = responseText.match(/\[.*?\]|\{.*?\}/);
            if (match) {
                const result = JSON.parse(match[0]);
                let attId = null;
                if (Array.isArray(result)) attId = result[0].id;
                else if (result.id) attId = result.id;
                
                if (attId) {
                    await this.orm.call(
                        "whatsapp.account",
                        "send_whatsapp_sticker",
                        [this.state.selectedChannel.id, attId],
                        {},
                        { silent: true }
                    );
                }
            }
        } catch (e) {
            console.error("Sticker upload failed", e);
            this.comingSoon(null, "Failed to upload and send sticker.");
        }
    }

    async onFileSelect(ev) {
        this.state.showPlusMenu = false;
        let files = ev.target.files;
        if (!files || files.length === 0) return;

        for (let i = 0; i < files.length; i++) {
            let file = files[i];
            if (file.type.startsWith('image/') && !file.type.includes('gif')) {
                try {
                    file = await this.compressImage(file);
                } catch (e) {
                    console.warn('Image compression failed', e);
                }
            }

            const dataUrl = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.readAsDataURL(file);
            });

            this.state.pendingFiles = [...this.state.pendingFiles, {
                name: file.name,
                type: file.type,
                size: file.size,
                file: file,
                dataUrl: dataUrl
            }];
        }
        if (ev.target) ev.target.value = "";
    }
    
    removePendingFile(index) {
        if (typeof index === 'number') {
            this.state.pendingFiles.splice(index, 1);
        } else {
            this.state.pendingFiles = [];
        }
    }

    async startRecording() {
        if (this.state.isRecording) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this._mediaStream = stream;
            this._audioChunks = [];

            let options = {};
            if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                options = { mimeType: 'audio/webm;codecs=opus' };
            } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
                options = { mimeType: 'audio/ogg;codecs=opus' };
            } else if (MediaRecorder.isTypeSupported('audio/webm')) {
                options = { mimeType: 'audio/webm' };
            } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                options = { mimeType: 'audio/mp4' };
            }
            
            this._mediaRecorder = new MediaRecorder(stream, options);
            this._mediaRecorder.ondataavailable = (ev) => {
                if (ev.data && ev.data.size > 0) {
                    this._audioChunks.push(ev.data);
                }
            };
            this._mediaRecorder.onstop = () => {
                // Chrome records audio/webm;codecs=opus but WhatsApp API only accepts audio/ogg.
                // Since both formats use the Opus codec, we can safely re-label the blob
                // as audio/ogg;codecs=opus without transcoding — this is the standard approach.
                let mimeType = this._mediaRecorder.mimeType || 'audio/webm';
                if (mimeType.includes('webm') && mimeType.includes('opus')) {
                    mimeType = 'audio/ogg; codecs=opus';
                } else if (mimeType.includes('webm')) {
                    mimeType = 'audio/ogg; codecs=opus';
                }
                const blob = new Blob(this._audioChunks, { type: mimeType });
                const url = URL.createObjectURL(blob);
                this.state.recordingBlob = blob;
                this.state.recordingBlobUrl = url;
                this.state.isRecording = false;
                
                if (this._sendAfterRecording) {
                    this._sendAfterRecording = false;
                    this.sendAudioMessage();
                }
                clearInterval(this._recordingTimer);
            };

            this._mediaRecorder.start();
            this.state.isRecording = true;
            this.state.isPaused = false;
            this.state.recordingSeconds = 0;
            this.state.recordingBlob = null;
            this.state.recordingBlobUrl = null;
            this._recordingTimer = setInterval(() => {
                if (!this.state.isPaused) {
                    this.state.recordingSeconds++;
                }
            }, 1000);
        } catch (e) {
            console.error('Microphone access denied or error:', e);
            alert('Microphone access is required to record audio.');
        }
    }

    pauseRecording() {
        if (this._mediaRecorder && this.state.isRecording) {
            if (this._mediaRecorder.state === 'recording') {
                this._mediaRecorder.pause();
                this.state.isPaused = true;
            } else if (this._mediaRecorder.state === 'paused') {
                this._mediaRecorder.resume();
                this.state.isPaused = false;
            }
        }
    }

    stopAndSendRecording() {
        this._sendAfterRecording = true;
        this.stopRecording();
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
        if (this._isSendingAudio) return;  // prevent double sends
        this._isSendingAudio = true;

        // Capture blob before clearing state
        const blob = this.state.recordingBlob;
        const blobUrl = this.state.recordingBlobUrl;

        // ── Clear recording UI INSTANTLY ──────────────────────────────────────
        this.state.recordingBlob = null;
        this.state.recordingBlobUrl = null;
        this.state.recordingSeconds = 0;

        // ── Show audio bubble in chat INSTANTLY (optimistic UI) ───────────────
        const tempAttId = 'temp_audio_' + Date.now();
        const tempMsg = {
            id: tempAttId,
            bodyText: '',
            isMe: true,
            isSystem: false,
            timeText: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            wa_state: 'pending',
            attachment_ids: [{
                id: tempAttId,
                mimetype: blob.type || 'audio/ogg',
                name: 'voice_message.ogg',
                localBlobUrl: blobUrl,  // plays immediately from blob, no server needed yet
            }]
        };
        this.state.messages.push(tempMsg);
        this.scrollToBottom();

        // Always use .ogg extension — the blob is already labelled audio/ogg above
        // so the server will store it with the correct mimetype that WhatsApp accepts
        let ext = 'ogg';
        if (blob.type.includes('mp4') || blob.type.includes('m4a')) ext = 'm4a';
        else if (blob.type.includes('mpeg')) ext = 'mp3';
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

            await new Promise(resolve => setTimeout(resolve, 400));
            await this.loadMessages();
            this.scrollToBottom();
            await this.pollMessages();
        } catch (e) {
            console.error('Failed to send audio message:', e);
            alert('Failed to send voice message.');
        } finally {
            this._isSendingAudio = false;
        }
    }

    async sendMenuReply(optionText) {
        // Bypass audio state guards — this is always a text reply
        this.state.newMessage = optionText;
        if (this.state.isSending) return;
        if (!this.state.selectedChannel) return;
        this.state.isSending = true;
        try {
            await this.orm.call(
                'discuss.channel',
                'message_post',
                [this.state.selectedChannel.id],
                {
                    body: optionText,
                    message_type: 'whatsapp_message',
                    subtype_xmlid: 'mail.mt_comment',
                }
            );
            this.state.newMessage = '';
            await this.loadMessages();
            this.scrollToBottom();
        } catch (e) {
            console.error('Failed to send menu reply:', e);
        } finally {
            this.state.isSending = false;
        }
    }

    async sendMessage() {
        // If actively recording → stop and send the audio immediately
        if (this.state.isRecording) {
            this.stopAndSendRecording();
            return;
        }
        // If a recorded blob is ready → send it
        if (this.state.recordingBlobUrl) {
            this.sendAudioMessage();
            return;
        }
        // If editing an existing message → update it instead of posting new
        if (this.state.editingMessageId) {
            await this.submitMessageEdit();
            return;
        }
        if (this.state.isSending) return; // prevent double sends
        if ((!this.state.newMessage.trim() && this.state.pendingFiles.length === 0) || !this.state.selectedChannel) return;
        
        this.state.isSending = true;
        const messageBody = this.state.newMessage;
        const pendingFiles = [...this.state.pendingFiles];
        this.state.newMessage = "";
        this.state.pendingFiles = [];
        const replyingToMessageId = this.state.replyingToMessage ? this.state.replyingToMessage.id : null;
        let replyingToMessageBody = null;
        let replyingToAttachment = null;
        let replyingToAuthor = null;
        if (this.state.replyingToMessage) {
            replyingToAuthor = this.state.replyingToMessage.isMe ? 'You' : (this.state.replyingToMessage.authorName || 'Customer');
            replyingToMessageBody = this.state.replyingToMessage.bodyText || 'document';
            if (!this.state.replyingToMessage.bodyText && this.state.replyingToMessage.attachment_ids && this.state.replyingToMessage.attachment_ids.length > 0) {
                replyingToAttachment = this.state.replyingToMessage.attachment_ids[0];
                const mime = replyingToAttachment.mimetype || '';
                if (mime.startsWith('image/')) replyingToMessageBody = 'image';
                else if (mime.startsWith('video/')) replyingToMessageBody = 'video';
                else if (mime.startsWith('audio/')) replyingToMessageBody = 'audio';
                else replyingToMessageBody = 'document';
            }
        }
        this.state.replyingToMessage = null;

        const offlineQueue = JSON.parse(localStorage.getItem('wa_offline_queue') || '[]');

        if (pendingFiles.length === 0) {
            // Text only
            const tempMsgId = 'temp_' + Date.now();
            const tempMsg = {
                id: tempMsgId,
                bodyText: messageBody,
                isMe: true,
                isSystem: false,
                timeText: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                wa_state: 'pending',
                attachment_ids: [],
                quoted_message_id: replyingToMessageId,
                quoted_message_body: replyingToMessageBody,
                quoted_attachment: replyingToAttachment,
                quoted_author: replyingToAuthor
            };
            this.state.messages.push(tempMsg);
            
            offlineQueue.push({
                tempId: tempMsgId,
                channelId: this.state.selectedChannel.id,
                body: messageBody,
                replyingToMessageId: replyingToMessageId,
                files: [],
                timestamp: Date.now()
            });
        } else {
            // One or more files, split into separate messages because WhatsApp API allows only 1 media per message
            for (let i = 0; i < pendingFiles.length; i++) {
                const pendingFile = pendingFiles[i];
                const isFirst = (i === 0);
                const body = isFirst && messageBody.trim() ? messageBody : ' ';
                const tempMsgId = 'temp_' + Date.now() + '_' + i;
                
                const tempMsg = {
                    id: tempMsgId,
                    bodyText: body,
                    isMe: true,
                    isSystem: false,
                    timeText: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    wa_state: 'pending',
                    attachment_ids: [{
                        id: 'temp_att_' + Math.random().toString(36).substr(2, 9),
                        name: pendingFile.name,
                        mimetype: pendingFile.type,
                        dataUrl: pendingFile.dataUrl || null
                    }],
                    quoted_message_id: replyingToMessageId,
                    quoted_message_body: replyingToMessageBody,
                    quoted_attachment: replyingToAttachment,
                    quoted_author: replyingToAuthor
                };
                this.state.messages.push(tempMsg);
                
                offlineQueue.push({
                    tempId: tempMsgId,
                    channelId: this.state.selectedChannel.id,
                    body: body,
                    replyingToMessageId: replyingToMessageId,
                    files: [{
                        name: pendingFile.name,
                        type: pendingFile.type,
                        dataUrl: pendingFile.dataUrl
                    }],
                    timestamp: Date.now() + i
                });
            }
        }
        
        this.scrollToBottom();
        localStorage.setItem('wa_offline_queue', JSON.stringify(offlineQueue));
        this.state.isSending = false;
        
        // Trigger background flush
        this.flushOfflineQueue();
    }
    
    dataURLtoBlob(dataurl) {
        if (!dataurl) return null;
        const arr = dataurl.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = window.atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while(n--){
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new window.Blob([u8arr], {type:mime});
    }

    comingSoon(ev, msg) {
        if (ev) ev.stopPropagation();
        const text = msg || 'Feature coming soon';
        const type = msg ? 'success' : 'info';
        if (this.env && this.env.services && this.env.services.notification) {
            this.env.services.notification.add(text, { type });
        } else {
            alert(text);
        }
    }

    startSelectingMessages(ev) {
        if (ev) ev.stopPropagation();
        this.state.isSelectingMessages = true;
        this.state.selectedMessages = [];
        this.toggleHeaderDropdown();
    }

    cancelSelection(ev) {
        if (ev) ev.stopPropagation();
        this.state.isSelectingMessages = false;
        this.state.selectedMessages = [];
    }

    async flushOfflineQueue() {
        if (!this.state.selectedChannel || this.isFlushing) return;
        this.isFlushing = true;
        try {
            // Flush read queue first
            try {
                const readQueue = JSON.parse(localStorage.getItem('wa_offline_read_queue') || '[]');
                if (readQueue.length > 0) {
                    for (const cid of readQueue) {
                        await this.orm.call("whatsapp.account", "mark_whatsapp_web_messages_read", [cid], {}, { silent: true });
                    }
                    localStorage.setItem('wa_offline_read_queue', '[]');
                }
            } catch(e) {
                console.warn("Failed to flush read queue", e);
            }

            while (true) {
                const queue = JSON.parse(localStorage.getItem('wa_offline_queue') || '[]');
                if (queue.length === 0) break;

                const task = queue[0];
                let attachment_ids = [];

                if (task.files && task.files.length > 0) {
                    try {
                        for (const fileData of task.files) {
                            if (!fileData.dataUrl) continue;
                            const blob = this.dataURLtoBlob(fileData.dataUrl);
                            const formData = new window.FormData();
                            formData.append('csrf_token', window.odoo?.csrf_token || '');
                            formData.append('name', fileData.name);
                            formData.append('ufile', blob, fileData.name);
                            formData.append('model', 'discuss.channel');
                            formData.append('id', task.channelId);

                            const response = await window.fetch('/web/binary/upload_attachment', {
                                method: 'POST',
                                body: formData,
                            });
                            const responseText = await response.text();
                            const match = responseText.match(/\[.*?\]|\{.*?\}/);
                            if (match) {
                                const result = JSON.parse(match[0]);
                                if (Array.isArray(result)) {
                                    attachment_ids.push(...result.map(a => a.id));
                                } else if (result.id) {
                                    attachment_ids.push(result.id);
                                }
                            }
                        }
                    } catch (e) {
                        console.error("Offline attachment upload failed", e);
                        // If attachment upload fails completely, we might need to abort this task or retry later.
                        // For now, if we are offline, fetch will throw. We break the loop and try later.
                        throw e;
                    }
                }

                const kwargs = {
                    body: task.body,
                    message_type: "whatsapp_message",
                    subtype_xmlid: "mail.mt_comment",
                    attachment_ids: attachment_ids
                };
                if (task.replyingToMessageId) {
                    kwargs.parent_id = task.replyingToMessageId;
                }

                try {
                    await this.orm.call(
                        "discuss.channel",
                        "message_post",
                        [task.channelId],
                        kwargs,
                        { silent: true }
                    );

                    // Successfully sent. Remove from queue.
                    const newQueue = JSON.parse(localStorage.getItem('wa_offline_queue') || '[]');
                    newQueue.shift(); // remove first item
                    localStorage.setItem('wa_offline_queue', JSON.stringify(newQueue));

                    // Update UI silently
                    if (this.state.selectedChannel && this.state.selectedChannel.id === task.channelId) {
                        const msgObj = this.state.messages.find(m => m.id === task.tempId);
                        if (msgObj) {
                            msgObj.wa_state = 'sent';
                        }
                    }
                    
                    // Refresh channel list so this chat bubbles to the top
                    await this.loadChannels();
                } catch (e) {
                    // API call failed (offline). Break and retry later.
                    throw e;
                }
            }
        } catch (e) {
            // We failed to send (offline). The interval loop will trigger this again later.
        } finally {
            this.isFlushing = false;
        }
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
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        if (el.value === "") {
            el.style.height = 'auto';
        }
    }

    onTextareaInput(ev) {
        // Auto-resize
        this.onInputResize(ev);
        // If user starts typing while a recording preview is showing, discard it
        if (ev.target.value && this.state.recordingBlobUrl && !this.state.isRecording) {
            this.cancelRecording();
        }
    }

    onTextareaFocus() {
        // Do nothing on focus — don't discard recording just because user clicks the input
    }

    toggleInputEmojiPicker(ev) {
        if (ev) ev.stopPropagation();
        this.state.showInputEmojiPicker = !this.state.showInputEmojiPicker;
    }

    insertEmoji(emoji) {
        this.state.newMessage = (this.state.newMessage || "") + emoji;
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

    openTemplatesModal(tab = 'quick') {
        this.state.showAttachMenu = false;
        this.state.showPlusMenu = false;
        this.state.showTemplatesModal = true;
        this.state.quickReplyTab = (tab === 'templates') ? 'templates' : 'quick';
    }

    closeTemplatesModal() {
        this.state.showTemplatesModal = false;
    }

    // ─── Quick Replies ────────────────────────────────────────────────────────

    async loadQuickReplies() {
        try {
            const accountId = this.state.selectedAccount ? parseInt(this.state.selectedAccount) : null;
            this.state.wa_quick_replies = await this.orm.call(
                'whatsapp.quick.reply',
                'get_quick_replies',
                [],
                { account_id: accountId }
            );
        } catch (e) {
            console.warn('[WA] Could not load quick replies:', e);
            this.state.wa_quick_replies = [];
        }
    }

    async toggleQuickReplyPin(qr, ev) {
        if (ev) ev.stopPropagation();
        qr.is_pinned = !qr.is_pinned;
        try {
            await this.orm.call("whatsapp.quick.reply", "toggle_pin", [[qr.id]]);
            await this.loadQuickReplies();
        } catch (e) {
            console.error("Failed to toggle pin", e);
            qr.is_pinned = !qr.is_pinned; // revert
        }
    }

    async toggleQuickReplyFavorite(qr, ev) {
        if (ev) ev.stopPropagation();
        qr.is_favorite = !qr.is_favorite;
        try {
            await this.orm.call("whatsapp.quick.reply", "toggle_favorite", [[qr.id]]);
            await this.loadQuickReplies();
        } catch (e) {
            console.error("Failed to toggle favorite", e);
            qr.is_favorite = !qr.is_favorite; // revert
        }
    }

    selectQuickReply(qr) {
        this.state.newMessage = (this.state.newMessage || '') + qr.body;
        this.state.showTemplatesModal = false;
    }

    openAddQuickReply() {
        this.state.newQuickReply = { shortcut: '', body: '' };
        this.state.showAddQuickReplyModal = true;
    }

    closeAddQuickReply() {
        this.state.showAddQuickReplyModal = false;
    }

    async saveQuickReply() {
        const { shortcut, body } = this.state.newQuickReply;
        if (!body || !body.trim()) {
            alert('Please enter a message body for the quick reply.');
            return;
        }
        try {
            await this.orm.create('whatsapp.quick.reply', [{
                shortcut: shortcut || false,
                body: body.trim(),
            }]);
            await this.loadQuickReplies();
            this.state.showAddQuickReplyModal = false;
            this.comingSoon(null, 'Quick reply saved!');
        } catch (e) {
            console.error('[WA] Failed to save quick reply:', e);
            alert('Failed to save quick reply.');
        }
    }

    // ─── Emoji Reaction ───────────────────────────────────────────────────────

    openEmojiPicker(msgId, ev) {
        if (ev) ev.stopPropagation();
        this.state.showMessageDropdownId = null;
        const rect = ev && ev.currentTarget ? ev.currentTarget.getBoundingClientRect() : { left: 200, top: 200 };
        this.state.emojiPickerX = Math.min(rect.left, window.innerWidth - 280);
        this.state.emojiPickerY = rect.top - 60;
        this.state.emojiPickerMsgId = msgId;
    }

    closeEmojiPicker() {
        this.state.emojiPickerMsgId = null;
    }

    async reactToMessage(msgId, emoji) {
        this.state.emojiPickerMsgId = null;
        try {
            const res = await this.orm.call(
                "whatsapp.account",
                "send_whatsapp_reaction",
                [msgId, emoji],
                {},
                { silent: true }
            );
            if (res && res.success) {
                // Update the message in state
                const msg = this.state.messages.find(m => m.id === msgId);
                if (msg) msg.wa_reaction_me = emoji;
            } else {
                this.comingSoon(null, `Failed to send reaction: ${res ? res.error : 'Unknown error'}`);
            }
        } catch (e) {
            console.error('[WA] React failed', e);
        }
    }

    // ─── Forward Message ──────────────────────────────────────────────────────

    openForwardModal(msgId) {
        this.state.showMessageDropdownId = null;
        this.state.forwardMessageId = msgId;
        this.state.forwardSearch = '';
    }

    closeForwardModal() {
        this.state.forwardMessageId = null;
    }

    async forwardToChannel(targetChannel) {
        const msgId = this.state.forwardMessageId;
        this.state.forwardMessageId = null;
        if (!msgId || !targetChannel) return;

        const srcMsg = this.state.messages.find(m => m.id === msgId);
        if (!srcMsg) return;

        const body = srcMsg.bodyText || srcMsg.body || '';
        const attachmentIds = srcMsg.attachment_ids ? srcMsg.attachment_ids.map(a => typeof a === 'object' ? a.id : a) : [];

        try {
            await this.orm.call('discuss.channel', 'message_post', [targetChannel.id], {
                body: '↩ Forwarded' + (body ? ': ' + body : ''),
                message_type: 'comment',
                attachment_ids: attachmentIds,
            });
            this.comingSoon(null, `Message forwarded to ${targetChannel.name}`);
        } catch (e) {
            console.error('[WA] Forward failed:', e);
            alert('Failed to forward message.');
        }
    }

    // ─── Disappearing Messages ────────────────────────────────────────────────

    openDisappearingModal() {
        this.state.showDisappearingModal = true;
    }

    closeDisappearingModal() {
        this.state.showDisappearingModal = false;
    }

    async setDisappearingMode(mode) {
        if (!this.state.selectedChannel) return;
        try {
            await this.orm.write('discuss.channel', [this.state.selectedChannel.id], {
                wa_disappearing_mode: mode
            });
            this.state.selectedChannel.wa_disappearing_mode = mode;
        } catch (e) {
            console.error('[WA] Disappearing mode set failed:', e);
        }
        this.state.showDisappearingModal = false;
    }

    // ─── Mute & Block ─────────────────────────────────────────────────────────

    async toggleMuteChat(ev) {
        if (ev) ev.stopPropagation();
        if (!this.state.selectedChannel) return;
        const newVal = !this.state.selectedChannel.wa_is_muted;
        try {
            await this.orm.write('discuss.channel', [this.state.selectedChannel.id], {
                wa_is_muted: newVal
            });
            this.state.selectedChannel.wa_is_muted = newVal;
        } catch (e) {
            console.error('[WA] Mute toggle failed:', e);
        }
        this.state.showHeaderDropdown = false;
    }

    async toggleBlockChat(ev) {
        if (ev) ev.stopPropagation();
        if (this.state.selectedChannel) {
            this.blockContact(this.state.selectedChannel, ev);
        }
    }

    openCatalogueModal() {
        this.state.showAttachMenu = false;
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
            const imgData = product.image_1920 || product.image_128;
            if (imgData) {
                const attachmentId = await this.orm.create("ir.attachment", [{
                    name: product.name + ".jpg",
                    datas: imgData,
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
            
            let body = `📦 *${product.name}*\nPrice: ${price}`;
            if (product.description) {
                body += `\n\n${product.description}`;
            }
            if (product.item_code) {
                body += `\nCode: ${product.item_code}`;
            }
            if (product.url) {
                body += `\nLink: ${product.url}`;
            }
            
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
            this.state.showMediaTabsView = false;
            await this.fetchContactMedia(this.state.selectedChannel.id);
        }
    }

    async viewContactProfile(channel, ev) {
        if (ev) ev.stopPropagation();
        this.state.showChatDropdownId = null;
        this.state.dropdownStyle = "";
        
        // Ensure channel is selected
        if (!this.state.selectedChannel || this.state.selectedChannel.id !== channel.id) {
            await this.selectChannel(channel);
        }
        
        this.state.showContactInfo = true;
        this.state.showMediaTabsView = false;
        await this.fetchContactMedia(channel.id);
    }

    async blockContact(channel, ev) {
        if (ev) ev.stopPropagation();
        this.state.showChatDropdownId = null;
        this.state.dropdownStyle = "";
        this.state.showHeaderDropdown = false;
        
        if (channel.wa_is_blocked) {
            await this.setChatState(channel.id, 'wa_is_blocked', false);
            return;
        }
        
        if (confirm(`Are you sure you want to block ${channel.name}? They will no longer be able to message you.`)) {
            await this.setChatState(channel.id, 'wa_is_blocked', true);
            if (this.state.selectedChannel && this.state.selectedChannel.id === channel.id) {
                this.closeChat();
            }
        }
    }

    async reportContact(channel, ev) {
        if (ev) ev.stopPropagation();
        this.state.showChatDropdownId = null;
        this.state.dropdownStyle = "";
        this.state.showHeaderDropdown = false;
        
        if (confirm(`Report ${channel.name} to WhatsApp? The last 5 messages will be forwarded to WhatsApp. This contact will also be blocked.`)) {
            await this.setChatState(channel.id, 'wa_is_blocked', true);
            if (this.state.selectedChannel && this.state.selectedChannel.id === channel.id) {
                this.closeChat();
            }
        }
    }
    
    getAttachmentIcon(mimetype) {
        if (!mimetype) return 'fa-file-o';
        if (mimetype.includes('pdf')) return 'fa-file-pdf-o';
        if (mimetype.includes('word') || mimetype.includes('document')) return 'fa-file-word-o';
        if (mimetype.includes('excel') || mimetype.includes('spreadsheet')) return 'fa-file-excel-o';
        if (mimetype.includes('powerpoint') || mimetype.includes('presentation')) return 'fa-file-powerpoint-o';
        if (mimetype.includes('zip') || mimetype.includes('compressed')) return 'fa-file-archive-o';
        if (mimetype.includes('text')) return 'fa-file-text-o';
        if (mimetype.includes('image')) return 'fa-file-image-o';
        if (mimetype.includes('video')) return 'fa-file-video-o';
        if (mimetype.includes('audio')) return 'fa-file-audio-o';
        return 'fa-file-o';
    }

    getAttachmentColor(mimetype) {
        if (!mimetype) return '#54656f';
        if (mimetype.includes('pdf')) return '#F40F02'; // Red
        if (mimetype.includes('word') || mimetype.includes('document')) return '#2B579A'; // Blue
        if (mimetype.includes('excel') || mimetype.includes('spreadsheet')) return '#217346'; // Green
        if (mimetype.includes('powerpoint') || mimetype.includes('presentation')) return '#D24726'; // Orange/Red
        if (mimetype.includes('zip') || mimetype.includes('compressed')) return '#ECA31E'; // Yellow
        if (mimetype.includes('text')) return '#666666'; // Grey
        if (mimetype.includes('image')) return '#00A5F4'; // Light Blue
        if (mimetype.includes('video')) return '#9E30FF'; // Purple
        if (mimetype.includes('audio')) return '#FF8C00'; // Orange
        return '#54656f'; // Default WhatsApp grey
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
            
            const msgs = this.messageCache[channelId] || this.state.messages || [];
            const links = [];
            const urlRegex = /(https?:\/\/[^\s<]+)/g;
            for (const m of msgs) {
                if (m.bodyText) {
                    let match;
                    while ((match = urlRegex.exec(m.bodyText)) !== null) {
                        links.push({
                            url: match[1],
                            date: m.dateDate ? m.dateDate.toLocaleDateString() : (m.date || '')
                        });
                    }
                }
            }
            this.state.contactLinks = links;
            if (!this.state.contactMediaTab) {
                this.state.contactMediaTab = 'media';
            }
        } catch(e) {
            console.warn("Failed to fetch media", e);
            this.state.contactMedia = [];
            this.state.contactLinks = [];
        }
    }

    setContactMediaTab(tab) {
        this.state.contactMediaTab = tab;
    }

    async selectTemplate(tmpl) {
        if (!this.state.selectedChannel) return;
        
        this.closeTemplatesModal();
        try {
            const result = await this.orm.call(
                "whatsapp.account",
                "send_whatsapp_template",
                [this.state.selectedChannel.id, tmpl.id],
                {},
                { silent: true }
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
    
    openDeleteModal(messageId) {
        this.state.deleteMessageId = messageId;
        this.state.showMessageDropdownId = null;
    }

    closeDeleteModal() {
        this.state.deleteMessageId = null;
    }

    async copyMessageText(text) {
        if (!text) return;
        try {
            await navigator.clipboard.writeText(text);
            this.state.showMessageDropdownId = null;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            alert("Failed to copy text to clipboard.");
        }
    }

    deleteMessageForMe() {
        const messageId = this.state.deleteMessageId;
        if (!messageId) return;
        
        // Optimistic delete for me (hides it in frontend)
        this.state.messages = this.state.messages.filter(m => m.id !== messageId);
        
        this.closeDeleteModal();
    }

    async confirmDeleteForEveryone() {
        const messageId = this.state.deleteMessageId;
        if (!messageId) return;
        
        if (!this.isAdmin) {
            alert("Only administrators can delete messages.");
            this.closeDeleteModal();
            return;
        }
        
        this.closeDeleteModal();
        
        const result = await this.orm.call("whatsapp.account", "delete_message_for_everyone", [parseInt(messageId)]);
        if (result && result.success) {
            // Remove from state
            this.state.messages = this.state.messages.filter(m => m.id !== messageId);
            if (this.state.selectedChannel && this.state.messages.length > 0) {
                this.state.selectedChannel.last_message_preview = this.state.messages[this.state.messages.length - 1].body;
            } else if (this.state.selectedChannel) {
                this.state.selectedChannel.last_message_preview = "";
            }
            await this.loadChannels();
        } else {
            alert("Could not delete message. " + (result?.error || ""));
        }
    }

    toggleEditContactName() {
        this.state.isEditingContactName = !this.state.isEditingContactName;
        if (this.state.isEditingContactName && this.state.selectedChannel) {
            this.state.editingContactNameValue = this.state.selectedChannel.name || "";
            this.state.editingContactNumberValue = this.state.selectedChannel.customer_phone || this.state.selectedChannel.whatsapp_number || "";
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
        const newNumber = (this.state.editingContactNumberValue || "").trim();
        if (!newName) return;

        try {
            const result = await this.orm.call("whatsapp.account", "update_contact_name", [this.state.selectedChannel.id, newName, newNumber]);
            if (result && result.success) {
                this.state.selectedChannel.name = newName;
                if (newNumber) {
                    this.state.selectedChannel.whatsapp_number = newNumber;
                    this.state.selectedChannel.customer_phone = newNumber;
                }
                this.state.isEditingContactName = false;
                
                // Update in the channels list
                const channelIndex = this.state.channels.findIndex(c => c.id === this.state.selectedChannel.id);
                if (channelIndex !== -1) {
                    this.state.channels[channelIndex].name = newName;
                    if (newNumber) {
                        this.state.channels[channelIndex].whatsapp_number = newNumber;
                        this.state.channels[channelIndex].customer_phone = newNumber;
                    }
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
            this.state.dropdownStyle = "";
        } else {
            this.state.showChatDropdownId = channelId;
            if (ev && ev.currentTarget) {
                const rect = ev.currentTarget.getBoundingClientRect();
                const dropdownHeight = 250; 
                const dropdownWidth = 180;
                let top;
                // If there isn't enough space below, but there is space above, show upwards
                if (window.innerHeight - rect.bottom < dropdownHeight && rect.top > dropdownHeight) {
                    top = rect.top - dropdownHeight; 
                } else {
                    top = rect.bottom; 
                }
                // align to the right of the button
                let left = rect.right - dropdownWidth;
                if (left < 10) left = 10;
                this.state.dropdownStyle = `top: ${top}px; left: ${left}px; width: ${dropdownWidth}px;`;
            }
        }
    }

    toggleHeaderDropdown(ev) {
        if (ev) ev.stopPropagation();
        this.state.showHeaderDropdown = !this.state.showHeaderDropdown;
        if (this.state.showHeaderDropdown) {
            this.state.dropdownUpwards = (ev && ev.clientY > window.innerHeight * 0.6);
        }
    }

    toggleMessageDropdown(msgId, ev) {
        if (ev) ev.stopPropagation();
        if (this.state.showMessageDropdownId === msgId) {
            this.state.showMessageDropdownId = null;
        } else {
            this.state.showMessageDropdownId = msgId;
            this.state.dropdownUpwards = (ev && ev.clientY > window.innerHeight * 0.6);
        }
    }

    notImplemented(ev) {
        if (ev) ev.stopPropagation();
        this.state.showHeaderDropdown = false;
        this.state.showMessageDropdownId = null;
        this.state.showChatDropdownId = null;
        alert("This feature is not yet supported in Odoo.");
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.messagesContainer.el) {
                this.messagesContainer.el.scrollTop = this.messagesContainer.el.scrollHeight;
            }
        }, 100);
    }
    
    scrollToMessage(msgId) {
        setTimeout(() => {
            if (this.messagesContainer.el) {
                const msgs = this.messagesContainer.el.querySelectorAll('.message-row');
                for (let msg of msgs) {
                    if (msg.querySelector('.msg-dropdown-btn') && msg.outerHTML.includes(`toggleMessageDropdown(${msgId}`)) {
                        msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        // Add a temporary highlight class
                        msg.style.transition = "background-color 0.5s ease";
                        const oldBg = msg.style.backgroundColor;
                        msg.style.backgroundColor = "rgba(0, 168, 132, 0.2)";
                        setTimeout(() => {
                            msg.style.backgroundColor = oldBg;
                        }, 1500);
                        break;
                    }
                }
            }
        }, 100);
    }

    async toggleMessageStar(msgId, ev) {
        if (ev) ev.stopPropagation();
        this.state.showMessageDropdownId = null;
        try {
            const res = await this.orm.call(
                "whatsapp.account",
                "toggle_message_star",
                [msgId],
                {},
                { silent: true }
            );
            if (res.success) {
                const msg = this.state.messages.find(m => m.id === msgId);
                if (msg) {
                    msg.wa_is_starred = res.wa_is_starred;
                }
            }
        } catch (e) {
            console.error("Failed to toggle star", e);
        }
    }

    async toggleMessagePin(msgId, ev) {
        if (ev) ev.stopPropagation();
        this.state.showMessageDropdownId = null;
        try {
            const res = await this.orm.call(
                "whatsapp.account",
                "toggle_message_pin",
                [msgId],
                {},
                { silent: true }
            );
            if (res.success) {
                const msg = this.state.messages.find(m => m.id === msgId);
                if (msg) {
                    msg.wa_is_pinned = res.wa_is_pinned;
                }
            }
        } catch (e) {
            console.error("Failed to toggle pin", e);
        }
    }
}

WhatsAppChatsAction.template = "whatsapp_web_chats.ChatsAction";

registry.category("actions").add("whatsapp_web_chats.chats_client_action", WhatsAppChatsAction);
