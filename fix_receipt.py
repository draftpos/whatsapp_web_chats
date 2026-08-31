import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_account_payment_receipt_override.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We know the exact string that is broken.
# It starts at <div class="letterhead"> and ends at <div class="title-bar">

start_idx = content.find('<div class="letterhead">')
end_idx = content.find('<div class="title-bar">', start_idx)

broken_block = content[start_idx:end_idx]

# Let's extract the brand logo part
logo_start = broken_block.find('<div class="brand-logo">')
logo_end = broken_block.find('</div>', broken_block.find('</div>', logo_start) + 1) + 6 # this gets the second </div> which closes brand-logo

logo_block = broken_block[logo_start:logo_end]

# Let's extract the letterhead-details part
details_start = broken_block.find('<div class="letterhead-details"')
details_end = broken_block.find('</div>\n                          \n  \n                      ')
if details_end == -1:
    details_end = broken_block.rfind('</div>') + 6
else:
    details_end = broken_block.rfind('</div>', 0, details_end) + 6 # closing of letterhead-details

# wait, better way:
details_end = broken_block.rfind('</div>', 0, len(broken_block)-10) + 6

details_block = broken_block[details_start:details_end]
if details_block.endswith('</div></div>'):
    details_block = details_block[:-6]

# Clean up any trailing </div> in details_block that belongs to letterhead
# Actually let's just make sure details_block ends with the single correct </div>
details_block = details_block.strip()
while details_block.endswith('</div></div>'):
    details_block = details_block[:-6].strip()

new_block = f"""<div class="letterhead">
                        {logo_block}
                        {details_block}
                    </div>

                    """

new_content = content[:start_idx] + new_block + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed again")
