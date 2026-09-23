channel_ids = env['discuss.channel'].search([('channel_type', '=', 'whatsapp')], limit=10).ids
print(f"Channels: {channel_ids}")

last_message_data = env['mail.message'].read_group(
    [('model', '=', 'discuss.channel'), ('res_id', 'in', channel_ids)],
    ['res_id', 'id:max'],
    ['res_id']
)
print(f"Read Group: {last_message_data}")
