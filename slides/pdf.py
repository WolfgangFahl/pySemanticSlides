"""
Created on 05.06.2025

@author: wf
"""

import os

from ngwidgets.widgets import Link


class PDF:
    """
    Portable Document File handling
    """

    def __init__(self, solution, ppt):
        self.solution = solution
        self.ppt = ppt
        self.pdf_name = self.ppt.basename.replace(".pptx", ".pdf")
        if self.solution.pdf_path:
            self.pdf_file = os.path.join(self.solution.pdf_path, self.pdf_name)
            self.valid = os.path.exists(self.pdf_file)
        else:
            self.pdf_file = None
            self.valid = False

    def get_url(self, page: int = None):
        url = f"/static/pdf/{self.pdf_name}" if self.valid else None
        if url and page:
            url = f"{url}#page={page}"
        return url

    def get_link(self, page: int = None):
        pdf_url = self.get_url(page=page)
        if pdf_url:
            pdf_link = Link.create(pdf_url, "📄 PDF")
        else:
            pdf_link = ""
        return pdf_link
