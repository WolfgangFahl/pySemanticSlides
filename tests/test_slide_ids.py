"""
Created on 2025-06-05

@author: wf
"""
from pathlib import Path

from slides.slidewalker import SlideWalker, PPT

from slides.slide_id import SlideId
from tests.basetest import Basetest


class TestSlideIds(Basetest):
    """
    test slide ID validation and fixing
    """

    def setUp(self, debug=False, profile=True):
        """
        setUp and set the slides directory
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.debug = debug
        base_path = Path(__file__).parent.parent
        self.slidedir = f"{base_path}/examples"

    def need_fix_generator(self):
        slide_id=SlideId()
        title_limit=65
        debug=self.debug
        slidewalker = SlideWalker(self.slidedir, debug=debug)

        # Phase 1: Register all slides
        for ppt in slidewalker.yieldPowerPointFiles(verbose=debug):
            for slide in slidewalker.yieldSlides(ppt, verbose=debug):
                slide_id.register(ppt.basename, slide.page, slide.title)
        # Phase 2: Process and display
        for ppt in slidewalker.yieldPowerPointFiles(verbose=debug):
            print("%s" % ppt.basename)
            needs_fix = False

            for slide in slidewalker.yieldSlides(ppt, verbose=debug):
                clean_title = slide.title.replace('\n', ' ')[:title_limit]
                needs_fix = slide.name.startswith("Slide") or not slide.name.strip()
                marker = "❌" if needs_fix else "✅"
                if needs_fix:
                    slide.name = slide_id.get_id(ppt.basename, slide.page)
                    yield slide
                msg = f"{slide.page:03d}:{slide.name}\n {clean_title}"
                print(f"{marker} {msg}")
            yield ppt


    def test_slide_ids(self):
        """
        Test slide names and identify slides needing IDs
        """
        for _element in self.need_fix_generator():
            pass

    def test_fix(self):
        """
        Fix slide names that need IDs
        """
        return
        for element in self.need_fix_generator():
            if isinstance(element, PPT):
                ppt = element
                newFileName = ppt.filepath.replace(".pptx", "-fixed.pptx")
                ppt.save(newFileName)
                print(" -> Saved as %s" % newFileName)
            else:
                slide=element
                slide.slide.name=slide.name