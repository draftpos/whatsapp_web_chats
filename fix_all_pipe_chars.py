import re

file_path = r"C:\odoo19\addons\havano_schools_odoo\views\report_havano_student_payment.xml"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("Before fixes - pipe count:", content.count('|'))

# Fix all the corrupted A characters (| replacing A in words)
replacements = [
    # Field labels
    ('|CCOUNT PAID TO', 'Account Paid To'),
    ('|llocated |mount', 'Allocated Amount'),
    ('|LLOCATED |MOUNT', 'Allocated Amount'),
    ('|llocated', 'Allocated'),
    ('|Allocated |mount', 'Allocated Amount'),
    # Totals section
    ('|llocated |mount', 'Allocated Amount'),
    ('|llocated\u003c', 'Allocated<'),
    # Thermal labels
    ('|CCOUNT', 'ACCOUNT'),
    ('|LLOC|TED', 'ALLOCATED'),
    ('|LLOC|TE', 'ALLOCATE'),
    ('|OUTST|NDING', 'OUTSTANDING'),
    ('OUTST|NDING', 'OUTSTANDING'),
    ('TOT|L OUTST|NDING', 'TOTAL OUTSTANDING'),
    ('TOT|L', 'TOTAL'),
    ('B|L|NCE DUE', 'BALANCE DUE'),
    ('B|L|NCE', 'BALANCE'),
    ('|LLOC', 'ALLOC'),
    ('D|TE', 'DATE'),
    ('CL|SS', 'CLASS'),
    ('|uthorised', 'Authorised'),
    ('OFFICI|L', 'OFFICIAL'),
    ('DR|FT', 'DRAFT'),
    ('OFFICI|L RECEIPT', 'OFFICIAL RECEIPT'),
    ('★ ★ ★ OFFICI|L RECEIPT ★ ★ ★', '★ ★ ★ OFFICIAL RECEIPT ★ ★ ★'),
    # Paper format
    ('FBF|F6', 'FBFAF6'),
    # CSS vars
    ('--paper: #FBF|F6', '--paper: #FBFAF6'),
    ('#FBF|F6', '#FBFAF6'),
    # Report action comment
    ('Report |ction', 'Report Action'),
    # Section headers
    ('THERM|L', 'THERMAL'),
    ('M|IN', 'MAIN'),
    # Ribbon
    ('DR|FT', 'DRAFT'),
    # Red color in thermal
    ('B23|2E', 'B2322E'),
    ('#B23|2E', '#B2322E'),
    # OUTSTANDING INVOICES label
    ('OUTST|NDING INVOICES', 'OUTSTANDING INVOICES'),
    # Table header
    ('|LLOC', 'ALLOC'),
    ('|CCOUNT\u003c', 'ACCOUNT<'),
    # Other corruptions
    ('|4', 'A4'),
    # Remaining pipe issues
    ('| ', 'A '),
]

for old, new in replacements:
    if old in content:
        count = content.count(old)
        content = content.replace(old, new)
        print(f"  Fixed '{old}' -> '{new}' ({count} times)")

# Final pass: fix any remaining pipes inside XML text content
# Only fix pipes that appear to be corrupted A's in known words
import re
# Fix patterns like |ccount, |llocated, |mount, etc.
def fix_pipe_a(m):
    word = m.group(0)
    return 'A' + word[1:]

# Fix pipes that start words inside element content (not in attributes with | as OR)
# Common words starting with A that got corrupted
corrupted_a_words = ['|ccount', '|llocated', '|mount', '|uthorised', '|ction', '|dmin']
for word in corrupted_a_words:
    if word in content:
        fixed = 'A' + word[1:]
        content = content.replace(word, fixed)
        print(f"  Fixed '{word}' -> '{fixed}'")

print("\nAfter fixes - pipe count:", content.count('|'))
print("Remaining pipes (should only be valid ones like t-if conditions):")
for i, line in enumerate(content.split('\n'), 1):
    if '|' in line and '<' in line:
        # Skip lines with t-if which use | as OR operator
        if 't-if' not in line and 'display_currency' not in line:
            print(f"  Line {i}: {line.strip()[:100]}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone - file saved.")
