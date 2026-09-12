from . import models


def post_migrate(env, version):
    """Run automatically after every module upgrade.
    Stamps tenant_id on any records that are still missing it.
    Safe to call repeatedly — only updates records where tenant_id is False.
    """
    try:
        env['whatsapp.account'].sudo().update_tenant_data()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            "whatsapp_web_chats: tenant migration skipped: %s", e
        )
