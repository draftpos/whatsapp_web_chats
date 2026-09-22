/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DashboardAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        // Initialize state with default filters (today)
        const today = new Date().toISOString().split('T')[0];
        
        this.state = useState({
            isLoading: true,
            filters: {
                accountId: "",
                dateFrom: today,
                dateTo: today,
            },
            accounts: [],
            stats: {
                new_inbound: 0,
                unreplied_count: 0,
                total_favorites: 0,
                total_contacts: 0,
                total_sent: 0,
                read_count: 0,
                delivered_count: 0,
                not_delivered_count: 0,
            }
        });

        onMounted(() => {
            this.fetchDashboardStats();
        });
    }

    async fetchDashboardStats() {
        this.state.isLoading = true;
        try {
            // Format dates properly for backend if provided
            let dateFrom = this.state.filters.dateFrom ? `${this.state.filters.dateFrom} 00:00:00` : false;
            let dateTo = this.state.filters.dateTo ? `${this.state.filters.dateTo} 23:59:59` : false;
            let accountId = this.state.filters.accountId || false;

            const results = await this.orm.call(
                'whatsapp.dashboard',
                'get_dashboard_stats',
                [],
                {
                    date_from: dateFrom,
                    date_to: dateTo,
                    account_id: accountId
                }
            );

            if (results) {
                this.state.accounts = results.accounts || [];
                this.state.stats = {
                    new_inbound: results.new_inbound || 0,
                    unreplied_count: results.unreplied_count || 0,
                    total_favorites: results.total_favorites || 0,
                    total_contacts: results.total_contacts || 0,
                    total_sent: results.total_sent || 0,
                    read_count: results.read_count || 0,
                    delivered_count: results.delivered_count || 0,
                    not_delivered_count: results.not_delivered_count || 0,
                };
            }
        } catch (error) {
            console.error("Failed to fetch dashboard stats", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    resetFilters() {
        const today = new Date().toISOString().split('T')[0];
        this.state.filters = {
            accountId: "",
            dateFrom: today,
            dateTo: today,
        };
        this.fetchDashboardStats();
    }
}

DashboardAction.template = "whatsapp_web_chats.DashboardAction";

registry.category("actions").add("whatsapp_web_chats.dashboard_action", DashboardAction);
