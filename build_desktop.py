import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# ================= XML =================
xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="whatsapp_wedsphere.ChatsAction" owl="1">
        <div t-attf-class="whatsapp-container {{ state.selectedChannel ? 'chat-active' : 'chat-inactive' }}">
            
            <!-- FAR LEFT NAV RAIL -->
            <div class="whatsapp-nav-rail">
                <div class="nav-rail-top">
                    <div class="nav-item active"><i class="fa fa-comment-dots"></i></div>
                    <div class="nav-item"><i class="fa fa-phone"></i></div>
                    <div class="nav-item"><i class="fa fa-circle-o-notch"></i></div>
                    <div class="nav-item"><i class="fa fa-users"></i></div>
                </div>
                <div class="nav-rail-bottom">
                    <div class="nav-item"><i class="fa fa-cog"></i></div>
                    
                    <t t-set="activeAcc" t-value="state.accounts.find(a => a.id.toString() === state.selectedAccount)"/>
                    <t t-if="activeAcc and activeAcc.image_1920">
                        <img t-attf-src="data:image/jpeg;base64,{{activeAcc.image_1920}}" class="nav-avatar" style="object-fit: cover; margin-top: 15px;"/>
                    </t>
                    <t t-else="">
                        <div class="nav-avatar" style="margin-top: 15px;"><i class="fa fa-building"></i></div>
                    </t>
                </div>
            </div>

            <!-- CHATS SIDEBAR -->
            <div class="whatsapp-sidebar">
                <div class="whatsapp-header sidebar-header-desktop">
                    <div class="sidebar-header-top">
                        <span class="sidebar-title">Chats</span>
                        <div class="header-actions">
                            <i class="fa fa-ellipsis-v"></i>
                            <i class="fa fa-plus new-chat-fab" title="New Chat" t-on-click="openNewChatModal"></i>
                        </div>
                    </div>
                    
                    <div class="sidebar-search">
                        <div class="search-box">
                            <i class="fa fa-search"></i>
                            <input type="text" placeholder="Search unread chats"/>
                        </div>
                    </div>
                    
                    <div class="chat-filters">
                        <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'all' ? 'active' : '' }}" t-on-click="() => this.setFilter('all')">All</div>
                        <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'unread' ? 'active' : '' }}" t-on-click="() => this.setFilter('unread')">Unread <t t-if="unreadTotal > 0"><span class="chip-badge"><t t-esc="unreadTotal"/></span></t></div>
                        <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'favourites' ? 'active' : '' }}" t-on-click="() => this.setFilter('favourites')">Favourites</div>
                    </div>
                </div>

                <div class="whatsapp-chat-list">
                    <t t-foreach="filteredChannels" t-as="channel" t-key="channel.id">
                        <div t-attf-class="whatsapp-chat-item {{ state.selectedChannel and state.selectedChannel.id === channel.id ? 'active' : '' }}" t-on-click="(ev) => this.selectChannel(channel, ev)">
                            <div class="chat-avatar-container">
                                <div class="chat-avatar"><t t-esc="(channel.name and channel.name.length > 0) ? channel.name[0].toUpperCase() : '?'"/></div>
                            </div>
                            <div class="chat-info">
                                <div class="chat-name-row" style="display:flex; justify-content:space-between; align-items:center; width: 100%;">
                                    <div class="chat-name"><t t-esc="channel.name || 'Unknown'"/></div>
                                    <div class="chat-time"><t t-esc="channel.last_message_date"/></div>
                                </div>
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-top: 5px;">
                                    <div class="chat-preview" t-out="channel.last_message_body || 'Start chatting...'"/>
                                    <t t-if="channel.unread_count > 0">
                                        <div class="unread-badge"><t t-esc="channel.unread_count"/></div>
                                    </t>
                                </div>
                            </div>
                        </div>
                    </t>
                </div>
            </div>
            
            <!-- MAIN CHAT PANEL -->
            <div class="whatsapp-main">
                <t t-if="state.selectedChannel">
                    <div class="whatsapp-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center;">
                            <i class="fa fa-arrow-left mobile-back-btn" t-on-click="closeChat" style="margin-right: 15px; font-size: 18px; color: var(--ws-text-muted); cursor: pointer;"></i>
                            <div class="chat-avatar" style="margin-right: 15px;"><t t-esc="(state.selectedChannel.name and state.selectedChannel.name.length > 0) ? state.selectedChannel.name[0].toUpperCase() : '?'"/></div>
                            <span class="chat-header-name"><t t-esc="state.selectedChannel.name || 'Unknown'"/></span>
                        </div>
                        <div class="header-actions" style="display: flex; gap: 20px; color: var(--ws-text-muted); font-size: 18px; margin-right: 15px;">
                            <i class="fa fa-exchange" title="Transfer Chat" t-on-click="openTransferModal" style="cursor: pointer; transition: color 0.2s;" onmouseover="this.style.color='var(--ws-primary)'" onmouseout="this.style.color='var(--ws-text-muted)'"></i>
                            <i class="fa fa-search" style="cursor: pointer;"></i>
                            <i class="fa fa-ellipsis-v" style="cursor: pointer;"></i>
                        </div>
                    </div>
                    <div class="whatsapp-messages" t-ref="messagesContainer">
                        <t t-foreach="state.messages" t-as="msg" t-key="msg.id">
                            <div t-attf-class="message-row {{ msg.isMe ? 'message-me' : 'message-other' }}">
                                <div class="message-bubble">
                                    <div class="message-body" t-out="msg.bodyText"/>
                                    <span class="msg-time"><t t-esc="msg.timeStr"/></span>
                                </div>
                            </div>
                        </t>
                    </div>
                    <div class="whatsapp-input-area">
                        <i class="fa fa-plus" style="font-size: 20px; color: var(--ws-text-muted); cursor: pointer; padding: 10px;"></i>
                        <textarea class="whatsapp-input" t-model="state.newMessage" placeholder="Type a message" t-on-keydown="onKeydown" rows="1"></textarea>
                        <button class="whatsapp-send-btn" t-on-click="sendMessage">
                            <i class="fa fa-paper-plane"/>
                        </button>
                    </div>
                </t>
                <t t-else="">
                    <div class="whatsapp-empty">
                        <div class="empty-state-content">
                            <i class="fa fa-whatsapp" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                            <h2 style="color: #41525d; font-weight: 300; font-size: 32px; margin-bottom: 15px;">WhatsApp Wedsphere</h2>
                            <p style="color: #667781; font-size: 14px; max-width: 400px; text-align: center; margin-bottom: 30px; line-height: 20px;">
                                Send and receive messages directly in Odoo without keeping your phone online.
                            </p>
                            <button class="btn btn-primary start-chat-btn" t-on-click="openNewChatModal">
                                <i class="fa fa-plus-circle" style="margin-right: 8px;"></i> Start New Chat
                            </button>
                        </div>
                        <div style="position: absolute; bottom: 40px; color: #8696a0; font-size: 13px; display: flex; align-items: center;">
                            <i class="fa fa-lock" style="margin-right: 5px;"></i> End-to-end encrypted
                        </div>
                    </div>
                </t>
            </div>
            
            <!-- Transfer Chat Modal -->
            <t t-if="state.isTransferModalOpen">
                <div class="modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); backdrop-filter: blur(5px); z-index: 9999; display: flex; align-items: center; justify-content: center;">
                    <div class="modal-content" style="background: white; width: 450px; border-radius: 16px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 16px 40px rgba(0,0,0,0.12); border: 1px solid rgba(0,0,0,0.05);">
                        <div class="modal-header" style="background: #ffffff; color: var(--ws-text-main); padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f0f2f5;">
                            <span style="font-size: 18px; font-weight: 700;">Transfer Chat</span>
                            <i class="fa fa-times" style="cursor: pointer; color: #8696a0; font-size: 20px;" t-on-click="closeTransferModal"></i>
                        </div>
                        <div class="modal-body" style="padding: 24px; background: white; max-height: 400px; overflow-y: auto;">
                            <p style="color: #8696a0; font-size: 14px; margin-bottom: 15px;">Select an agent to transfer this chat to:</p>
                            <t t-foreach="state.users" t-as="user" t-key="user.id">
                                <div class="user-transfer-item" t-on-click="() => this.transferChat(user.id)" style="padding: 12px; border-bottom: 1px solid #f0f2f5; display: flex; align-items: center; cursor: pointer;">
                                    <div class="chat-avatar" style="width: 35px; height: 35px; margin-right: 15px; font-size: 14px;"><t t-esc="user.name[0].toUpperCase()"/></div>
                                    <span style="font-size: 15px; font-weight: 500; color: var(--ws-text-main);"><t t-esc="user.name"/></span>
                                </div>
                            </t>
                        </div>
                    </div>
                </div>
            </t>
            
            <!-- New Chat Modal -->
            <t t-if="state.isNewChatModalOpen">
                <div class="modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); backdrop-filter: blur(5px); z-index: 9999; display: flex; align-items: center; justify-content: center;">
                    <div class="modal-content" style="background: white; width: 450px; border-radius: 16px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 16px 40px rgba(0,0,0,0.12); border: 1px solid rgba(0,0,0,0.05);">
                        <div class="modal-header" style="background: #ffffff; color: var(--ws-text-main); padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #f0f2f5;">
                            <span style="font-size: 18px; font-weight: 700;">New Chat</span>
                            <i class="fa fa-times" style="cursor: pointer; color: #8696a0; font-size: 20px; transition: color 0.2s;" t-on-click="closeNewChatModal" onmouseover="this.style.color='#f24a4a'" onmouseout="this.style.color='#8696a0'"></i>
                        </div>
                        <div class="modal-search" style="padding: 15px 24px; border-bottom: 1px solid #f0f2f5; background: #ffffff;">
                            <div class="search-box">
                                <i class="fa fa-search" style="color: #8696a0; margin-left: 10px;"></i>
                                <input type="text" class="form-control" t-model="state.newNumberQuery" placeholder="Search contacts or enter phone number..." style="border-radius: 8px; border: none; padding: 10px 10px 10px 15px; outline: none; width: 100%; background: #f0f2f5; font-size: 15px;"/>
                            </div>
                        </div>
                        <div class="modal-body" style="padding: 24px; background: white; min-height: 150px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                            <t t-if="state.newNumberQuery">
                                <button class="btn btn-primary start-chat-btn" t-on-click="startChatWithNumber" style="width: 100%; justify-content: center;">
                                    Start chat with <t t-esc="state.newNumberQuery"/>
                                </button>
                            </t>
                            <t t-else="">
                                <p style="color: #8696a0; font-size: 14px; text-align: center;">Enter a phone number above to start a chat.</p>
                            </t>
                        </div>
                    </div>
                </div>
            </t>

        </div>
    </t>
</templates>"""

# ================= JS =================
js_content = """/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillDestroy, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class ChatsAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.messagesContainer = useRef("messagesContainer");
        
        this.state = useState({
            channels: [],
            selectedChannel: null,
            messages: [],
            newMessage: "",
            accounts: [],
            selectedAccount: null,
            isNewChatModalOpen: false,
            newNumberQuery: "",
            isTransferModalOpen: false,
            users: [],
            activeFilter: 'all', // can be 'all', 'unread', 'favourites'
        });
        
        onMounted(() => {
            window.addEventListener("keydown", this.onGlobalKeydown.bind(this));
        });
        onWillDestroy(() => {
            window.removeEventListener("keydown", this.onGlobalKeydown.bind(this));
        });

        onWillStart(async () => {
            await this.loadAccounts();
            await this.loadChannels();
        });
    }

    get filteredChannels() {
        if (this.state.activeFilter === 'unread') {
            return this.state.channels.filter(c => c.unread_count > 0);
        }
        if (this.state.activeFilter === 'favourites') {
            // Implementation detail for later, return empty or mock
            return []; 
        }
        return this.state.channels;
    }

    get unreadTotal() {
        return this.state.channels.filter(c => c.unread_count > 0).length;
    }

    setFilter(filterName) {
        this.state.activeFilter = filterName;
    }

    onGlobalKeydown(ev) {
        if (ev.key === "Escape") {
            this.closeChat();
        }
    }
    
    closeChat() {
        this.state.selectedChannel = null;
    }

    async loadAccounts() {
        this.state.accounts = await this.orm.searchRead("wasphere.account", [], ["id", "name"]);
        if (this.state.accounts.length > 0) {
            this.state.selectedAccount = this.state.accounts[0].id.toString();
        }
    }

    async changeChatAccountDropdown(ev) {
        this.state.selectedAccount = ev.target.value;
        await this.loadChannels();
    }

    async loadChannels() {
        if (!this.state.selectedAccount) return;
        const channels = await this.orm.call(
            "discuss.channel",
            "get_wasphere_channels",
            [parseInt(this.state.selectedAccount)]
        );
        this.state.channels = channels;
    }

    async selectChannel(channel, event) {
        this.state.selectedChannel = channel;
        await this.orm.call("discuss.channel", "mark_channel_read", [channel.id]);
        channel.unread_count = 0;
        await this.loadMessages();
    }

    async loadMessages() {
        if (!this.state.selectedChannel) return;
        
        const channelId = this.state.selectedChannel.id;
        
        // Load odoo discuss messages for this channel
        const msgs = await this.orm.searchRead(
            "mail.message",
            [["res_id", "=", channelId], ["model", "=", "discuss.channel"], ["message_type", "=", "comment"]],
            ["id", "body", "author_id", "date"],
            { order: 'id asc' }
        );
        
        this.state.messages = msgs.map(msg => {
            let tmp = document.createElement("DIV");
            tmp.innerHTML = msg.body || "";
            let isMe = msg.author_id ? true : false;
            
            return {
                id: msg.id,
                bodyText: tmp.textContent || tmp.innerText || "",
                isMe: isMe,
                timeStr: new Date(msg.date).toLocaleTimeString([], {hour: "2-digit", minute:"2-digit"})
            };
        });
        
        this.scrollToBottom();
    }

    async sendMessage() {
        if (!this.state.newMessage.trim() || !this.state.selectedChannel || !this.state.selectedAccount) return;
        
        const messageBody = this.state.newMessage;
        this.state.newMessage = "";

        // 1. Post internally to discuss.channel
        await this.orm.call(
            "discuss.channel",
            "message_post",
            [this.state.selectedChannel.id],
            {
                body: messageBody,
                message_type: "comment",
                subtype_xmlid: "mail.mt_comment",
            }
        );
        
        // 2. Outbound to Wasphere
        await this.orm.create("wasphere.message", [{
            account_id: parseInt(this.state.selectedAccount),
            phone_number: this.state.selectedChannel.whatsapp_number,
            message_type: 'outbound',
            body: messageBody
        }]);
        
        const records = await this.orm.searchRead("wasphere.message", [["account_id", "=", parseInt(this.state.selectedAccount)], ["phone_number", "=", this.state.selectedChannel.whatsapp_number]], ["id"], { order: 'id desc', limit: 1 });
        if(records.length > 0) {
            await this.orm.call("wasphere.message", "send_via_wasphere", [records[0].id]);
        }
        
        await this.loadMessages();
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            if (this.messagesContainer.el) {
                this.messagesContainer.el.scrollTop = this.messagesContainer.el.scrollHeight;
            }
        }, 100);
    }
    
    openNewChatModal() {
        this.state.isNewChatModalOpen = true;
        this.state.newNumberQuery = "";
    }

    closeNewChatModal() {
        this.state.isNewChatModalOpen = false;
    }

    async startChatWithNumber() {
        if (!this.state.selectedAccount || !this.state.newNumberQuery) return;
        
        const number = this.state.newNumberQuery.replace(/\D/g,'');
        if (!number) {
            alert("Please enter a valid numeric phone number.");
            return;
        }

        try {
            const result = await this.orm.call(
                "wasphere.account",
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
                alert("Failed to start chat: " + (result.error || "Unknown error"));
            }
        } catch (e) {
            console.error("Failed to start new chat", e);
        }
    }

    async openTransferModal() {
        this.state.isTransferModalOpen = true;
        this.state.users = await this.orm.searchRead("res.users", [["active", "=", true]], ["id", "name"]);
    }

    closeTransferModal() {
        this.state.isTransferModalOpen = false;
    }

    async transferChat(userId) {
        if (!this.state.selectedChannel) return;
        try {
            await this.orm.call(
                "discuss.channel",
                "transfer_whatsapp_chat",
                [this.state.selectedChannel.id, userId]
            );
            this.closeTransferModal();
            this.state.selectedChannel = null;
            await this.loadChannels();
        } catch (e) {
            console.error("Transfer failed", e);
        }
    }
}

ChatsAction.template = "whatsapp_wedsphere.ChatsAction";
registry.category("actions").add("whatsapp_wedsphere.chats_client_action", ChatsAction);
"""

# ================= CSS =================
css_content = """/** @odoo-module **/

:root {
    --ws-primary: #0A7CFF;
    --ws-primary-light: #4A9FFF;
    --ws-bg-main: #f0f2f5;
    --ws-bg-sidebar: #ffffff;
    --ws-bg-nav: #f0f2f5;
    --ws-bg-chat: #efeae2;
    --ws-text-main: #111b21;
    --ws-text-muted: #667781;
    --ws-border: #e9ecef;
    --ws-bubble-in: #ffffff;
    --ws-bubble-out: #d9fdd3;
    --glass-bg: rgba(255, 255, 255, 0.85);
    --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
}

.whatsapp-container {
    display: flex;
    height: 100%;
    width: 100%;
    background-color: var(--ws-bg-main);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--ws-text-main);
}

/* NEW NAV RAIL */
.whatsapp-nav-rail {
    width: 60px;
    background-color: var(--ws-bg-nav);
    border-right: 1px solid var(--ws-border);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 15px 0;
    z-index: 11;
}

.nav-rail-top, .nav-rail-bottom {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
}

.nav-item {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--ws-text-muted);
    font-size: 20px;
    cursor: pointer;
    transition: all 0.2s;
}

.nav-item:hover {
    background-color: rgba(0,0,0,0.05);
}

.nav-item.active {
    background-color: rgba(10, 124, 255, 0.1);
    color: var(--ws-primary);
}

.nav-avatar {
    width: 35px;
    height: 35px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--ws-primary-light) 0%, var(--ws-primary) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 14px;
}

.whatsapp-sidebar {
    width: 350px;
    max-width: 350px;
    background-color: var(--ws-bg-sidebar);
    border-right: 1px solid var(--ws-border);
    display: flex;
    flex-direction: column;
    z-index: 10;
}

.whatsapp-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: var(--ws-bg-chat);
    background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');
    background-size: cover;
    background-position: center;
    position: relative;
}

.whatsapp-main::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(255,255,255,0.7);
    z-index: 0;
}

/* NEW SIDEBAR HEADER STRUCTURE */
.sidebar-header-desktop {
    flex-direction: column;
    height: auto;
    align-items: flex-start;
    padding: 15px 20px;
}

.sidebar-header-top {
    display: flex;
    justify-content: space-between;
    width: 100%;
    align-items: center;
    margin-bottom: 10px;
}

.sidebar-title {
    font-size: 22px;
    font-weight: 700;
}

.new-chat-fab {
    font-size: 24px !important;
    color: var(--ws-primary);
}

.sidebar-search {
    width: 100%;
    padding: 10px 0;
}

.chat-filters {
    display: flex;
    gap: 8px;
    margin-top: 5px;
    width: 100%;
    overflow-x: auto;
    padding-bottom: 5px;
}

.chat-filter-chip {
    background: #f0f2f5;
    padding: 6px 14px;
    border-radius: 16px;
    font-size: 14px;
    font-weight: 500;
    color: var(--ws-text-muted);
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 5px;
}

.chat-filter-chip:hover {
    background: #e4e6eb;
}

.chat-filter-chip.active {
    background: rgba(10, 124, 255, 0.15);
    color: var(--ws-primary);
}

.chip-badge {
    background: var(--ws-primary);
    color: white;
    font-size: 11px;
    padding: 1px 5px;
    border-radius: 10px;
}

/* EXISTING CSS */
.whatsapp-header {
    height: 70px;
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px;
    box-sizing: border-box;
    border-bottom: 1px solid rgba(255,255,255,0.3);
    z-index: 1;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
}

.search-box {
    display: flex;
    align-items: center;
    background: #f0f2f5;
    border-radius: 8px;
    padding: 6px 12px;
    transition: all 0.2s;
}
.search-box:focus-within {
    background: #ffffff;
    box-shadow: 0 0 0 1px var(--ws-primary-light);
}
.search-box input {
    border: none;
    background: transparent;
    width: 100%;
    padding: 4px 8px;
    outline: none;
    font-size: 14px;
    color: var(--ws-text-main);
}
.whatsapp-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background-color: var(--ws-bg-chat);
    position: relative;
    z-index: 1;
}
.empty-state-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.start-chat-btn {
    background: linear-gradient(135deg, var(--ws-primary) 0%, var(--ws-primary-light) 100%);
    border: none;
    border-radius: 24px;
    padding: 12px 28px;
    font-weight: 600;
    font-size: 15px;
    color: white;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(10,124,255,0.3);
    transition: all 0.2s;
    display: flex;
    align-items: center;
}
.start-chat-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(10,124,255,0.4);
}
.start-chat-btn:active {
    transform: translateY(0);
}
.chat-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--ws-primary-light) 0%, var(--ws-primary) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 700;
    color: #fff;
    box-shadow: 0 4px 10px rgba(10,124,255,0.2);
    border: 2px solid white;
}
.header-actions i {
    cursor: pointer;
    transition: color 0.2s;
    padding: 8px;
    border-radius: 50%;
}
.header-actions i:hover {
    background-color: #f0f2f5;
}

.chat-header-name {
    font-weight: 700;
    font-size: 17px;
}

.whatsapp-chat-list {
    flex: 1;
    overflow-y: auto;
    background: var(--ws-bg-sidebar);
    padding: 10px;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.2); }

.whatsapp-chat-item {
    display: flex;
    align-items: center;
    padding: 10px 15px;
    height: 75px;
    cursor: pointer;
    background-color: var(--ws-bg-sidebar);
    border-radius: 16px;
    margin-bottom: 5px;
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    position: relative;
    border: 1px solid transparent;
}

.whatsapp-chat-item:hover {
    background-color: var(--ws-bg-main);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.whatsapp-chat-item.active {
    background-color: rgba(10, 124, 255, 0.08);
    border-color: rgba(10, 124, 255, 0.2);
}

.chat-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.chat-name {
    font-size: 16px;
    font-weight: 600;
    color: var(--ws-text-main);
}

.whatsapp-messages {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    z-index: 1;
}

.message-row {
    display: flex;
    margin-bottom: 15px;
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.message-me { justify-content: flex-end; }
.message-other { justify-content: flex-start; }

.message-bubble {
    max-width: 65%;
    padding: 12px 16px;
    border-radius: 18px;
    position: relative;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    font-size: 15px;
    line-height: 1.5;
}

.message-me .message-bubble {
    background: linear-gradient(145deg, #e3f2fd, #bbdefb);
    border-bottom-right-radius: 4px;
    color: #0d47a1;
}

.message-other .message-bubble {
    background-color: var(--ws-bubble-in);
    border-bottom-left-radius: 4px;
}

.whatsapp-input-area {
    min-height: 80px;
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    padding: 15px 25px;
    box-sizing: border-box;
    border-top: 1px solid rgba(255,255,255,0.4);
    z-index: 1;
    box-shadow: 0 -4px 15px rgba(0,0,0,0.02);
}

.whatsapp-input {
    flex: 1;
    min-height: 50px;
    max-height: 120px;
    border-radius: 25px;
    border: 1px solid var(--ws-border);
    background-color: #ffffff;
    padding: 14px 24px;
    font-size: 15px;
    margin: 0 20px;
    box-sizing: border-box;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    resize: none;
    overflow-y: auto;
    color: var(--ws-text-main) !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.whatsapp-input:focus {
    outline: none;
    border-color: var(--ws-primary-light);
    box-shadow: 0 0 0 4px rgba(10, 124, 255, 0.15);
    background-color: #ffffff;
}

.whatsapp-send-btn, .whatsapp-attach-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 24px;
    color: var(--ws-text-muted);
    padding: 12px;
    display: flex;
    align-items: center;
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
    border-radius: 50%;
}

.whatsapp-send-btn:hover, .whatsapp-attach-btn:hover {
    color: var(--ws-primary);
    background-color: rgba(10, 124, 255, 0.1);
    transform: scale(1.05);
}

.whatsapp-send-btn:active {
    transform: scale(0.95);
}

.unread-badge {
    background-color: var(--ws-primary);
    color: white;
    border-radius: 10px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: bold;
    min-width: 18px;
    text-align: center;
}
.chat-preview {
    font-size: 13px;
    color: var(--ws-text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 200px;
}
.chat-time {
    font-size: 11px;
    color: var(--ws-text-muted);
}
.msg-time {
    font-size: 10px;
    color: rgba(0,0,0,0.45);
    align-self: flex-end;
    margin-top: 4px;
    margin-left: 10px;
}
.message-me .msg-time {
    color: rgba(13, 71, 161, 0.6);
}

.mobile-back-btn {
    display: none;
}

@media (max-width: 768px) {
    .whatsapp-nav-rail {
        display: none !important;
    }
    
    .whatsapp-container.chat-active .whatsapp-sidebar { display: none !important; }
    .whatsapp-container.chat-active .whatsapp-main { display: flex !important; width: 100% !important; }
    
    .whatsapp-container.chat-inactive .whatsapp-sidebar { display: flex !important; width: 100% !important; max-width: none !important; }
    .whatsapp-container.chat-inactive .whatsapp-main { display: none !important; }
    
    .mobile-back-btn { display: block !important; }
}
"""

with open(os.path.join(base, "static", "src", "xml", "chats_template.xml"), "w", encoding="utf-8") as f:
    f.write(xml_content)

with open(os.path.join(base, "static", "src", "js", "chats.js"), "w", encoding="utf-8") as f:
    f.write(js_content)
    
with open(os.path.join(base, "static", "src", "css", "chats.css"), "w", encoding="utf-8") as f:
    f.write(css_content)

print("Desktop 3-pane layout applied.")
