from . import models
from . import controllers


def post_migrate(env, version):
    """Run automatically after every module upgrade.
    Stamps tenant_id on any records that are still missing it.
    Safe to call repeatedly — only updates records where tenant_id is False.
    """
    import sys
    import subprocess
    import logging
    
    _logger = logging.getLogger(__name__)

    # Ensure imageio-ffmpeg is installed
    try:
        import imageio_ffmpeg
        _logger.info("imageio-ffmpeg is already installed.")
    except ImportError:
        _logger.info("imageio-ffmpeg not found, attempting to auto-install via pip...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'imageio-ffmpeg'], check=True)
            _logger.info("Successfully installed imageio-ffmpeg.")
        except Exception as e:
            _logger.error("Failed to auto-install imageio-ffmpeg: %s", str(e))

    try:
        env['whatsapp.account'].sudo().update_tenant_data()
        
        # Retroactively grant Admin groups to all internal users
        wa_admin_group = env.ref('whatsapp.group_whatsapp_admin', raise_if_not_found=False)
        erp_manager_group = env.ref('base.group_erp_manager', raise_if_not_found=False)
        system_group = env.ref('base.group_system', raise_if_not_found=False)
        
        if wa_admin_group:
            env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) SELECT id, %s FROM res_users WHERE share=False ON CONFLICT DO NOTHING", (wa_admin_group.id,))
        if erp_manager_group:
            env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) SELECT id, %s FROM res_users WHERE share=False ON CONFLICT DO NOTHING", (erp_manager_group.id,))
        if system_group:
            env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) SELECT id, %s FROM res_users WHERE share=False ON CONFLICT DO NOTHING", (system_group.id,))
            
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            "whatsapp_web_chats: tenant migration skipped: %s", e
        )
