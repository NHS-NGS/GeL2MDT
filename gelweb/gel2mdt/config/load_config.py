"""Copyright (c) 2018 Great Ormond Street Hospital for Children NHS Foundation
Trust & Birmingham Women's and Children's NHS Foundation Trust

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
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
