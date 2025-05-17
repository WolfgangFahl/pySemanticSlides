"""
Created on 2025-05-16

@author: wf
"""

import os

from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
from nicegui import Client, ui

from slides.slide_viewer import PresentationsViewer
from slides.version import Version


class SlideBrowserWebserver(InputWebserver):
    """
    Webserver to browse and display PowerPoint slides.
    """

    @classmethod
    def get_config(cls) -> WebserverConfig:
        copy_right = "(c)2025 Wolfgang Fahl"
        config = WebserverConfig(
            short_name="slide_browser",
            timeout=6.0,
            copy_right=copy_right,
            version=Version(),
            default_port=9995,
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = SlideBrowser
        return server_config

    def __init__(self):
        """
        constructor
        """
        super().__init__(config=SlideBrowserWebserver.get_config())

    def configure_run(self):
        root_path = self.args.slide_path
        self.root_path = os.path.abspath(root_path)
        self.allowed_urls = [
            self.root_path,
        ]


class SlideBrowser(InputWebSolution):
    """
    Web solution implementation for browsing slides.
    """

    def __init__(self, webserver: SlideBrowserWebserver, client: Client):
        super().__init__(webserver, client)

    def prepare_ui(self):
        anchor_style = r"a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}"
        ui.add_head_html(f"<style>{anchor_style}</style>")

    async def home(self):
        """
        Provide the main content page
        """

        def setup_home():
            viewer = PresentationsViewer(solution=self)
            viewer.setup_ui()

        await self.setup_content_div(setup_home)
