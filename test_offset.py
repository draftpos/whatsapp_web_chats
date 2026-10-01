def test_offset(env):
    channel = env['discuss.channel'].search([('channel_type', '=', 'whatsapp')], limit=1)
    if not channel:
        print("No channel")
        return
    m1 = env['whatsapp.account'].get_whatsapp_web_messages(channel.id, offset=0, limit=50)
    m2 = env['whatsapp.account'].get_whatsapp_web_messages(channel.id, offset=50, limit=50)
    print(f"M1 count: {len(m1)}")
    print(f"M2 count: {len(m2)}")
    if m1 and m2:
        print(f"M1 first: {m1[0].get('id')}, M1 last: {m1[-1].get('id')}")
        print(f"M2 first: {m2[0].get('id')}, M2 last: {m2[-1].get('id')}")
    else:
        print("Not enough messages")

if 'env' in locals():
    test_offset(env)
