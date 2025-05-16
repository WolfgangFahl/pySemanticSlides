import json
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
        # debug=True
        slidewalker = SlideWalker(self.slidedir)
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
            for attr in ["page", "pdf_page", "title", "name", "text", "notes"]:
                self.assertTrue(attr in slide)
        pass
