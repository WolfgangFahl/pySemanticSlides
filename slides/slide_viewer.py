"""
Created on 2025-05-16

@author: wf
"""

from collections import OrderedDict
from typing import List

from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.lod_grid import GridConfig, ListOfDictsGrid
from ngwidgets.widgets import Link
from nicegui import background_tasks, ui

from slides.slidewalker import Presentation, SlideWalker


class GridViewer:
    """
    Base class for grid-based viewers using ListOfDictsGrid
    """

    def __init__(self, solution: InputWebSolution, key_col:str,html_columns:List[int]=[1]):
        """
        Initialize the GridViewer with a UI solution.

        Args:
            solution (InputWebSolution): the web solution providing the content_div for rendering
        """
        self.solution = solution
        self.key_col=key_col
        self.grid = None
        self.html_columns=html_columns
        self.reset_lod()

    def reset_lod(self):
        """
        Reset the logical and view layer data and summary state
        """
        self.lod: List[dict] = []
        self.view_lod: List[dict] = []
        self.summary: str = ""
        self.delim: str = ""

    def to_view_lod(self):
        """
        Create view layer data with key_col first and sorted by key_col.
        """
        self.view_lod = []
        for ri,record in enumerate(self.lod):
            view_record = OrderedDict(record)
            view_record.move_to_end(self.key_col, last=False)
            view_record["#"]=ri
            view_record.move_to_end("#", last=False)
            self.view_lod.append(view_record)
        self.view_lod.sort(key=lambda r: r.get(self.key_col))
        pass


    async def render_grid(self,grid_row):
        """
        Render the view_lod into a ListOfDictsGrid

        Args:
            grid_row: the container row where the grid should be rendered
        """
        grid_config = GridConfig(
            key_col=self.key_col,
            editable=False,
            multiselect=True,
            with_buttons=False,
        )
        with grid_row:
            if self.summary:
                ui.label(f"{self.summary}")
            self.grid = ListOfDictsGrid(lod=self.view_lod, config=grid_config)
            self.grid.ag_grid._props["html_columns"] = self.html_columns
            self.grid.set_checkbox_selection(self.key_col)

    def load_lod(self):
        """
        abstract data loading - needs to be overridden
        """
        raise Exception("abstract load_lod called")

    async def render_view_lod(self,grid_row):
        self.to_view_lod()
        await self.render_grid(grid_row)


class SlideViewer(GridViewer):
    """
    Shows slides of one or more PowerPoint presentations
    """

    def __init__(self, ppts: List[Presentation], solution: InputWebSolution):
        """
        Initialize the SlideViewer.

        Args:
            ppts (List[Presentation]): the list of PowerPoint presentations
            solution (InputWebSolution): the UI solution context
        """
        super().__init__(solution,"page")
        self.ppts = ppts

    def load_lod(self):
        """
        Load slide data from the list of presentations
        """
        self.reset_lod()
        for ppt in self.ppts:
            slides = ppt.getSlides()
            self.summary += f"{self.delim}{ppt.basename}({len(slides)})"
            self.delim = ", "
            for slide in slides:
                slide_record = slide.asDict()
                self.lod.append(slide_record)

class PresentationsViewer(GridViewer):
    """
    Viewer for available presentations
    """

    def __init__(self, solution: InputWebSolution):
        """
        Initialize the PresentationsViewer.

        Args:
            solution (InputWebSolution): the UI solution context
        """
        super().__init__(solution,"path")
        self.ppts = {}
        self.slide_viewer=None

    def setup_ui(self):
        """
        Set up UI controls and layout
        """
        self.slidewalker = SlideWalker(self.solution.webserver.root_path)
        with ui.row() as self.header_row:
            ui.label(self.slidewalker.rootFolder)
            ui.button("walk", on_click=self.on_walk)
            ui.button("show slides", on_click=self.on_show_slides)
        # unfortunately does not work
        #self.expansion = ui.expansion("Presentations", icon="slideshow", value=True)
        #with self.expansion:
        self.grid_row = ui.row()
        self.slide_grid_row = ui.row()

    async def on_walk(self):
        background_tasks.create(self.load_and_show_presentations())

    def to_view_lod(self):
        """
        make path clickable
        """
        super().to_view_lod()
        for record in self.view_lod:
            path=record["path"]
            ppt=self.ppts.get(path)
            url = f"{self.solution.webserver.root_path}/{path}"
            record["path"] = Link.create(url,ppt.basename)

    async def load_and_show_presentations(self):
        try:
            self.load_lod()
            await self.render_view_lod(self.grid_row)
        except Exception as ex:
            self.solution.handle_exception(ex)

    def load_lod(self):
        """
        Load available presentation metadata
        """
        self.reset_lod()
        for ppt in self.slidewalker.yieldPowerPointFiles(verbose=True):
            record = ppt.asDict()
            self.ppts[ppt.filepath] = ppt
            self.lod.append(record)

    async def on_show_slides(self):
        """
        Load selected presentations and display their slides
        """
        selected = await self.grid.get_selected_rows()
        if not selected:
            ui.notify("No presentations selected")
            return
        background_tasks.create(self.show_selected_slides(selected))

    async def show_selected_slides(self, selected: List[dict]):
        """
        Load and display slides from the selected presentations.

        Args:
            selected (List[dict]): selected rows from the presentation list
        """
        self.slide_grid_row.clear()
        # unfortunately does not work
        #self.expansion.value = False
        ppts = []
        for r in selected:
            # magic view to data retranslation
            ri=r.get("#")
            row=self.lod[ri]
            path=row.get("path")
            if path:
                ppt=self.ppts.get(path)
            ppts.append(ppt)
        with self.slide_grid_row:
            self.slide_viewer = SlideViewer(ppts, self.solution)
            self.slide_viewer.load_lod()
            await self.slide_viewer.render_view_lod(self.slide_grid_row)
