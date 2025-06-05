"""
Created on 2025-06-05

@author: wf
"""

from nicegui import ui
from nicegui_pdf.pdf_viewer import PdfViewer

from slides.slide_viewer import PresentationView


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

    async def load_and_render(self):
        """
        Load presentation data and render the view
        """
        with self.solution.content_div:
            self.render()
            ui.number().bind_value(self, "current_page")
            pdf_url = self.pdf.get_url()
            self.pdf_viewer = (
                PdfViewer(pdf_url)
                .classes("w-full")
                .style("border: solid 1px gray;")
                .bind_current_page(self)
            )
        pass
