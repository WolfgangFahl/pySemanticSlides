"""
Created on 2025-05-16

@author: wf
"""
from collections import OrderedDict
import os
from typing import List

from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.lod_grid import GridConfig, ListOfDictsGrid
from ngwidgets.progress import NiceguiProgressbar
from ngwidgets.widgets import Link
from nicegui import ui
from slides.pdf_generator import PdfGenerator, FileSet
from slides.slidewalker import PPT, Slide
from ngwidgets.task_runner import TaskRunner

class View:
    """
    Base class for views with common functions
    """

    def __init__(
        self,
        solution: InputWebSolution):
        self.solution = solution
        self.debug = self.solution.debug

    def label_value(self,label: str, value, default=""):
        """
        Helper function to display a label-value pair

        Args:
            label: The label to display
            value: The value to display
            default: Default value if value is None
        """
        value = value if value is not None else default
        with ui.row().classes("items-center gap-2"):
            ui.label(f"{label}:").classes("font-bold")
            ui.label(f"{value}")

class GridView(View):
    """
    Base class for grid-based views using ListOfDictsGrid
    """

    def __init__(
        self,
        solution: InputWebSolution,
        key_col: str,
        search_cols: List[str] = None,
        html_columns: List[int] = [1],
    ):
        """
        Initialize the GridView with a UI solution.

        Args:
            solution: the web solution providing the content_div for rendering
            key_col: the primary column key used for sorting and selection
            search_cols: list of column names to be searched via the search UI; defaults to all columns
            html_columns: list of column indices rendered as HTML; defaults to [1]
        """
        super().__init__(solution=solution)
        self.key_col = key_col
        self.grid = None
        self.html_columns = html_columns
        self.reset_lod()
        self.search_cols = search_cols
        self.search_text = ""

    def setup_search(self):
        ui.input(label="Search", placeholder="search ...").bind_value(
            self, "search_text"
        )
        ui.button("Search", on_click=self.on_search_click)

    async def on_search_click(self):
        try:
            if not self.grid or not self.search_text.strip():
                return
            search_lower = self.search_text.strip().lower()
            matched_keys = []
            columns = (
                self.search_cols or list(self.view_lod[0].keys()) if self.view_lod else []
            )
            for row in self.lod:
                for col in columns:
                    val = row.get(col)
                    if isinstance(val, str) and search_lower in val.lower():
                        key_value = row.get(self.key_col)
                        matched_keys.append(key_value)
            msg = f"search {self.search_text}→{len(matched_keys)}"
            ui.notify(msg)
            self.grid.select_rows_by_keys(matched_keys)
        except Exception as ex:
            self.solution.handle_exception(ex)

    def reset_lod(self):
        """
        Reset the logical and view layer data and summary state
        """
        self.lod: List[dict] = []
        self.view_lod: List[dict] = []
        self.summary_html: str = ""
        self.delim: str = ""

    def to_view_lod(self):
        """
        Create view layer data with key_col first and sorted by key_col.
        """
        self.view_lod = []
        for ri, record in enumerate(self.lod):
            view_record = OrderedDict(record)
            view_record.move_to_end(self.key_col, last=False)
            view_record["#"] = ri
            view_record.move_to_end("#", last=False)
            self.view_lod.append(view_record)
        self.view_lod.sort(key=lambda r: r.get(self.key_col))

    async def render_grid(self, grid_row):
        """
        Render the view_lod into a ListOfDictsGrid

        Args:
            grid_row: the container row where the grid should be rendered
        """
        grid_config = GridConfig(
            key_col=self.key_col,
            editable=True,
            multiselect=True,
            with_buttons=True,
            button_names=["all", "fit"],
            debug=self.debug,
        )
        with grid_row:
            if self.summary_html:
                ui.html(f"{self.summary_html}")
            self.setup_search()
            self.grid = ListOfDictsGrid(lod=self.view_lod, config=grid_config)
            self.grid.ag_grid._props["html_columns"] = self.html_columns
            self.grid.set_checkbox_selection(self.key_col)

    def load_lod(self):
        """
        Abstract data loading - needs to be overridden
        """
        raise Exception("abstract load_lod called")

    async def render_view_lod(self, grid_row):
        self.to_view_lod()
        await self.render_grid(grid_row)


class SlidesViewer(GridView):
    """
    Shows slides of one or more PowerPoint presentations
    """
    def __init__(self, solution: InputWebSolution, ppts: List[PPT]):
        """
        Initialize the SlideViewer.

        Args:
            solution: the UI solution context
            ppts: selected presentations to show slides for
        """
        super().__init__(solution, "page", html_columns=[1, 2])
        self.ppts = ppts
        self.ppt_set = solution.ppt_set

    def load_lod(self):
        """
        Load slide data from the given presentations
        """
        self.reset_lod()
        for ppt in self.ppts:
            slides = ppt.getSlides()
            # Link to the presentation view
            pres_url = f"/presentation/{ppt.relpath}"
            pres_info = f"{ppt.basename}({len(slides)})"
            pres_link = Link.create(pres_url, pres_info)
            self.summary_html += self.delim + pres_link
            self.delim = "•"
            for slide in slides:
                slide_record = slide.asDict()
                slide_record["path"] = ppt.relpath
                self.lod.append(slide_record)

    def to_view_lod(self):
        """
        Add links to slide detail view
        """
        super().to_view_lod()
        for record in self.view_lod:
            path = record["path"]
            page = record["page"]
            slide = self.ppt_set.get_slide(path, page, relative=True)
            if slide:
                url = f"/slide/{path}/{page}"
                name = slide.name
                record["name"] = Link.create(url, name)
                ppt = slide.ppt
                url = f"/slides/{ppt.relpath}"
                record["path"] = Link.create(url, ppt.basename)
            else:
                self.solution.logger.error(f"Slide not found: path={path}, page={page}")
            record.move_to_end("path", last=False)
            record.move_to_end("name", last=False)
            record.move_to_end("#", last=False)

    async def load_and_render(self, grid_row):
        self.load_lod()
        await self.render_view_lod(grid_row)

class PresentationView(View):
    """
    View for a single presentation
    """
    def __init__(self, solution: InputWebSolution, ppt_path: str):
        """
        Initialize the presentation view

        Args:
            solution: The web solution instance
            ppt_path: Path to the presentation file
        """
        super().__init__(solution)
        self.ppt = solution.ppt_set.get_ppt(ppt_path, relative=True)
        self.task_runner = TaskRunner()

    def render(self):
        """
        Render the presentation view
        """
        if not self.ppt:
            ui.label("Presentation not found")
            return

        with ui.card().classes("w-full"):
            ui.label(self.ppt.basename).classes("text-xl font-bold")
            self.label_value("title", self.ppt.title)
            self.label_value("author", self.ppt.author)
            self.label_value("created", self.ppt.created)
            self.label_value("path", self.ppt.relpath)
            self.label_value("slides", len(self.ppt.getSlides()))

            with ui.row():
                ui.button("Open", on_click=self.open_in_office)
                ui.button("View Slides", on_click=self.view_slides)

                # Add PDF button if available
                if self.solution.pdf_path:
                    pdf_name = self.ppt.basename.replace(".pptx", ".pdf")
                    pdf_file = os.path.join(self.solution.pdf_path, pdf_name)
                    if os.path.exists(pdf_file):
                        pdf_url = f"/static/pdf/{pdf_name}"
                        ui.button("PDF", on_click=lambda: ui.navigate.to(pdf_url))

    def open_in_office(self):
        """
        Open the presentation in Office
        """
        self.ppt.open_in_office()

    def view_slides(self):
        """
        Navigate to the slides view
        """
        ui.navigate.to(f"/slides/{self.ppt.relpath}")

class PresentationsViewer(GridView):
    """
    Viewer for available presentations
    """
    def __init__(self, solution: InputWebSolution):
        """
        Initialize the PresentationsViewer.

        Args:
            solution: the UI solution context
        """
        super().__init__(solution, "path", html_columns=[1,2,3,4,5])
        self.ppt_set = solution.ppt_set
        self.slide_viewer = None
        self.task_runner = TaskRunner()

    def setup_ui(self):
        """
        Set up UI controls and layout
        """
        with ui.row() as self.header_row:
            ui.label(self.ppt_set.slidewalker.rootFolder)
            ui.button("walk", on_click=self.on_walk)
            pdf_disabled = not self.solution.pdf_path
            pdf_tooltip = "Generate PDFs" if not pdf_disabled else "PDF output path not configured"

            btn = ui.button("PDFs", icon="picture_as_pdf", on_click=self.on_generate_pdfs if not pdf_disabled else None)
            if pdf_disabled:
                btn.disable()
            btn.tooltip(pdf_tooltip)
            ui.button("show slides", on_click=self.on_show_slides)
        with ui.row() as self.progress_row:
            self.progress_bar = NiceguiProgressbar(
                total=0, desc="pdfgenerator", unit="pdfs"
            )
            self.task_runner.progress = self.progress_bar

        self.grid_row = ui.row()
        self.slide_grid_row = ui.row()

    async def on_walk(self):
        self.task_runner.run_async(self.load_and_show_presentations)

    def to_view_lod(self):
        """
        Make path clickable and add PDF links
        """
        super().to_view_lod()
        for record in self.view_lod:
            path = record["path"]
            ppt = self.ppt_set.get_ppt(path)
            url = f"/slides/{ppt.relpath}"
            record["path"] = Link.create(url, ppt.basename)
            pdf_link = ""
            if self.solution.pdf_path:
                pdf_name = ppt.basename.replace(".pptx", ".pdf")
                pdf_file = os.path.join(self.solution.pdf_path, pdf_name)
                if os.path.exists(pdf_file):
                    pdf_url = f"/static/pdf/{pdf_name}"
                    pdf_link = Link.create(pdf_url, "📄 PDF")
            record["pdf"] = pdf_link

    async def load_and_show_presentations(self):
        """
        Load and display presentations
        """
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
        self.lod = self.ppt_set.as_lod()

    async def on_show_slides(self):
        """
        Load selected presentations and display their slides
        """
        selected = await self.grid.get_selected_rows()
        if not selected:
            ui.notify("No presentations selected")
            return
        await self.show_selected_slides(selected)

    async def on_generate_pdfs(self):
        """
        Generate PDF files for the presentations
        """
        self.task_runner.run_blocking(self.generate_pdfs)

    def generate_pdfs(self):
        """
        Generate PDF files from PowerPoint presentations
        """
        try:
            base_path = self.ppt_set.slidewalker.rootFolder
            pdf_path = self.solution.pdf_path
            pptx_set = FileSet(base_path=str(base_path), ext="pptx")

            pdfgen = PdfGenerator(debug=self.debug)
            _result = pdfgen.generate_pdfs(
                pptx_set=pptx_set,
                pdf_path=pdf_path,
                with_stats=True,
                progress_bar=self.progress_bar
            )
            self.task_runner.run_async(self.load_and_show_presentations)

        except Exception as ex:
            self.solution.handle_exception(ex)

    async def show_selected_slides(self, selected: List[dict]):
        """
        Load and display slides from the selected presentations.

        Args:
            selected: selected rows from the presentation list
        """
        self.slide_grid_row.clear()
        ppts = []
        for r in selected:
            ri = r.get("#")
            row = self.lod[ri]
            path = row.get("path")
            if path:
                ppt = self.ppt_set.get_ppt(path)
            ppts.append(ppt)
        with self.slide_grid_row:
            self.slide_viewer = SlidesViewer(self.solution, ppts)
            self.task_runner.run_async(lambda: self.slide_viewer.load_and_render(self.slide_grid_row))


class SlideDetailViewer:
    """
    Viewer for a single slide
    """
    def __init__(self, solution: InputWebSolution, slide: Slide):
        """
        Initialize the SlideDetailViewer.

        Args:
            solution: the UI solution context
            slide: the slide to display
        """
        self.solution = solution
        self.slide = slide

    def render(self):
        """
        Render the slide details
        """
        with ui.card():
            ui.label(f"{self.slide.title}")
            ui.label(f"{self.slide.name}")
            ui.label(f"#{self.slide.page}")
            ui.html(f"<pre>{self.slide.getText()}</pre>")