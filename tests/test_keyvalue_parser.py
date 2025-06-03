"""
Created on 2023-02-15

@author: wf
"""

import json
from pathlib import Path

from slides.keyvalue_parser import (
    Keydef,
    KeyValueParser,
    KeyValueParserConfig,
    KeyValueSplitParser,
    SimpleKeyValueParser,
    Split,
)

from tests.basetest import Basetest


class TestKeyValueParser(Basetest):
    """
    test the key value parser
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        base_path = Path(__file__).parent.parent
        self.example_dir = base_path / "examples" / "KeyValueParser"

    def testQuotedStringSplit(self):
        """
        test the quoted String Split class
        """
        testParams = [
            ("#", "A#B", ["A", "B"]),
            (
                "|",
                "First|'Second|More|EvenMore'|Third",
                ["First", "'Second|More|EvenMore'", "Third"],
            ),
            (
                "•",
                "Name:Test•Title: Test•Extra: '1,2,3'•Keywords: A,B,C,'D,E',F",
                [
                    "Name:Test",
                    "Title: Test",
                    "Extra: '1,2,3'",
                    "Keywords: A,B,C,'D,E',F",
                ],
            ),
            (",", "A,B,'C,D',E", ["A", "B", "'C,D'", "E"]),
        ]
        debug = self.debug
        # debug=True
        for testParam in testParams:
            with self.subTest(testParam=testParam):
                delim, text, expected = testParam
                split = Split(delim=delim)
                parts = split.split(text)
                if debug:
                    print(parts)
                self.assertEqual(expected, parts)

    def testNotAsList(self):
        """
        test the list handling
        """
        debug = True
        keydefs = [Keydef("Keywords", "keyword")]
        config = KeyValueParserConfig(keydefs=keydefs)
        kvp = KeyValueSplitParser(config=config)
        for text, expected in [
            ("Keywords: a,b,c", "a,b,c"),
            ("Keywords: 'a','b,c','d'", "'a','b,c','d'"),
        ]:
            kv_dict = kvp.getKeyValues(text)
            self.assertTrue(len(kvp.errors) == 0)
            if debug:
                print(kv_dict)
            self.assertEqual(expected, kv_dict["keyword"])

    def yieldConfigs(self, debug: bool = False):
        """
        get different configs
        """
        for r in ["•", "|", "\n"]:
            for s in [":", "→", "="]:
                for v in [",", ";"]:
                    config = KeyValueParserConfig(
                        record_delim=r,
                        key_value_delim=s,
                        value_delim=v,
                        debug=debug
                    )
                    yield config

    def yieldConfiguredParsers(self, debug: bool = False):
        """
        generate a loop over the available parser
        """
        for parserClass in [
            KeyValueSplitParser,
            SimpleKeyValueParser,
            # causes too many errors - see comment to
            # https://stackoverflow.com/a/75270267/1497139
            # uncomment to try out and fix
            # KeyValueParser
        ]:
            for config in self.yieldConfigs(debug):
                parser = parserClass(config=config)
                yield parser

    def yieldTestParams(self, debug: bool = False):
        """
        generate a loop over combinations of delimiters
        as ParserConfigurations
        """
        for parser in self.yieldConfiguredParsers(debug):
            s = parser.config.key_value_delim
            r = parser.config.record_delim
            v = parser.config.value_delim
            testParams = [
                (
                    f"Name{s}Test{r}Title{s} Test{r}Extra{s} '1,2,3'{r}Keywords{s} A{v}B{v}C{v}'D,E'{v}F",
                    0,
                    {
                        "name": "Test",
                        "title": "Test",
                        "extra": "'1,2,3'",
                        "keywords": ["A", "B", "C", "D,E", "F"],
                    },
                ),
                (
                    f"Name{s} SQL Geschachtelte Anfragen{r}Titel{s}  Quantorensimulation  in SQL - Geschachtelte Anfragen{r}Lernziel{s}  SQL-DML-NestedQueries{r}Keywords{s} SQL{v} SQL Syntax{v}  nested   queries",
                    0,
                    {
                        "name": "SQL Geschachtelte Anfragen",
                        "title": "Quantorensimulation  in SQL - Geschachtelte Anfragen",
                        "Lernziel": "SQL-DML-NestedQueries",
                        "keywords": ["SQL", "SQL Syntax", "nested   queries"],
                    },
                ),
                (
                    f"Title{s}Title{r}Keywords{s}test{r}Label{s}title",
                    0,
                    {"title": "Title", "keywords": ["test"], "label": "title"},
                ),
                (
                    f"Title{s}Title{r}Keywords{s}test with spaces{r}Label{s}title",
                    0,
                    {
                        "title": "Title",
                        "keywords": ["test with spaces"],
                        "label": "title",
                    },
                ),
                (None, 0, {}),
                ("", 0, {}),
                (f"Key{s}Value1{s}Value2", 1, {}),
                (f"Key{s}Value1{r}", 1, {}),
            ]
            for testParam in testParams:
                yield (parser,) + testParam

    def test_keywordExtraction(self):
        """
        tests the keyword extraction
        """
        debug = self.debug
        # debug=True
        keydefs = [
            Keydef("Name", "name"),
            Keydef("Title", "title"),
            Keydef("Titel", "title"),
            Keydef("Extra", "extra"),
            Keydef("Label", "label"),
            Keydef("Keywords", "keywords", True),
        ]
        for testParam in self.yieldTestParams(debug):
            with self.subTest(testParam=testParam):
                try:
                    kvp, text, expected_errors, expected = testParam
                    kvp_name = kvp.__class__.__name__
                    if text and (kvp.config.quote in text) and ("Simple" in kvp_name):
                        continue
                    kvp.config.keydefs=keydefs
                    kvp.config.__post_init__()
                    kv = kvp.getKeyValues(text)
                    if debug:
                        print(f"{text}")
                        print(json.dumps(kv, indent=2))
                    if debug or len(kvp.errors) > expected_errors:
                        print(f"errors: {kvp.errors}")
                    self.assertEqual(expected_errors, len(kvp.errors))
                    if expected is not None and expected_errors == 0:
                        for keyword in expected:
                            self.assertTrue(keyword in kv, f"{keyword} not found")
                            value = kv.get(keyword, None)
                            expected_value = expected[keyword]
                            self.assertEqual(
                                expected_value,
                                value,
                                f"{kvp_name} can't parse {text} using config {kvp.config}",
                            )
                except Exception as ex:
                    self.fail(str(ex))

    def testLoadConfigFromYaml(self):
        """
        test loading config from YAML file
        """
        debug = self.debug
        #debug=True
        yaml_file = self.example_dir / "dbis_slides_keyvalues.yaml"
        config = KeyValueParserConfig.ofYaml(str(yaml_file))
        if debug:
            print(json.dumps(config.keydefs_by_keyword,indent=2,default=str))

