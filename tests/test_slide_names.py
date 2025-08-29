"""
Created on 2025-08-29

@author: wf
"""
import json
from pathlib import Path

from slides.slide_names import SlideNames
from tests.basetest import Basetest


class TestSlideNames(Basetest):
    """
    test the SlideNames class
    """

    def setUp(self, debug=True, profile=True):
        """
        setUp and set the slides directory
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.debug = debug
        base_path = Path(__file__).parent.parent
        self.slidedir = f"{base_path}/examples/ScalingUpSemantics"

    def test_iter_vars(self):
        """
        simple test for SlideNames.iter_vars
        """
        ppt_file = Path(self.slidedir) / "mungall-swat4hcls-2023.pptx"
        slidenames = SlideNames(ppt_file)
        slides = list(slidenames.iter_vars())
        if self.debug:
            print(f"found {len(slides)} slides in {ppt_file}")
        self.assertTrue(len(slides) > 1)
        for slide in slides:
            for attr in ["page", "title", "name"]:
                self.assertTrue(attr in slide)
            if self.debug:
                print(json.dumps(slide, indent=2))
