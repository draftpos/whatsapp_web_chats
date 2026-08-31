import os

base = r"C:\odoo19\addons\whatsapp_wedsphere"
css_path = os.path.join(base, "static", "src", "css", "chats.css")

with open(css_path, "r", encoding="utf-8") as f:
    css = f.read()

# I need to fix the nav-top and nav-bottom elements in mobile view so they don't break the row layout
fix_css = """
    /* Flatten the nav groups on mobile so all icons sit perfectly in a row */
    .nav-top, .nav-bottom {
        display: contents !important;
    }
    
    /* Make sure icons are spaced out perfectly across the bottom */
    .nav-item {
        margin: 0 !important;
        flex: 1 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        border-radius: 0 !important;
        font-size: 20px !important;
    }
"""

# Insert this inside the @media (max-width: 768px) block. I can just append it before the closing brace of the media query if I can parse it, or just append a new media query. Appending a new one is safer.
mobile_fix = """
@media (max-width: 768px) {
    .nav-top, .nav-bottom {
        display: contents !important;
    }
    .nav-item {
        flex: 1 !important;
        padding: 10px 0 !important;
    }
    .whatsapp-nav-rail {
        background: var(--ws-bg-sidebar) !important;
    }
}
"""

with open(css_path, "a", encoding="utf-8") as f:
    f.write("\n" + mobile_fix)

print("Mobile tab bar icon layout fixed.")
