import os
import inspect

class LoadConfig():
    """
     Representation of an instance when loading the config file
    """
    def load(self):
        """
        Loads config data from config.txt
        :return: dict containing key:configuration option value:configuration value
        """
        config_dict = {}
        with open(
            os.path.join(
                os.path.dirname(
                    os.path.abspath(
                        inspect.stack()[0][1]
                    )
                ),
                "config.txt"), 'r') as config_file:
            for line in config_file:
                if not line.startswith('#'):
                    line = line.strip().split('=', 1)
                    if len(line) == 2:
                        config_dict[line[0]] = line[1]
        return config_dict
