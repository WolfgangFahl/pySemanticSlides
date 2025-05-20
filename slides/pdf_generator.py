"""
Created on 2025-05-18

@author: wf
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import ngwidgets.persistent_log as log
from ngwidgets.persistent_log import Log
from ngwidgets.progress import Progressbar
from ngwidgets.shell import Shell
from dataclasses import dataclass, field

@dataclass
class FileSet:
    """
    Represents a set of files with a given extension
    """
    base_path: str
    ext: str
    paths: List[Path] = field(init=False)
    total: int = field(init=False)

    def __post_init__(self):
        base = Path(self.base_path)
        self.paths = list(self.glob_files(base, self.ext))
        self.total = len(self.paths)

    def glob_files(self, base_path: Path, ext: str):
        """
        Yield files with the specified extension in base_path.

        Args:
            base_path (Path): Directory to search.
            ext (str): File extension (e.g. 'pptx').

        Returns:
            Generator[Path]: Matching file paths.
        """
        for path in base_path.rglob(f"*.{ext}"):
            if not path.name.startswith("~$"):
                yield path

class PdfGenerator:
    """
    Generates PDF files from PowerPoint presentations using LibreOffice (soffice).
    """

    def __init__(self, debug: bool = False):
        """
        Initialize PdfGenerator with optional debug mode.

        Args:
            debug (bool): Enable debug output if True.
        """
        self.debug = debug
        self.log = Log()
        self.shell = Shell()
        self.ignores = ["Unknown property", "warn:"]
        self.check_soffice()

    def check_soffice(self):
        """
        Check if LibreOffice 'soffice' is available on the system.
        Logs an error if not found.
        """
        result = self.shell.run("which soffice", debug=self.debug)
        if result.returncode != 0:
            self.log.log("❌", "soffice", "LibreOffice 'soffice' not found in PATH")
        else:
            self.log.log("✅", "soffice", f"Found soffice at {result.stdout.strip()}")

    def generate_pdfs(self,
        pptx_set:FileSet,
        pdf_path,
        with_stats: bool = False,
        progress_bar: Optional[Progressbar] = None) -> Dict[Path, subprocess.CompletedProcess]:
        """
        Convert all .pptx files in pptx_set to PDFs using LibreOffice.

        Args:
            pptx_set(FileSet): FileSet of .pptx files.
            pdf_path (str | Path): Directory for output .pdf files.
            with_stats (bool): If True, show summary of results.
            progress_bar (Progressbar | None): Optional progress bar instance to update

        Returns:
            Dict[Path, subprocess.CompletedProcess]: Mapping from input files to process results.
        """
        procs = {}
        if progress_bar:
            progress_bar.total = pptx_set.total
            progress_bar.reset()
        for pptx_path in pptx_set.paths:
            base_name = pptx_path.stem
            msg = f"converting {base_name} to PDF"
            if self.debug:
                msg += f" in {pptx_path.parent}"
            self.log.color_msg(log.BLUE, msg)

            cmd = f'soffice --headless --invisible --convert-to pdf "{pptx_path}" --outdir "{pdf_path}"'
            result = self.shell.run(cmd, debug=self.debug, tee=False)
            procs[pptx_path] = result
            if progress_bar:
                progress_bar.update(1)

        if with_stats:
            self.shell.proc_stats("PDF conversions", procs, ignores=self.ignores)

        return procs
