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
                    <div t-attf-class="nav-item {{ state.activeTab === 'chats' ? 'active' : '' }}" t-on-click="() => this.setTab('chats')" title="Chats"><i class="fa fa-comment-dots"></i></div>
                    <div t-attf-class="nav-item {{ state.activeTab === 'calls' ? 'active' : '' }}" t-on-click="() => this.setTab('calls')" title="Calls"><i class="fa fa-phone"></i></div>
                    <div t-attf-class="nav-item {{ state.activeTab === 'status' ? 'active' : '' }}" t-on-click="() => this.setTab('status')" title="Status"><i class="fa fa-circle-o-notch"></i></div>
                    <div t-attf-class="nav-item {{ state.activeTab === 'communities' ? 'active' : '' }}" t-on-click="() => this.setTab('communities')" title="Communities"><i class="fa fa-users"></i></div>
                </div>
                <div class="nav-rail-bottom">
                    <div t-attf-class="nav-item {{ state.activeTab === 'settings' ? 'active' : '' }}" title="Settings" t-on-click="() => this.setTab('settings')"><i class="fa fa-cog"></i></div>
                    
                    <t t-set="activeAcc" t-value="state.accounts.find(a => a.id.toString() === state.selectedAccount)"/>
                    <t t-if="activeAcc and activeAcc.image_1920">
                        <img t-attf-src="data:image/jpeg;base64,{{activeAcc.image_1920}}" class="nav-avatar" style="object-fit: cover; margin-top: 15px;"/>
                    </t>
                    <t t-else="">
                        <div class="nav-avatar" style="margin-top: 15px;"><i class="fa fa-building"></i></div>
                    </t>
                </div>
            </div>

            <!-- CHATS TAB -->
            <t t-if="state.activeTab === 'chats'">
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
            </t> <!-- END CHATS TAB -->
            
            <!-- OTHER TABS PLACEHOLDERS -->
            <t t-elif="state.activeTab === 'calls'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Calls</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 20px; text-align: center; color: var(--ws-text-muted);">
                         <p>Your call history will appear here.</p>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-phone" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">No recent calls</h2>
                    </div>
                </div>
            </t>

            <t t-elif="state.activeTab === 'status'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Status</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 20px; text-align: center; color: var(--ws-text-muted);">
                        <i class="fa fa-circle-o-notch" style="font-size: 40px; margin-bottom: 15px; color: #dfe5e7;"></i>
                        <p>No recent updates</p>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-circle-o-notch" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">Click on a contact to view their status updates</h2>
                    </div>
                </div>
            </t>

            <t t-elif="state.activeTab === 'communities'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Communities</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 20px; text-align: center; color: var(--ws-text-muted);">
                         <p>Your communities will appear here.</p>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-users" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">Introducing Communities</h2>
                        <p style="color: #667781; font-size: 14px; max-width: 400px; text-align: center;">Easily organize your related groups and send announcements. Now your communities, like neighborhoods or schools, can have their own space.</p>
                    </div>
                </div>
            </t>

            <t t-elif="state.activeTab === 'settings'">
                <div class="whatsapp-sidebar">
                    <div class="whatsapp-header sidebar-header-desktop">
                        <span class="sidebar-title">Settings</span>
                    </div>
                    <div class="whatsapp-chat-list" style="padding: 20px;">
                         <p style="font-weight: bold; margin-bottom: 10px;">Active Account:</p>
                         <t t-if="state.accounts.length > 0">
                             <select class="whatsapp-account-select" t-model="state.selectedAccount" t-on-change="changeChatAccountDropdown" style="width: 100%; max-width: none; border: 1px solid var(--ws-border); padding: 10px; border-radius: 8px;">
                                 <t t-foreach="state.accounts" t-as="acc" t-key="acc.id">
                                     <option t-att-value="acc.id.toString()"><t t-esc="acc.name"/></option>
                                 </t>
                             </select>
                         </t>
                    </div>
                </div>
                <div class="whatsapp-main">
                    <div class="whatsapp-empty">
                        <i class="fa fa-cog" style="font-size: 80px; color: #dfe5e7; margin-bottom: 20px;"></i>
                        <h2 style="color: #41525d; font-weight: 300;">Settings</h2>
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
            activeTab: 'chats', // can be 'chats', 'calls', 'status', 'communities', 'settings'
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

    setTab(tabName) {
        this.state.activeTab = tabName;
    }

    get filteredChannels() {
        if (this.state.activeFilter === 'unread') {
            return this.state.channels.filter(c => c.unread_count > 0);
        }
        if (this.state.activeFilter === 'favourites') {
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
css_path = os.path.join(base, "static", "src", "css", "chats.css")
with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Fix filters overflow
if 'overflow-x: auto;' not in css:
    css = css.replace(
        '.chat-filters {\n    display: flex;\n    gap: 8px;\n    margin-top: 5px;\n    width: 100%;\n    overflow-x: auto;\n    padding-bottom: 5px;\n}',
        '.chat-filters {\n    display: flex;\n    gap: 8px;\n    margin-top: 5px;\n    width: 100%;\n    overflow-x: auto;\n    padding-bottom: 5px;\n    white-space: nowrap;\n}\n.chat-filters::-webkit-scrollbar { display: none; }'
    )

with open(os.path.join(base, "static", "src", "xml", "chats_template.xml"), "w", encoding="utf-8") as f:
    f.write(xml_content)

with open(os.path.join(base, "static", "src", "js", "chats.js"), "w", encoding="utf-8") as f:
    f.write(js_content)
    
with open(css_path, "w", encoding="utf-8") as f:
    f.write(css)

print("Tabs logic and CSS fixes applied.")
