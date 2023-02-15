'''
Created on 2023-01-27

@author: wf
'''
import json
from tests.basetest import Basetest
from pathlib import Path
from slides.slidewalker import SlideWalker
from slides.keyvalue_parser import Keydef,KeyValueSplitParser,KeyValueParserConfig

class TestCollectKeyValuesFromNotes(Basetest):
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
        pres_list=slidewalker.dumpInfo(outputFormat='lod')
        return pres_list
    
    def testSlideNotes(self):
        """
        test handling the slide Notes
        """
        debug=self.debug
        #debug=True
        config=KeyValueParserConfig(record_delim="\n")
        kvp=KeyValueSplitParser(config=config)
        keydefs=[
            Keydef("Name","name"),
            Keydef("Title","title"),
            Keydef("Keywords","keywords",False),
            Keydef("Literature","literatur",True)
        ]
        kvp.setKeydefs(keydefs)
        pres_list=self.getPresentations()
        for _pres_file,pres_dict in pres_list.items():
            slide_records=pres_dict["slides"]
            for i,slide_record in enumerate(slide_records):
                notes=slide_record["notes"]
                notes_info=kvp.getKeyValues(notes)
                if debug:
                    print(json.dumps(notes_info,indent=2))
                self.assertEqual(0,len(kvp.errors))
                if i==1:
                    expected={
                        "name": "Why_semantify",
                        "title": "Why semantify your slides?",
                        "keywords": "Semantification, FAIR",
                        "literatur": [
                          "Furth2018",
                          "Fair2016"
                        ]
                    }
                    self.assertEqual(expected,notes_info)
                        
                pass