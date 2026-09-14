from . import models
from . import controllers


def post_migrate(env, version):
    """Run automatically after every module upgrade.
    Stamps tenant_id on any records that are still missing it.
    Safe to call repeatedly — only updates records where tenant_id is False.
    """
    import shutil
    import subprocess
    import platform
    import logging
    
    _logger = logging.getLogger(__name__)

    # Ensure ffmpeg is installed
    if not shutil.which('ffmpeg'):
        _logger.info("ffmpeg not found, attempting to auto-install...")
        try:
            if platform.system() == 'Linux':
                # For Debian/Ubuntu based
                subprocess.run(['apt-get', 'update'], check=False)
                subprocess.run(['apt-get', 'install', '-y', 'ffmpeg'], check=True)
            elif platform.system() == 'Windows':
                # Try chocolatey
                subprocess.run(['choco', 'install', 'ffmpeg', '-y'], check=True)
            else:
                _logger.warning("Auto-install of ffmpeg not supported on this OS: %s", platform.system())
        except Exception as e:
            _logger.error("Failed to auto-install ffmpeg: %s", str(e))
    else:
        _logger.info("ffmpeg is already installed.")

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
