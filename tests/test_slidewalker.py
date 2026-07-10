import json
import shutil
import tempfile
from pathlib import Path

from slides.slidewalker import SlideWalker
from tests.basetest import Basetest


class TestSlideWalker(Basetest):
    """
    test the slide walker
    """

    def setUp(self, debug=False, profile=True):
        """
        setUp and set the slides directory
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.debug = debug
        base_path = Path(__file__).parent.parent
        self.slidedir = f"{base_path}/examples/semanticslides"
        pass

    def test_slidewalker(self):
        """
        simple test for slidewalker
        """
        debug = self.debug
        #debug=True
        slidewalker = SlideWalker(self.slidedir)
        for kvp_name in ["newline-colon-comma","LG-Utf8-dots"]:
            slidewalker.set_key_value_parser_byname(kvp_name)
            json_str = slidewalker.dumpInfoToString("json", excludeHiddenSlides=True)
            if debug:
                print(json_str)
            pres_dict = json.loads(json_str)
            ppt_file = "SemanticSlides.pptx"
            self.assertTrue(ppt_file in pres_dict)
            pres = pres_dict[ppt_file]
            self.assertTrue("slides" in pres)
            slides = pres["slides"]
            self.assertTrue(len(slides) > 1)
            for slide in slides:
                for attr in ["page", "pdf_page", "title", "name", "text", "notes","notes_info"]:
                    self.assertTrue(attr in slide)
            pass

    def test_pptm_is_walked(self):
        """
        macro-enabled .pptm decks must be discovered, not only .pptx
        see https://github.com/WolfgangFahl/pySemanticSlides/issues/24
        """
        source = Path(self.slidedir) / "SemanticSlides.pptx"
        with tempfile.TemporaryDirectory() as tmp:
            pptm = Path(tmp) / "SemanticSlides.pptm"
            shutil.copy(source, pptm)
            slidewalker = SlideWalker(tmp)
            names = [ppt.basename for ppt in slidewalker.yieldPowerPointFiles(verbose=self.debug)]
            self.assertIn("SemanticSlides.pptm", names)
