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


class GridViewer:
    """
    Base class for grid-based viewers using ListOfDictsGrid
    """

    def __init__(
        self,
        solution: InputWebSolution,
        key_col: str,
        search_cols: List[str] = None,
        html_columns: List[int] = [1],
    ):
        self.solution = solution
        self.debug = self.solution.debug
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
        self.lod: List[dict] = []
        self.view_lod: List[dict] = []
        self.summary: str = ""
        self.delim: str = ""

    def to_view_lod(self):
        self.view_lod = []
        for ri, record in enumerate(self.lod):
            view_record = OrderedDict(record)
            view_record.move_to_end(self.key_col, last=False)
            view_record["#"] = ri
            view_record.move_to_end("#", last=False)
            self.view_lod.append(view_record)
        self.view_lod.sort(key=lambda r: r.get(self.key_col))

    async def render_grid(self, grid_row):
        grid_config = GridConfig(
            key_col=self.key_col,
            editable=True,
            multiselect=True,
            with_buttons=True,
            button_names=["all", "fit"],
            debug=self.debug,
        )
        with grid_row:
            if self.summary:
                ui.label(f"{self.summary}")
            self.setup_search()
            self.grid = ListOfDictsGrid(lod=self.view_lod, config=grid_config)
            self.grid.ag_grid._props["html_columns"] = self.html_columns
            self.grid.set_checkbox_selection(self.key_col)

    def load_lod(self):
        raise Exception("abstract load_lod called")

    async def render_view_lod(self, grid_row):
        self.to_view_lod()
        await self.render_grid(grid_row)


class SlidesViewer(GridViewer):
    """
    viewer for slides
    """
    def __init__(self, solution: InputWebSolution, ppts: List[PPT]):
        super().__init__(solution, "page", html_columns=[1, 2])
        self.ppts = ppts
        self.ppt_set = solution.ppt_set

    def load_lod(self):
        self.reset_lod()
        for ppt in self.ppts:
            slides = ppt.getSlides()
            self.summary += f"{self.delim}{ppt.basename}({len(slides)})"
            self.delim = ", "
            for slide in slides:
                slide_record = slide.asDict()
                slide_record["path"] = ppt.relpath
                self.lod.append(slide_record)

    def to_view_lod(self):
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


class PresentationsViewer(GridViewer):
    """
    viewer for presentations
    """
    def __init__(self, solution: InputWebSolution):
        super().__init__(solution, "path", html_columns=[1,2,3,4,5])
        self.ppt_set = solution.ppt_set
        self.slide_viewer = None
        self.task_runner = TaskRunner()

    def setup_ui(self):
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
        try:
            self.load_lod()
            await self.render_view_lod(self.grid_row)
        except Exception as ex:
            self.solution.handle_exception(ex)

    def load_lod(self):
        self.reset_lod()
        self.lod = self.ppt_set.as_lod()

    async def on_show_slides(self):
        selected = await self.grid.get_selected_rows()
        if not selected:
            ui.notify("No presentations selected")
            return
        await self.show_selected_slides(selected)

    async def on_generate_pdfs(self):
        self.task_runner.run_blocking(self.generate_pdfs)

    def generate_pdfs(self):
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
    def __init__(self, solution: InputWebSolution, slide: Slide):
        self.solution = solution
        self.slide = slide

    def render(self):
        with ui.card():
            ui.label(f"{self.slide.title}")
            ui.label(f"{self.slide.name}")
            ui.label(f"#{self.slide.page}")
            ui.html(f"<pre>{self.slide.getText()}</pre>")
            ui.button("Open", on_click=lambda: self.open_in_office())

    def open_in_office(self):
        self.slide.ppt.open_in_office()
