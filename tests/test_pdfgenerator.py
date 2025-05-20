"""
Created on 2025-05-18

Test PdfGenerator functionality.
"""

from pathlib import Path

from slides.pdf_generator import PdfGenerator, FileSet

from tests.basetest import Basetest


class TestPdfGenerator(Basetest):
    """
    Test the PdfGenerator class.
    """

    def setUp(self, debug=False, profile=True):
        """
        Set up test context.
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.debug = debug
        base_path = Path(__file__).parent.parent
        self.example_dir = base_path / "examples" / "semanticslides"
        self.output_dir =  Path("/tmp/pdfgenerator")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pptx_set=FileSet(self.example_dir,ext="pptx")

    def test_check_soffice(self):
        """
        Verify soffice is found or reported.
        """
        pdfgen = PdfGenerator(debug=self.debug)
        pdfgen.check_soffice()

    def test_generate_pdfs(self):
        """
        Generate PDFs for example .pptx files.
        """
        pdfgen = PdfGenerator(debug=self.debug)
        procs = pdfgen.generate_pdfs(self.pptx_set, self.output_dir, with_stats=True)
        self.assertTrue(len(procs) > 0)
        for input_path, _proc in procs.items():
            out_pdf = self.output_dir / f"{input_path.stem}.pdf"
            self.assertTrue(out_pdf.exists())

