/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class DashboardAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        this.lineChartCanvas = useRef("lineChartCanvas");
        this.doughnutChartCanvas = useRef("doughnutChartCanvas");
        this.charts = { line: null, doughnut: null };
        
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
                inbound_media: {images: 0, videos: 0, documents: 0},
                outbound_media: {images: 0, videos: 0, documents: 0},
                total_chats_active: 0,
                replied_chats_count: 0,
                not_replied_chats_count: 0,
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
                    inbound_media: results.inbound_media || {images: 0, videos: 0, documents: 0},
                    outbound_media: results.outbound_media || {images: 0, videos: 0, documents: 0},
                    total_chats_active: results.total_chats_active || 0,
                    replied_chats_count: results.replied_chats_count || 0,
                    not_replied_chats_count: results.not_replied_chats_count || 0,
                };
                
                // Render charts after state update
                setTimeout(async () => {
                    await loadJS("/web/static/lib/Chart/Chart.js");
                    this.renderCharts(results.timeseries);
                }, 100);
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
    
    viewErrorLogs() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Failed WhatsApp Messages",
            res_model: "whatsapp.message",
            views: [[false, "list"], [false, "form"]],
            view_mode: "list,form",
            domain: [['state', 'in', ['error', 'cancel', 'bounced']]],
            target: "current",
        });
    }

    renderCharts(timeseries) {
        const ChartJS = window.Chart || (typeof Chart !== 'undefined' ? Chart : null);
        if (!ChartJS) return;
        
        if (this.charts.line) this.charts.line.destroy();
        if (this.charts.doughnut) this.charts.doughnut.destroy();

        // Prepare line chart data
        let labels = [];
        let inboundData = [];
        let outboundData = [];
        
        if (timeseries) {
            // Merge all dates from both inbound and outbound
            let dateSet = new Set();
            timeseries.inbound.forEach(d => dateSet.add(d.date));
            timeseries.outbound.forEach(d => dateSet.add(d.date));
            
            // Try to parse dates to sort them chronologically, fallback to string sort
            labels = Array.from(dateSet).sort((a, b) => {
                const dateA = new Date(a);
                const dateB = new Date(b);
                if (!isNaN(dateA) && !isNaN(dateB)) {
                    return dateA - dateB;
                }
                return a.localeCompare(b);
            });
            
            labels.forEach(date => {
                const inb = timeseries.inbound.find(d => d.date === date);
                const outb = timeseries.outbound.find(d => d.date === date);
                inboundData.push(inb ? inb.count : 0);
                outboundData.push(outb ? outb.count : 0);
            });
            
            // Format labels for readability (e.g., "Sep 23")
            labels = labels.map(label => {
                const d = new Date(label);
                if (!isNaN(d)) {
                    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }
                return label;
            });
        }

        // Render Line Chart
        if (this.lineChartCanvas.el) {
            this.charts.line = new ChartJS(this.lineChartCanvas.el, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Inbound',
                            data: inboundData,
                            borderColor: '#25D366',
                            backgroundColor: 'rgba(37, 211, 102, 0.15)',
                            borderWidth: 3,
                            pointBackgroundColor: '#25D366',
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Outbound',
                            data: outboundData,
                            borderColor: '#4285f4',
                            backgroundColor: 'rgba(66, 133, 244, 0.15)',
                            borderWidth: 3,
                            pointBackgroundColor: '#4285f4',
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false,
                    tooltips: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(17, 27, 33, 0.95)',
                        titleFontSize: 14,
                        titleFontStyle: 'bold',
                        bodyFontSize: 13,
                        xPadding: 12,
                        yPadding: 12,
                        cornerRadius: 8
                    },
                    legend: {
                        labels: {
                            fontSize: 14,
                            fontColor: '#54656f',
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    scales: {
                        xAxes: [{
                            gridLines: { display: false },
                            ticks: {
                                fontColor: '#8696a0',
                                fontSize: 12,
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }],
                        yAxes: [{
                            gridLines: {
                                color: 'rgba(0, 0, 0, 0.05)',
                                drawBorder: false
                            },
                            ticks: {
                                beginAtZero: true,
                                fontColor: '#8696a0',
                                fontSize: 12,
                                stepSize: 1,
                                precision: 0
                            }
                        }]
                    }
                }
            });
        }

        // Render Doughnut Chart
        if (this.doughnutChartCanvas.el) {
            this.charts.doughnut = new ChartJS(this.doughnutChartCanvas.el, {
                type: 'doughnut',
                data: {
                    labels: ['Read', 'Delivered', 'Failed/Other'],
                    datasets: [{
                        data: [
                            this.state.stats.read_count, 
                            this.state.stats.delivered_count, 
                            this.state.stats.not_delivered_count
                        ],
                        backgroundColor: ['#4285f4', '#fbbc04', '#ea4335'],
                        borderWidth: 0
                    }]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false,
                    cutoutPercentage: 75,
                    legend: { display: false },
                    tooltips: {
                        backgroundColor: 'rgba(17, 27, 33, 0.95)',
                        bodyFontSize: 13,
                        xPadding: 10,
                        yPadding: 10,
                        cornerRadius: 8
                    }
                }
            });
        }
    }
}

DashboardAction.template = "whatsapp_web_chats.DashboardAction";

registry.category("actions").add("whatsapp_web_chats.dashboard_action", DashboardAction);
