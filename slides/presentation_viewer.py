"""
Created on 2025-06-05

@author: wf
"""
from nicegui import ui
from nicegui_pdf.pdf_viewer import PdfViewer
from slides.slide_viewer import PresentationView
from slides.page_navigator import NicePageNavigator

class SinglePresentationView(PresentationView):
    """
    Specialized presentation view with PDF viewer and page navigation
    """

    def __init__(self, solution, ppt_path: str):
        """
        Initialize the single presentation view

        Args:
            solution: The web solution instance
            ppt_path: Path to the presentation file
        """
        super().__init__(solution, ppt_path)
        self.current_page = 1
        self.pdf_markup = None
        self.page_navigator = None
        self.page_number_input = None

    def show_pdf_viewer(self,pdf_url):
        self.pdf_viewer = (
                PdfViewer(pdf_url)
                .classes("w-full")
                .style("border: solid 1px gray;")
                .bind_current_page(self)
        )

    def update_pdf(self,pdf_url):
        """
        update my pdf markup
        """
        markup = f"""
            <iframe
                src="{pdf_url}"
                class="w-full"
                style="height:800px; border: 1px solid #ddd; border-radius: 4px;"
                loading="lazy">
            </iframe>
"""
        self.pdf_markup.content=markup

    def render_slide_info(self):
        """Create toggleable slide information structure"""
        self.slide_info_expansion = ui.expansion("", icon="info").classes("w-full")
        with self.slide_info_expansion:
            self.slide_info_text = ui.html("")
        self.update_slide_info()

    def update_slide_info(self):
        """Update slide information content"""
        slide = self.solution.ppt_set.get_slide(self.ppt_path, page=self.current_page, relative=True)
        if slide:
            self.slide_info_expansion.text = f"Slide #{slide.page}: {slide.name} • {slide.title}"
            text = "\n".join(slide.getText())
            self.slide_info_text.content = f"<pre>{text}</pre>"

    async def load_and_render(self):
        """
        Load presentation data and render the view
        """
        with self.solution.content_div:
            self.render()
            with self.header_row:
                self.page_navigator = NicePageNavigator(
                    parent=self.header_row,
                    target_object=self,
                    total_pages=self.total_slides,
                    current_page_attr="current_page",
                    on_page_change=self.on_page_changed
                )
                self.page_navigator.render()
            # Add slide information section
            with ui.row() as self.info_row:
                self.render_slide_info()
            with ui.row() as self.pdf_row:
                pdf_url = self.pdf.get_url()
                # wait until https://github.com/peerdavid/nicegui-pdf/issues/1 is fixed
                #self.show_pdf_viewer(pdf_url)
                self.pdf_markup=ui.html().classes("items-center gap-2 w-full")
                self.update_pdf(pdf_url)

    def on_page_changed(self, page: int):
        """
        Handle page change events - update PDF iframe

        Args:
            page: New page number
        """
        if self.pdf_markup and self.pdf:
            pdf_url = self.pdf.get_url(page=page)
            self.update_pdf(pdf_url)
            self.update_slide_info()
