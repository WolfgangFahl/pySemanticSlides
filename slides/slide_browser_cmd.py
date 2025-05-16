"""
Created on 2025-05-16

@author: wf
"""

import sys
from argparse import ArgumentParser

from ngwidgets.cmd import WebserverCmd
from slides.slide_browser import SlideBrowserWebserver


class SlideBrowserCmd(WebserverCmd):
    """
    Command line interface for the Slide Browser Webserver.
    """

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        parser = super().getArgParser(description, version_msg)
        parser.add_argument(
            "slide_path",
            help="path to PowerPoint files (required)",
        )
        return parser


def main(argv: list = None):
    cmd = SlideBrowserCmd(
        config=SlideBrowserWebserver.get_config(),
        webserver_cls=SlideBrowserWebserver,
    )
    exit_code = cmd.cmd_main(argv)
    return exit_code


DEBUG = 0
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
