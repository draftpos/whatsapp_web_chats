# python script to pipe into odoo shell
import odoo
env['whatsapp.account']._cron_sync_school_balances()
env.cr.commit()
