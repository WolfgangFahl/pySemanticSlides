"""
Created on 2025-05-16

@author: wf
"""

import os

from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
from nicegui import Client, ui

from slides.slide_viewer import PresentationsViewer, SlideDetailViewer, SlidesViewer
from slides.slidewalker import PPTSet, SlideWalker
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

        @ui.page("/presentations")
        async def presentations(client: Client):
            return await self.page(client, SlideBrowser.show_presentations)

        @ui.page("/slides/{presentation_path:path}")
        async def slides(presentation_path: str, client: Client):
            return await self.page(client, SlideBrowser.show_slides, presentation_path)

        @ui.page("/slide/{presentation_path:path}/{slide_index}")
        async def slide_detail(
            presentation_path: str, slide_index: int, client: Client
        ):
            return await self.page(
                client, SlideBrowser.show_slide_detail, presentation_path, slide_index
            )

    def configure_run(self):
        """
        configure me before run
        """
        root_path = self.args.slide_path
        self.root_path = os.path.abspath(root_path)
        self.allowed_urls = [
            self.root_path,
        ]
        self.slidewalker = SlideWalker(self.root_path)
        self.ppt_set = PPTSet(self.slidewalker)
        self.ppt_set.load(with_progress=True)
        pass


class SlideBrowser(InputWebSolution):
    """
    Web solution implementation for browsing slides.
    """

    def __init__(self, webserver: SlideBrowserWebserver, client: Client):
        super().__init__(webserver, client)

    def prepare_ui(self):
        anchor_style = r"a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}"
        ui.add_head_html(f"<style>{anchor_style}</style>")
        self.ppt_set = self.webserver.ppt_set

    async def show_slide(self, path: str, page: int):
        def show():
            try:
                ppt = self.ppt_set.get_ppt(path)
                slide = ppt.getSlides()[page - 1]
                viewer = SlideDetailViewer(self, slide)
                viewer.render()
            except Exception as ex:
                self.handle_exception(ex)

        await self.setup_content_div(show)

    async def show_slides(self, presentation_path: str):
        """
        Display slides for a single presentation path.
        """
        self.slides_viewer = None
        self.grid_row = None

        def show():
            try:
                ppt = self.ppt_set.get_ppt(presentation_path, relative=True)
                if not ppt:
                    ui.label(f"no such path {presentation_path}")
                    return

                self.slides_viewer = SlidesViewer(solution=self, ppts=[ppt])
                self.slides_viewer.load_lod()
                self.slides_viewer.setup_search()
                self.grid_row = ui.row()

            except Exception as ex:
                self.handle_exception(ex)

        await self.setup_content_div(show)
        await self.slides_viewer.render_view_lod(grid_row=self.grid_row)


    def show_presentations(self):
        """
        Display the presentations viewer.
        """
        viewer = PresentationsViewer(solution=self)
        viewer.setup_ui()

    async def home(self):
        """
        Provide the main content page
        """

        def setup_home():
            self.show_presentations()

        await self.setup_content_div(setup_home)
