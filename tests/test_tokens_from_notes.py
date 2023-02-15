'''
Created on 2023-01-27

@author: wf
'''
from tests.basetest import Basetest
from pathlib import Path
from slides.slidewalker import SlideWalker

class TestCollectTokensFromNotes(Basetest):
    """
    test the handling of slide notes information
    
    see https://stackoverflow.com/questions/75266188/pyparsing-syntax-tree-from-named-value-list
    """
    
    def setUp(self, debug=False, profile=True):
        """
        setUp and set the slides directory
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.debug = debug
        base_path=Path(__file__).parent.parent
        self.slidedir=f"{base_path}/examples"
        pass
    
    def getPresentations(self):
        """
        """
        slidewalker = SlideWalker(self.slidedir)
        slidewalker.dump
        
    