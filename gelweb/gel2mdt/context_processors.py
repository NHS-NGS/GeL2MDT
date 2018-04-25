from .config.load_config import LoadConfig


def config_access(request):
    config = LoadConfig().load()
    return {'config_dict': config}
