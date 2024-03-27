__all__ = ('stop_auto_reloader',)

from scarletio import copy_docs

from ..plugin_auto_reloader import PLUGIN_AUTO_RELOADER_MANAGER, PluginAutoReloaderManager


@copy_docs(PluginAutoReloaderManager.stop)
def stop_auto_reloader():
    return PLUGIN_AUTO_RELOADER_MANAGER.stop()
