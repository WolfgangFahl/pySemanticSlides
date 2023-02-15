'''
Created on 2023-02-14

@author: wf
'''
import pyparsing as pp
import typing
from dataclasses import dataclass

@dataclass
class KeyValueParserConfig():
    """
    a configuration for a key/value Parser
    """
    key_value_delim:str=":"
    record_delim:str="•"
    value_delim:str=","
    quote:str="\'"
    strip:bool=True
    ignore_errors:bool=True
    defined_keys_only:bool=False
    debug:bool=False
    
@dataclass
class Keydef():
    """
    a key definition
    """
    keyword: str
    key: str
    has_list: bool=False
    
    @classmethod
    def as_dict(cls,keydefs:typing.List['Keydef'])->typing.Dict[str,'Keydef']:
        """
        convert the given list of keydefs to a dict by keyword
        
        Args:
            keydefs(list): the list of key defs
            
        Returns:
            dict: a dict keyword -> Keydef
        
        """
        keydefs_by_keyword={}
        for keydef in keydefs:
            keydefs_by_keyword[keydef.keyword]=keydef
        return keydefs_by_keyword
    
class Split():
    """
    quoted string splitter
    """
    
    def __init__(self,delim:str=',',quote:str="'",unicode_chars:str="•→",keep_quotes:bool=True):
        """
        constructor
        
        Args:
            delim(str): the delimiter char, default comma
            quote(str): the quote char, default single quote
            unicode_chars(str): unicode characters to allow
            keep_quotes(str): if True keep the quoted strings if False remove quotes
            
        """
        self.delim=delim
        self.quote=quote
        self.keep_quotes=keep_quotes
        pp.ParserElement.setDefaultWhitespaceChars("")
        self.g_quoted=pp.QuotedString(quote_char=quote)
        self.g_value = pp.OneOrMore(pp.Word(pp.printables+unicode_chars+" ", excludeChars=delim+quote) | self.g_quoted)
        self.g_quoted.add_parse_action(lambda x:
            f"{quote}{x[0]}{quote}" if self.keep_quotes else f"{x[0]}"
        )
        self.g_value.add_parse_action(lambda x: 
            "".join(x) if len(x) > 1 else x
        )  
        self.g_split = pp.delimited_list(self.g_value, delim=delim)
        pass

    def split(self,text:str,)->list:
        """
        split the given text with my delim acknowleding my quote char for quoted strings
        
        Args:
            text(str): the text to split
            
        Returns:
            list: a list of strings
        """
        parse_result=self.g_split.parse_string(text, parse_all=True)
        result_list=parse_result.asList()
        return result_list
    
class KeyValueSplitParser():
    """
    Key / Value Parser
    
    see https://stackoverflow.com/questions/75266188/pyparsing-syntax-tree-from-named-value-list/75270267#75270267
    """
    
    def __init__(self,config:KeyValueParserConfig):
        """
        constructor
        
        Args:
            config(KeyValueParserConfig): the configuration to use
        """
        self.config=config
        
    def getKeyValues(self,text:str,keydefs:typing.List[Keydef])->dict:
        """
        get key/value pairs from the given text using the configured keys definition
        
        Args:
            text(str): the text to parser
            
        Returns:
            dict: the resulting key-value pairs
        """
        def add_error(error_msg:str):
            """
            add the given error
            
            Args:
                error_msg(str): the error to add
            """
            if self.config.debug:
                print(error_msg)
            errors.append(error_msg)
         
        errors=[]   
        result = dict()
        keydefs_by_keyword=Keydef.as_dict(keydefs)
        if text:
            try: 
                rsplit=Split(delim=self.config.record_delim)
                records=rsplit.split(text)
            except Exception as rsplit_ex:
                add_error(f"record split failed {rsplit_ex}")
                records=[]
            for record in records:
                key_value_split=Split(delim=self.config.key_value_delim)
                key_values=key_value_split.split(record)
                if len(key_values)!=2:
                    add_error(f"{key_values} has {len(key_values)}) elements but should have two")
                    continue
                else:
                    key_str=key_values[0]
                    keyword=key_str.strip()
                    values_str=key_values[1]
                    # is the keyword defined
                    if not keyword in keydefs_by_keyword:
                        if self.config.defined_keys_only:
                            add_error(f"undefined keyword {keyword}")
                        key=keyword
                        value=values_str
                    else:
                        keydef=keydefs_by_keyword[keyword]
                        # map keyword to key
                        key=keydef.key
                        values_split=Split(delim=self.config.value_delim,keep_quotes=False)
                        if keydef.has_list:
                            values=values_split.split(values_str)
                            if self.config.strip:
                                stripped_values=[]
                                for value in values:
                                    stripped_values.append(value.strip())
                                values=stripped_values
                            # value is a list
                            value=values
                        else:
                            value=values_str
                    if self.config.strip and isinstance(value,str):
                        value=value.strip()
                result[key]=value
        return result,errors

class KeyValueParser():
    """
    Key Value Parser (which won't handle all details properly)
    see https://stackoverflow.com/a/75270267/1497139
    """
    
    def __init__(self,config:KeyValueParserConfig):
        """
        constructor
        
        Args:
            config(KeyValueParserConfig): the configuration to use
        """
        self.config=config      
        if config.record_delim=="\n":
            pp.ParserElement.setDefaultWhitespaceChars("\t")
        else:
            pp.ParserElement.setDefaultWhitespaceChars("\n")
        pass
        # set local variable from config
        record_delim=self.config.record_delim
        key_value_delim=self.config.key_value_delim
        value_delim=self.config.value_delim
        quote=self.config.quote
        keys=self.config.keys
        #
        # initialize grammar
        # 
        # valid keys are alphas
        g_key = pp.Word(pp.alphas)
        # items may not have record or value delimiters or must be quoted
        g_item = pp.Word(pp.printables+" ", excludeChars=record_delim+value_delim+quote) | pp.QuotedString(quote_char=quote)
        # a value is a value_delim delimited list of items
        g_value = pp.delimited_list(g_item, delim=value_delim)
        l_key_value_sep = pp.Suppress(pp.Literal(key_value_delim))
        g_key_value = g_key + l_key_value_sep + g_value
        self.g_grammar = pp.delimited_list(g_key_value, delim=record_delim)
            
        g_key.add_parse_action(lambda x: 
            keys[x[0]] if x[0] in keys else x
        )
        g_value.add_parse_action(lambda x: 
            [x] if len(x) > 1 else x
        )
        g_key_value.add_parse_action(lambda x: 
            (x[0], x[1].as_list()) if isinstance(x[1],pp.ParseResults) else (x[0], x[1])
        )
        pass
    
    def getKeyValues(self,text:str)->dict:
        """
        get key/value pairs from the given text using the configured keys definition
        
        Args:
            text(str): the text to parser
            
        Returns:
            dict: the resulting key-value pairs
        """
        key_values = dict()
        if text:         
            try:
                for k,v in self.g_grammar.parse_string(text, parse_all=True):
                    if self.config.strip:
                        if isinstance(v,list):
                            for vi in list:
                                if vi:
                                    vi=vi.strip()
                        else:
                            v=v.strip()
                    key_values[k] = v
            except Exception as ex:
                if self.config.ignore_errors:
                    if self.config.debug:
                        print(f"parsing {text} failed: \n{str(ex)}")
                else:
                    raise ex
        return key_values
    
class SimpleKeyValueParser():
    """
    a simple key value parser (which won't handle quote properly)
    """
    
    def __init__(self,config:KeyValueParserConfig):
        """
        constructor
        
        Args:
            config(KeyValueParserConfig): the configuration to use
        """
        self.config=config
 
    def getKeyValues(self,text:str)->dict:
        """
        get key/value pairs from the given text using the configured keys definition
        
        Args:
            text(str): the text to parser
            strip(bool): if True strip leading and trailing blanks from values
            ignore_errors(bool): if True ignore errors
            
        Returns:
            dict: the resulting key-value pairs
        """
        
        def add_error(error_msg:str):
            """
            add the given error
            
            Args:
                error_msg(str): the error to add
            """
            if self.config.debug:
                print(error_msg)
            errors.append(error_msg)
            
        result={}
        errors=[]
        key_values=text.split(self.config.record_delim)
        for key_value in key_values:
            if not self.config.key_value_delim in key_value:
                error_msg=f"missing key_value delimiter '{self.config.key_value_delim} in {key_value}"
                add_error(error_msg)
                if self.config.ignore_errors:
                    continue
            parts=key_value.split(self.config.key_value_delim)
            if len(parts)>2:
                error_msg=(f"notes syntax error: {key_value} has {len(parts)}) elements but should have two")
                add_error(error_msg)
                break
            # parsed key and value
            pkey,value=parts[0],parts[1]
            pkey=pkey.strip()
            if self.config.strip:
                value=value.strip()
            if pkey in self.config.keys:
                key=self.config.keys[pkey]
            else:
                if self.config.defined_keys_only:
                    error_msg=f"undefined key {pkey}"
                    add_error(error_msg)
                else:
                    key=pkey
            if self.config.split_values and self.config.value_delim in value:
                value=value.split(self.config.value_delim)
            result[key]=value # could do another split here if need be
            if not self.config.ignore_errors:
                error_str="\n".join(errors)
                raise Exception(f"key/value parsing of {text} failed with {len(errors)} errors:\n{error_str}")
        return result