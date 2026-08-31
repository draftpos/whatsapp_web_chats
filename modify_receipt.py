import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_account_payment_receipt_override.xml"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace the letterhead-details and brand-logo blocks
# We'll extract them, change text-align:left to right, and swap their positions.

letterhead_start = content.find('<div class="letterhead">')
letterhead_end = content.find('<div class="title-bar">', letterhead_start)

letterhead_block = content[letterhead_start:letterhead_end]

# Extract letterhead-details
details_start = letterhead_block.find('<div class="letterhead-details"')
details_end = letterhead_block.find('<div class="brand-logo"')
details_block = letterhead_block[details_start:details_end]

# Extract brand-logo
logo_start = details_end
logo_end = letterhead_block.rfind('</div>', 0, len(letterhead_block)-10) + 6 # find the closing div of letterhead
logo_block = letterhead_block[logo_start:logo_end]

# Modify details block to change text-align:left to text-align:right
details_block_modified = details_block.replace("text-align:left;", "text-align:right;")

# Construct new letterhead block
new_letterhead_block = '<div class="letterhead">\n' + logo_block + details_block_modified

# Replace in content
new_content = content[:letterhead_start] + new_letterhead_block + content[letterhead_start + logo_end:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Success")
