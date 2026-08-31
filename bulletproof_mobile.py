import os
import re

base = r"C:\odoo19\addons\whatsapp_wedsphere"
css_path = os.path.join(base, "static", "src", "css", "chats.css")

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# 1. Remove all existing @media (max-width: 768px) blocks
css_clean = re.sub(r'@media \(max-width: 768px\) \{[\s\S]*?^\}', '', css, flags=re.MULTILINE)

# 2. Append the single bulletproof mobile block
mobile_block = """
@media (max-width: 768px) {
    /* Main container is full screen and standard column (top-to-bottom) */
    .whatsapp-container {
        display: flex !important;
        flex-direction: column !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        height: 100% !important;
        width: 100% !important;
        z-index: 99999 !important;
        background: var(--ws-bg-main) !important;
    }

    /* 1. Sidebar (List view) - Takes remaining space at Top (Order 1) */
    .whatsapp-container.chat-inactive .whatsapp-sidebar {
        display: flex !important;
        flex: 1 !important;
        width: 100% !important;
        max-width: 100% !important;
        order: 1 !important;
    }
    .whatsapp-container.chat-active .whatsapp-sidebar {
        display: none !important;
    }

    /* 2. Main (Chat view) - Takes remaining space at Top (Order 1) */
    .whatsapp-container.chat-inactive .whatsapp-main {
        display: none !important;
    }
    .whatsapp-container.chat-active .whatsapp-main {
        display: flex !important;
        flex: 1 !important;
        width: 100% !important;
        order: 1 !important;
    }

    /* 3. Nav Rail (Bottom Tab Bar) - Fixed at Bottom (Order 2) */
    .whatsapp-nav-rail {
        display: flex !important;
        flex-direction: row !important;
        width: 100% !important;
        height: 60px !important;
        min-height: 60px !important;
        background: var(--ws-bg-sidebar) !important;
        border-top: 1px solid var(--ws-border) !important;
        border-right: none !important;
        order: 2 !important;
        padding: 0 !important;
    }
    
    /* Flatten nav groups so icons distribute evenly */
    .nav-top, .nav-bottom {
        display: contents !important;
    }
    
    .nav-item {
        flex: 1 !important;
        height: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 !important;
        border-radius: 0 !important;
        padding: 0 !important;
        font-size: 20px !important;
    }

    /* Show back button */
    .mobile-back-btn {
        display: block !important;
    }

    /* Force settings to single column */
    .whatsapp-container [style*="grid-template-columns"] {
        grid-template-columns: 1fr !important;
    }
}
"""

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css_clean.strip() + "\n" + mobile_block)

print("Bulletproof mobile layout applied.")
