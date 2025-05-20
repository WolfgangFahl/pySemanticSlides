"""
Created on 2025-05-16

@author: wf
"""

import os

from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
from ngwidgets.task_runner import TaskRunner
from nicegui import app, Client, ui
from slides.slide_viewer import PresentationsViewer, SlideDetailViewer, SlidesViewer
from slides.slidewalker import PPTSet, SlideWalker
from slides.version import Version
from typing import List

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

        @ui.page("/slides/{presentation_paths:path}")
        async def slides(presentation_paths: str, client: Client):
            return await self.page(client, SlideBrowser.show_slides, presentation_paths)

        @ui.page("/slide/{presentation_path:path}/{slide_index}")
        async def slide_detail(
            presentation_path: str, slide_index: int, client: Client
        ):
            return await self.page(
                client, SlideBrowser.show_slide, presentation_path, slide_index
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
        # PDF path
        self.pdf_path = os.path.abspath(self.args.pdf_path) if self.args.pdf_path else None
        # Serve static PDF files if --pdf_path was given
        if self.pdf_path:
            if os.path.isdir(self.pdf_path):
                app.add_static_files("/static/pdf", self.pdf_path)
            else:
                self.pdf_path=None


class SlideBrowser(InputWebSolution):
    """
    Web solution implementation for browsing slides.
    """

    def __init__(self, webserver: SlideBrowserWebserver, client: Client):
        super().__init__(webserver, client)
        self.pdf_path=webserver.pdf_path
        pass

    def prepare_ui(self):
        anchor_style = r"a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}"
        ui.add_head_html(f"<style>{anchor_style}</style>")
        self.ppt_set = self.webserver.ppt_set

    async def show_slide(self, path: str, page: int):
        """
        Show the given slide.
        """
        def show():
            try:
                slide = self.ppt_set.get_slide(path, page, relative=True)
                if slide:
                    viewer = SlideDetailViewer(self, slide)
                    viewer.render()
                else:
                    ui.label(f"Slide {page} not found in {path}")
            except Exception as ex:
                self.handle_exception(ex)

        await self.setup_content_div(show)


    async def show_slides(self, presentation_paths_str: str):
        """
        Display slides for single or multiple presentation paths.

        Args:
            presentation_paths_str: Path string that may contain multiple paths separated by '+'
        """
        # Parse the path string into a list of paths
        delim=","
        presentation_paths = presentation_paths_str.split(delim) if delim in presentation_paths_str else [presentation_paths_str]

        self.slides_viewer = None
        self.grid_row = None

        async def render_task():
            await self.slides_viewer.load_and_render(self.grid_row)

        def show():
            try:
                ppts = []
                for presentation_path in presentation_paths:
                    ppt = self.ppt_set.get_ppt(presentation_path, relative=True)
                    if not ppt:
                        ui.notify(f"{presentation_path} not available")
                    else:
                        ppts.append(ppt)
                if not ppts:
                    ui.label("No valid presentations requested")
                    return
                self.grid_row = ui.row()
                self.slides_viewer = SlidesViewer(solution=self, ppts=ppts)

            except Exception as ex:
                self.handle_exception(ex)

        await self.setup_content_div(show)
        TaskRunner().run_async(render_task)

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
