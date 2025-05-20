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

class PageNavigator:
    """
    Simple page navigator with URL generation callback
    """

    def __init__(self, current_page: int, total_pages: int, url_for_page):
        """
        Initialize the page navigator

        Args:
            current_page: Current page number (1-based)
            total_pages: Total number of pages
            url_for_page: Callback function that returns URL for a given page number
        """
        self.current_page = current_page
        self.total_pages = total_pages
        self.url_for_page = url_for_page

    def generate_markup(self) -> str:
        """Generate HTML markup for page navigation"""
        def get_link(page,symbol,tooltip)->str:
            page_url=self.url_for_page(page)
            link=Link.create(page_url,symbol)
            if tooltip:
                pass
            return link

        # provide a page nav
        markup = f"""<div class="page-nav" style="display: flex; align-items: center; justify-content: center; gap: 15px; margin: 10px 0;">"""
        markup += get_link(1, "⏮", f"First Page (1/{self.total_pages})")
        markup += get_link(max(1, self.current_page - 10), "⏪", "Fast Backward (Jump -10 Pages)")
        markup += get_link(max(1, self.current_page - 1), "◀", "Previous Page")
        markup += f'<span>Page {self.current_page} of {self.total_pages}</span>'
        markup += get_link(min(self.total_pages, self.current_page + 1), "▶", "Next Page")
        markup += get_link(min(self.total_pages, self.current_page + 10), "⏩", "Fast Forward (Jump +10 Pages)")
        markup += get_link(self.total_pages, "⏭", f"Last Page ({self.total_pages}/{self.total_pages})")
        markup += "</div>"
        return markup

    def render(self):
        """Render the page navigator with a single HTML call"""
        markup=self.generate_markup()
        ui.html(markup)
class PDF:
    """
    Portable Document File handling
    """
    def __init__(self,solution,ppt):
        self.solution=solution
        self.ppt=ppt
        self.pdf_name = self.ppt.basename.replace(".pptx", ".pdf")
        if self.solution.pdf_path:
            self.pdf_file = os.path.join(self.solution.pdf_path, self.pdf_name)
            self.valid=os.path.exists(self.pdf_file)
        else:
            self.pdf_file=None
            self.valid=False

    def get_url(self,page:int=None):
        url=f"/static/pdf/{self.pdf_name}" if self.valid else None
        if url and page:
            url=f"{url}#page={page}"
        return url

    def get_link(self,page:int=None):
        pdf_url=self.get_url(page=page)
        if pdf_url:
            pdf_link = Link.create(pdf_url, "📄 PDF")
        else:
            pdf_link=""
        return pdf_link

class View:
    """
    Base class for views with common functions
    """

    def __init__(
        self,
        solution: InputWebSolution):
        self.solution = solution
        self.debug = self.solution.debug

    def label_value(self,label: str, value, default="", compact:bool=False):
        """
        Helper function to display a label-value pair

        Args:
            label: The label to display
            value: The value to display
            default: Default value if value is None
        """
        value = value if value is not None else default
        if compact:
            ui.label("•").classes("text-gray-500")
            ui.label(value).tooltip(label)
        else:
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

    def render_master(self,grid_row):
        # Master view (presentation details)
        with grid_row:
            with ui.card().classes("w-full mb-4") as self.master_card:
                if len(self.ppts) == 1:
                    # If only one presentation is selected, show full details
                    ppt = self.ppts[0]
                    presentation_view = PresentationView(self.solution, ppt.relpath)
                    presentation_view.render()
                else:
                    # If multiple presentations, show a summary
                    with ui.row():
                        for i,ppt in enumerate(self.ppts):
                            PresentationView.get_ppt_header(ppt,i>0)
    async def load_and_render(self, grid_row):
        self.render_master(grid_row)
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
        self.pdf = PDF(solution, self.ppt) if self.ppt else None
        self.task_runner = TaskRunner(timeout=40)


    def render(self):
        """
        Render the presentation view
        """
        with ui.row().classes("items-center gap-2 w-full"):
            ui.label(self.ppt.basename).classes("font-bold")
            ui.label(f"({len(self.ppt.getSlides())} slides)")
            # Action buttons
            ui.button(icon="open_in_new", on_click=self.open_in_office, color="primary").props("flat dense")
            if self.pdf and self.pdf.valid:
                pdf_url = self.pdf.get_url()
                ui.button(icon="picture_as_pdf", on_click=lambda url=pdf_url: ui.navigate.to(url), color="primary").props("flat dense")
            self.label_value("title", self.ppt.title, compact=True)
            self.label_value("created", self.ppt.created, compact=True)
            if self.ppt.author:
                self.label_value("author", self.ppt.author, compact=True)

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

    @classmethod
    def get_ppt_header(cls,ppt,with_delim:bool=False):
        pres_url = f"/slides/{ppt.relpath}"
        name=ppt.basename.replace(".pptx","")
        pres_info = f"{name} ({len(ppt.getSlides())} slides)"
        if with_delim:
            ui.label("•").classes("text-gray-500")
        ui.link(pres_info, pres_url).classes("block mb-2").tooltip(ppt.title)


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
            pdf=PDF(self.solution,ppt)
            record["pdf"] = pdf.get_link()

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

    async def load_and_render_slider_viewer(self):
        self.slide_viewer.load_and_render(self.slide_grid_row)

    async def show_selected_slides(self, selected: List[dict]):
        """
        Load and display slides from the selected presentations.

        Args:
            selected: selected rows from the presentation list
        """
        self.slide_grid_row.clear()
        path_str=""
        delim=""
        for r in selected:
            ri = r.get("#")
            row = self.lod[ri]
            path = row.get("path")
            if path:
                ppt = self.ppt_set.get_ppt(path, relative=False)
                if ppt:
                    path_str+=f"{delim}{ppt.relpath}"
                    delim=","
        url=f"/slides/{path_str}"
        ui.navigate.to(url)

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
        self.pdf = PDF(solution, self.slide.ppt)
        self.total_slides = len(self.slide.ppt.getSlides())

    def show_pdf(self):
        # Show PDF preview if available
        if self.pdf.valid:
            pdf_url = self.pdf.get_url(page=self.slide.pdf_page)
            # Use an iframe to embed the PDF with specific page
            markup=f"""
            <iframe
                src="{pdf_url}"
                class="w-full"
                style="height:800px; border: 1px solid #ddd; border-radius: 4px;"
                loading="lazy">
            </iframe>
"""
            ui.html(markup)

    def render(self):
        """
        Render the slide details
        """
        presentation_view = PresentationView(self.solution, self.slide.ppt.relpath)
        presentation_view.render()
        #PresentationView.get_ppt_header(self.slide.ppt)
        # Add page navigation
        relpath = self.slide.ppt.relpath
        navigator = PageNavigator(
            current_page=self.slide.page,
            total_pages=self.total_slides,
            url_for_page=lambda page, path=relpath: f"/slide/{path}/{page}"
        )
        navigator.render()
        with ui.row():
            ui.label(f"#{self.slide.page} {self.slide.name} • {self.slide.title}")
            text = "\n".join(self.slide.getText())
            ui.html(f"<pre>{text}</pre>")

        with ui.row().classes("w-full my-2"):
            self.show_pdf()
