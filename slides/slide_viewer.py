"""
Created on 2025-05-16

@author: wf
"""

from ngwidgets.lod_grid import ListOfDictsGrid, GridConfig
from slides.slidewalker import SlideWalker
from nicegui import ui

class SlideViewer:
    """
    Shows slides of a single PowerPoint presentation
    """

    def __init__(self, ppt, solution):
        self.ppt = ppt
        self.solution = solution
        self.lod = []
        self.grid = None
        self.load_slides()
        self.show_slides()

    def load_slides(self):
        """
        Load slide data from the PPT instance
        """
        self.lod = []
        slides = self.ppt.getSlides()
        for slide in slides:
            slide_record = slide.asDict()
            self.lod.append(slide_record)

    def show_slides(self):
        """
        Display slides in a grid
        """
        grid_config = GridConfig(
            key_col="page",
            editable=False,
            multiselect=False,
            with_buttons=False,
        )
        with self.solution.content_div:
            ui.label(f"Slides from {self.ppt.basename}")
            self.grid = ListOfDictsGrid(lod=self.lod, config=grid_config)
            self.grid.ag_grid._props["html_columns"] = [0, 1, 2]

class PresentationsViewer:
    """
    Presentations viewer for PowerPoint presentations
    """

    def __init__(self, solution):
        self.solution = solution
        self.grid = None
        self.ppts={}
        self.lod = []
        self.view_lod= []
        self.grid=None

    def setup_ui(self):
        """
        Set up the UI using ngwidgets
        """
        root_path = self.solution.webserver.root_path
        self.slidewalker = SlideWalker(root_path)
        with ui.row() as self.header_row:
            self.path_label=ui.label(root_path)
            self.walk_button = ui.button("walk", on_click=self.on_walk)
        #self.expansion = ui.expansion("Presentations", icon="slideshow", value=True)
        #with self.expansion:
        self.grid_row=ui.row()
        self.slide_grid_row=ui.row()


    async def on_walk(self):
        self.load_data()

    def load_data(self):
        """
        Load slide metadata as LOD
        """
        for ppt in self.slidewalker.yieldPowerPointFiles(verbose=True):
            record = ppt.asDict()
            self.ppts[ppt.filepath]=ppt
            self.lod.append(record)
        if self.grid is None:
            self.setup_grid()
        else:
            self.grid.load_lod(self.lod)

    def setup_grid(self):
        """
        Setup the grid UI element
        """
        grid_config = GridConfig(
            key_col="path",
            editable=False,
            multiselect=False,
            with_buttons=False,
        )
        with self.grid_row:
            self.grid = ListOfDictsGrid(lod=self.lod, config=grid_config)
            self.grid.ag_grid._props["html_columns"] = [0, 1, 2]
            self.grid.ag_grid.on("cellDoubleClicked", self.on_double_click)


    def on_double_click(self, event):
        """
        Handle double-click on a row
        """
        row_data = event.args.get("data")
        if row_data:
            path = row_data.get("path")
            ui.notify(f"Double-clicked: {row_data.get('title', row_data)}")
            if path:
                ppt = self.ppts[path]
                #self.expansion.value = False  # collapse presentation list
                self.slide_grid_row.clear()
                with self.slide_grid_row:
                    SlideViewer(ppt, self.solution)