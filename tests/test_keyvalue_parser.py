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
            #("test", "keywords", f"Title:Title{delim}Keywords:test{delim}Label:title"),
            #("test", "keywords", f"Title:Title{delim}Keywords:test"),
            #("test with spaces", "keywords", f"Title:Title{delim}Keywords:test with spaces{delim}Label:title"),
            #("test with spaces", "keywords", f"Title:Title{delim}Keywords:test with spaces"),
            #("SQL-DML", "keywords", f"Title:Title{delim}Keywords:SQL-DML"),
            #("SQL_DML", "keywords", f"Title:Title{delim}Keywords:SQL_DML"),
            #(None, "keywords", None),
            #(None, None, None),
            #("rel algebra, query plan","keywords", ' Name: Auswertungsplan einer SQL-Abfrage mit relationaler Algebra darstellbar•Titel: Kanonischer Auswertungsplan zu einer SQL-Anfrage•Lernziel: •RelQuery-OptimizeQuery-SQL2RA•Keywords: •rel• •algebra•, •query• plan '),
            #("1st normal form, database normalisation", "keywords",  "Name: •First_Normal_Form•Titel: Erste Normalform•Lernziel: •RelDesign-Normalform-1NF•Keywords: 1•st normal form, •database• •normalisation•Eine Relation   befindet sich in der ersten Normalform wenn die Wertebereiche der Attribute des Relationstypen atomar sind.•Also zum Beispiel String, Integer. Damit sind •zusammengesetzte•, •mengenwertige• •oder• •relationenwertige• Attribute •sind• •nicht• •erlaubt•.•Als Beispiel schauen wir uns die Relation Eltern an •In der ersten Eltern Relationsausprägung haben wir ein mengenwertiges Attribut Kind.•Die zweite Relationsausprägung hat keine mengenwertige Attribute mehr – hier wurden die mengen aufgelöst und stattdessen wurden mehrere Tupel eingeführt.•Der Begriff •NF²-Modelle •steht• •für• non-first-normal-form •Modelle•, also •Modelle• in •denen• •Attribut kann selbst wieder Menge von Attributen sein und ein Attributwert wieder eine Relation sein kann.•Im Folgenden gehen wir stets von Relationen in erster Normalform aus." )
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
                    kvp,text,expected=testParam
                    kv,errors=kvp.getKeyValues(text,keydefs)
                    if debug:
                        print(f"{text}")
                        print(json.dumps(kv,indent=2))
                        print(f"errors: {errors}")
                    if expected is not None:
                        for keyword in expected:
                            self.assertTrue(keyword in kv, f"{keyword} not found")
                            value=kv.get(keyword, None)
                            expected_value=expected[keyword]
                            self.assertEqual(expected_value, value,f"{kvp.__class__.__name__} can't parse {text} using config {kvp.config}") 
                except Exception as ex:
                    self.fail(str(ex))   