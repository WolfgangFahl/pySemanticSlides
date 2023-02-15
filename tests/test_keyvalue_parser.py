'''
Created on 2023-02-15

@author: wf
'''
from tests.basetest import Basetest
import json
from slides.keyvalue_parser import Split,Keydef,KeyValueSplitParser,KeyValueParserConfig
#,SimpleKeyValueParser, KeyValueParser, 

class TestKeyValueParser(Basetest):
    """
    test the key value parser
    """
    
    def testQuotedStringSplit(self):
        """
        test the quoted String Split class
        """
        testParams=[
            (
                "#",
                "A#B",
                ['A', 'B']
            ),
            (
                "|",
                "First|'Second|More|EvenMore'|Third",
                ['First', "'Second|More|EvenMore'", 'Third']
            ),
            (
                "•",
                "Name:Test•Title: Test•Extra: '1,2,3'•Keywords: A,B,C,'D,E',F",
                ['Name:Test', 'Title: Test', "Extra: '1,2,3'", "Keywords: A,B,C,'D,E',F"]
            ),
            (
                ",",
                "A,B,'C,D',E",
                ['A', 'B', "'C,D'", 'E']
            )
        ]
        debug=self.debug
        #debug=True
        for testParam in testParams:
            with self.subTest(testParam=testParam):
                delim,text,expected=testParam
                split=Split(delim=delim)
                parts=split.split(text)
                if debug:
                    print(parts)
                self.assertEqual(expected,parts)
        
    def yieldConfigs(self,debug:bool=False):
        """
        get different configs
        """
        for r in ["•","|","\n"]:
            for s in [":","→","="]:
                for v in [",",";"]:
                    config=KeyValueParserConfig(record_delim=r,key_value_delim=s,value_delim=v,debug=debug)
                    yield config
    
    def yieldConfiguredParsers(self,debug:bool=False):
        for parserClass in [KeyValueSplitParser]: #,SimpleKeyValueParser,KeyValueParser:
            for config in self.yieldConfigs(debug):
                parser=parserClass(config=config)
                yield parser
                
    def yieldTestParams(self,debug:bool=False):
        for parser in self.yieldConfiguredParsers(debug):
            s=parser.config.key_value_delim
            r=parser.config.record_delim
            v=parser.config.value_delim
            testParams = [
            (
                f"Name{s}Test{r}Title{s} Test{r}Extra{s} '1,2,3'{r}Keywords{s} A{v}B{v}C{v}'D,E'{v}F",
                0,
                {
                  "name": "Test",
                  "title": "Test",
                  "extra": "1,2,3",
                  "keywords": [
                    "A",
                    "B",
                    "C",
                    "D,E",
                    "F"
                  ]
                }
            ),
            (
                f'Name{s} SQL Geschachtelte Anfragen{r}Titel{s}  Quantorensimulation  in SQL - Geschachtelte Anfragen{r}Lernziel{s}  SQL-DML-NestedQueries{r}Keywords{s} SQL{v} SQL Syntax{v}  nested   queries',
                0,
                {
                  "name": "SQL Geschachtelte Anfragen",
                  "title": "Quantorensimulation  in SQL - Geschachtelte Anfragen",
                  "Lernziel": "SQL-DML-NestedQueries",
                  "keywords": [
                      "SQL",
                      "SQL Syntax",
                      "nested   queries"
                    ]
                }
            ),
            (
                f"Title{s}Title{r}Keywords{s}test{r}Label{s}title",
                0,
                {
                  "title": "Title",
                  "keywords": [
                    "test"
                  ],
                  "label": "title"
                }
            ),
            ( 
                f"Title{s}Title{r}Keywords{s}test with spaces{r}Label{s}title",
                0,
                {
                  "title": "Title",
                  "keywords": [
                    "test with spaces"
                  ],
                  "label": "title"
                }
            ),
            ( 
                None,
                0,
                {}
            ),
            ( 
                "",
                0,
                {}
            ),
            (   
                f"Key{s}Value1{s}Value2",
                1,
                {} 
            ),
            (   
                f"Key{s}Value1{r}",
                1,
                {} 
            )
            ]
            for testParam in testParams:
                yield (parser,)+testParam
        
    def test_keywordExtraction(self):
        """
        tests the keyword extraction
        """
        debug=self.debug
        #debug=True
        keydefs=[
            Keydef("Name","name"),
            Keydef("Title","title"),
            Keydef("Titel","title"),
            Keydef("Extra","extra"),
            Keydef("Label","label"),
            Keydef("Keywords","keywords",True)
        ]
        for testParam in self.yieldTestParams(debug):
            with self.subTest(testParam=testParam):
                try:
                    kvp,text,expected_errors,expected=testParam
                    kv,errors=kvp.getKeyValues(text,keydefs)
                    if debug:
                        print(f"{text}")
                        print(json.dumps(kv,indent=2))
                    if debug or len(errors)>expected_errors:
                        print(f"errors: {errors}")
                    self.assertEqual(expected_errors,len(errors))
                    if expected is not None and expected_errors==0:
                        for keyword in expected:
                            self.assertTrue(keyword in kv, f"{keyword} not found")
                            value=kv.get(keyword, None)
                            expected_value=expected[keyword]
                            self.assertEqual(expected_value, value,f"{kvp.__class__.__name__} can't parse {text} using config {kvp.config}") 
                except Exception as ex:
                    self.fail(str(ex))   