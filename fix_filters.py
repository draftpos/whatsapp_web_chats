import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"

# 1. Update CSS for Filter Chips
css_path = os.path.join(base, "static", "src", "css", "chats.css")
with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# Make the active filter solid color instead of translucent
css = css.replace(
    'background: rgba(10, 124, 255, 0.15);\n    color: var(--ws-primary);',
    'background: var(--ws-primary) !important;\n    color: white !important;'
)
css = css.replace('border-radius: 16px;', 'border-radius: 20px;')

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css)

# 2. Update XML for Filter Chips structure
xml_path = os.path.join(base, "static", "src", "xml", "chats_template.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    xml = f.read()

old_filters = """<div class="chat-filters">
                            <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'all' ? 'active' : '' }}" t-on-click="() => this.setFilter('all')">All</div>
                            <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'unread' ? 'active' : '' }}" t-on-click="() => this.setFilter('unread')">Unread <t t-if="unreadTotal > 0"><span class="chip-badge"><t t-esc="unreadTotal"/></span></t></div>
                            <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'favourites' ? 'active' : '' }}" t-on-click="() => this.setFilter('favourites')">Favourites</div>
                        </div>"""

new_filters = """<div class="chat-filters">
                            <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'all' ? 'active' : '' }}" t-on-click="() => this.setFilter('all')">All</div>
                            
                            <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'unread' ? 'active' : '' }}" t-on-click="() => this.setFilter('unread')">
                                Unread<t t-if="unreadTotal > 0"><span style="margin-left: 5px; opacity: 0.9;"><t t-esc="unreadTotal"/></span></t>
                            </div>
                            
                            <div t-attf-class="chat-filter-chip {{ state.activeFilter === 'favourites' ? 'active' : '' }}" t-on-click="() => this.setFilter('favourites')">Favourites</div>
                            
                            <div class="chat-filter-chip" style="padding: 6px 12px; cursor: pointer;" title="More options" t-on-click="() => this.setFilter('groups')">
                                <i class="fa fa-caret-down"></i>
                            </div>
                        </div>"""

if "fa-caret-down" not in xml:
    # It might have been formatted slightly differently in the file, let's use regex or just replace the inner content
    import re
    xml = re.sub(r'<div class="chat-filters">.*?</div>\s*</div>\s*<div class="whatsapp-chat-list">', new_filters + '\n                    </div>\n\n                    <div class="whatsapp-chat-list">', xml, flags=re.DOTALL)
    
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml)

print("Filters updated successfully.")
