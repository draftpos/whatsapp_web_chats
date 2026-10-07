import sys

def merge_duplicates(env):
    """
    Merges duplicate WhatsApp channels in Odoo based on whatsapp_number.
    """
    channels = env['discuss.channel'].search([('channel_type', '=', 'whatsapp')])
    
    # Group channels by (whatsapp_number, wa_account_id)
    grouped = {}
    for ch in channels:
        if not ch.whatsapp_number:
            continue
        key = (ch.whatsapp_number, ch.wa_account_id.id if ch.wa_account_id else False)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(ch)
        
    merged_count = 0
    deleted_count = 0
    
    for key, duplicates in grouped.items():
        if len(duplicates) > 1:
            # Sort by ID so we keep the original (oldest) channel
            duplicates.sort(key=lambda c: c.id)
            primary = duplicates[0]
            others = duplicates[1:]
            
            for dup in others:
                # Move all mail.messages to the primary channel
                messages = env['mail.message'].search([
                    ('model', '=', 'discuss.channel'),
                    ('res_id', '=', dup.id)
                ])
                if messages:
                    messages.write({'res_id': primary.id})
                    merged_count += len(messages)
                    
                # Move any channel members (if needed)
                # Odoo normally handles members, but we can ensure the current agent is on the primary
                for member in dup.channel_member_ids:
                    if not env['discuss.channel.member'].search([('channel_id', '=', primary.id), ('partner_id', '=', member.partner_id.id)]):
                        member.write({'channel_id': primary.id})
                    else:
                        member.unlink()
                
                # Delete the duplicate channel
                dup.unlink()
                deleted_count += 1
                
            print(f"Merged {len(others)} duplicates into channel ID {primary.id} for number {key[0]}")
            env.cr.commit()
            
    print(f"\nDone! Moved {merged_count} messages and deleted {deleted_count} duplicate channels.")

if __name__ == '__main__':
    merge_duplicates(env)
