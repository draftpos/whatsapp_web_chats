import subprocess

# Clear Odoo assets cache for Nadias
cmd = """
sudo -S docker exec odoo_nadias_s4_havano_pro_qrmeqxutyzvhwwupoxju odoo shell -d nadias_s4_havano_pro_qrmeqxutyzvhwwupoxju --no-http << 'EOF'
env['ir.attachment'].search([('url', 'like', '/web/assets/')]).unlink()
env.cr.commit()
print("Assets cache cleared!")
EOF
"""

result = subprocess.run(
    ["ssh", "-i", "C:/odoo19/addons/havano_schools_odoo/server_key",
     "-o", "StrictHostKeyChecking=no",
     "amakoni@s4.havano.pro",
     "echo amakoni | " + cmd],
    capture_output=True, text=True, timeout=120
)
print("OUT:", result.stdout)
print("ERR:", result.stderr)
