"""
Created on 2023-02-23

@author: wf
"""

import os
import sys
import traceback
import webbrowser
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from slides.version import Version


class SemSlides:
    """
    a semantic mediawiki for slides
    """

    def __init__(self, args):
        """
        constructor

        Args:
            args(Args): my command line arguments
        """
        self.args = args

    @classmethod
    def getArgParser(cls, version_msg) -> ArgumentParser:
        """
        Setup command line argument parser

        Args:
            description(str): the description
            version_msg(str): the version message

        Returns:
            ArgumentParser: the argument parser
        """
        parser = ArgumentParser(
            description=Version.description, formatter_class=RawDescriptionHelpFormatter
        )
        parser.add_argument(
            "-a",
            "--about",
            help="show about info [default: %(default)s]",
            action="store_true",
        )
        parser.add_argument(
            "--context",
            default="MetaModel",
            help="context to generate from [default: %(default)s]",
        )
        parser.add_argument(
            "-d", "--debug", dest="debug", action="store_true", help="show debug info"
        )
        parser.add_argument("-V", "--version", action="version", version=version_msg)
        parser.add_argument(
            "--wikiId",
            default="wiki",
            help="id of the wiki to generate for [default: %(default)s]",
        )
        return parser


def main(argv=None):
    """
    main routine
    """
    if argv is None:
        argv = sys.argv
    program_name = os.path.basename(sys.argv[0])  #

    debug = True
    try:
        program_version_message = (
            f"{program_name} (v{Version.version},{Version.updated})"
        )
        parser = SemSlides.getArgParser(program_version_message)
        args = parser.parse_args(argv[1:])
        semSlides = SemSlides(args)
        if args.about:
            print(program_version_message)
            print(f"see {Version.doc_url}")
            webbrowser.open(Version.doc_url)
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if debug:
            print(traceback.format_exc())
        return 2


if __name__ == "__main__":
    sys.exit(main())
