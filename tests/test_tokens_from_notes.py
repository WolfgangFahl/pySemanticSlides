"""
Created on 2023-01-27

@author: wf
"""

import json
from pathlib import Path

from slides.keyvalue_parser import Keydef, KeyValueParserConfig, KeyValueSplitParser,\
    SimpleKeyValueParser
from slides.slidewalker import SlideWalker
from tests.basetest import Basetest


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
        base_path = Path(__file__).parent.parent
        self.slidedir = f"{base_path}/examples/semanticslides"
        self.config_dir = base_path / "examples" / "KeyValueParser"
        pass

    def getPresentations(self):
        """ """
        slidewalker = SlideWalker(self.slidedir)
        pres_list = slidewalker.dumpInfo(outputFormat="lod")
        return pres_list

    def get_configs(self):
        debug=True
        keydefs = [
            Keydef("Name", "name"),
            Keydef("Title", "title"),
            Keydef("Keywords", "keywords", False),
            Keydef("Literature", "literatur", True),
        ]
        yaml_path = self.config_dir / "utf8dot_slides_keyvalues.yaml"
        configs={
            "default": KeyValueParserConfig(record_delim="\n", keydefs=keydefs),
            "utf-8-dot":  KeyValueParserConfig.ofYaml(yaml_path)
        }
        return configs

    def testSlideNotes(self):
        """
        test handling the slide Notes
        """
        pres_list = self.getPresentations()
        debug = self.debug
        #debug=True
        for config_name,config in self.get_configs().items():
            kvp = SimpleKeyValueParser(config=config)
            #kvp=KeyValueSplitParser(config=config) # still problematic!
            for _pres_file, pres_dict in pres_list.items():
                slide_records = pres_dict["slides"]
                for i, slide_record in enumerate(slide_records):
                    notes = slide_record["notes"]
                    notes_info = kvp.getKeyValues(notes)
                    expected=None
                    expected_i=1 if config_name=="default" else 2;
                    if i==expected_i:
                        if debug:
                            print(json.dumps(notes_info, indent=2))
                        error_count=len(kvp.errors)
                        if len(kvp.errors)>0:
                            for ei,error in enumerate(kvp.errors):
                                print(f"error {ei}:{error}")
                        self.assertEqual(0, error_count,config_name)
                        if config_name=="default":
                            expected = {
                                "name": "Why_semantify",
                                "title": "Why semantify your slides?",
                                "keywords": "Semantification, FAIR",
                                "literatur": ["Furth2018", "Fair2016"],
                            }
                        elif config_name=="utf-8-dot":
                            expected={
                              "lg": "LG42-42",
                              "name": "Key-Value-Parser",
                              "mainslide": "\u2714\ufe0f"
                            }
                            pass
                        self.assertEqual(expected, notes_info)

                pass
