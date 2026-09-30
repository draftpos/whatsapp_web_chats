import logging

_logger = logging.getLogger(__name__)

def remove_whatsapp_duplicates(env):
    """
    Finds and removes duplicate WhatsApp messages and their associated mail.message records.
    Run this script using Odoo shell:
    odoo-bin shell -d your_db_name -c your_odoo_config.conf
    >>> exec(open('addons/whatsapp_web_chats/remove_wa_duplicates.py').read())
    >>> remove_whatsapp_duplicates(env)
    """
    _logger.info("Starting WhatsApp duplicates removal based on msg_uid...")
    
    cr = env.cr
    
    # Method 1: Find duplicates by msg_uid
    query = """
        SELECT msg_uid, COUNT(*) 
        FROM whatsapp_message 
        WHERE msg_uid IS NOT NULL AND msg_uid != ''
        GROUP BY msg_uid 
        HAVING COUNT(*) > 1
    """
    cr.execute(query)
    duplicates_by_uid = cr.fetchall()
    
    total_removed = 0
    
    for msg_uid, count in duplicates_by_uid:
        msgs = env['whatsapp.message'].sudo().with_context(active_test=False).search(
            [('msg_uid', '=', msg_uid)], order='id asc'
        )
        if len(msgs) > 1:
            # Keep the first one, delete the rest
            to_delete = msgs[1:]
            _logger.info("Removing %s duplicates for msg_uid %s", len(to_delete), msg_uid)
            
            # Delete associated mail.message records to prevent UI duplicates
            mail_msgs = to_delete.mapped('mail_message_id')
            if mail_msgs:
                mail_msgs.unlink()
                
            to_delete.unlink()
            total_removed += len(to_delete)
            
    # Method 2: Find duplicates for outbound messages that might not have a msg_uid yet
    # Group by mobile_number, body, and timestamp within a small window
    _logger.info("Checking for duplicates by exact body, number, and time...")
    query_body = """
        SELECT mobile_number, body, DATE_TRUNC('minute', create_date) as min_date, COUNT(*)
        FROM whatsapp_message
        WHERE msg_uid IS NULL OR msg_uid = ''
        GROUP BY mobile_number, body, min_date
        HAVING COUNT(*) > 1
    """
    cr.execute(query_body)
    duplicates_by_body = cr.fetchall()
    
    for mobile, body, min_date, count in duplicates_by_body:
        # Search for these records
        msgs = env['whatsapp.message'].sudo().with_context(active_test=False).search([
            '|', ('msg_uid', '=', False), ('msg_uid', '=', ''),
            ('mobile_number', '=', mobile),
            ('body', '=', body)
        ], order='id asc')
        
        # Filter strictly by creation date within the same minute
        same_minute_msgs = msgs.filtered(lambda m: m.create_date and m.create_date.replace(second=0, microsecond=0) == min_date)
        
        if len(same_minute_msgs) > 1:
            to_delete = same_minute_msgs[1:]
            _logger.info("Removing %s body-based duplicates for %s", len(to_delete), mobile)
            
            mail_msgs = to_delete.mapped('mail_message_id')
            if mail_msgs:
                mail_msgs.unlink()
                
            to_delete.unlink()
            total_removed += len(to_delete)

    _logger.info("Finished. Total duplicates removed: %s", total_removed)
    env.cr.commit()

if __name__ == '__main__':
    # This block executes if script is run directly in Odoo shell via `odoo-bin shell < script.py`
    # or `exec(open(...))`
    if 'env' in locals() or 'env' in globals():
        remove_whatsapp_duplicates(env)
    else:
        print("Please run this script within the Odoo shell environment.")
