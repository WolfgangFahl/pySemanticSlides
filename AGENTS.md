# AGENTS.md - pySemanticSlides

## Project Overview

pySemanticSlides turns a folder of PowerPoint presentations (`.pptx` and
macro-enabled `.pptm`) into a **knowledge graph**. It reads each slide's title,
text runs and notes — including semantic key/value annotations placed in the
slide notes — and emits structured JSON/CSV/text or a **Semantic MediaWiki**.
It is a Python library plus CLI tools built on
[python-pptx](https://pypi.org/project/python-pptx/).

- **GitHub**: https://github.com/WolfgangFahl/pySemanticSlides
- **Wiki**: https://wiki.bitplan.com/index.php/PySemanticSlides
- **PyPI**: https://pypi.org/project/pySemanticSlides/
- **Agent**: [Agent/Guido](https://media.bitplan.com/index.php/Agent/Guido) — Python developer agent following BITPlan conventions
- **Agent rules**: [Agent/Guido/BITPlan](https://media.bitplan.com/index.php/Agent/Guido/BITPlan) — canonical BITPlan Python conventions

## Commands

The package installs four console scripts (see `[project.scripts]` in `pyproject.toml`):

| Command | Entry point | Purpose |
|---------|-------------|---------|
| `slidewalker` | `slides.slidewalker:main` | Walk a folder and extract metadata for all presentations (JSON/CSV/txt) |
| `semslides` | `slides.semslides:main` | Generate a Semantic MediaWiki from the annotated slides |
| `slidebrowser` | `slides.slide_browser_cmd:main` | Interactive slide viewer |
| `slidenames` | `slides.slide_names:main` | List / set the internal slide names |

## Key Files

| File | Purpose |
|------|---------|
| `slides/slidewalker.py` | Core: `SlideWalker`, `PPT`, `Slide` — discover presentations, extract title/text/notes; the `slidewalker` CLI |
| `slides/keyvalue_parser.py` | Parse `key: value` semantic annotations from slide notes (uses `pyparsing`) |
| `slides/semslides.py` | Semantic MediaWiki generation (`semslides` CLI) |
| `slides/slide_browser.py`, `slides/slide_browser_cmd.py` | Interactive slide browser (`slidebrowser` CLI) |
| `slides/slide_names.py` | List/set slide names (`slidenames` CLI) |
| `slides/slide_id.py` | Slide id / slug generation |
| `slides/pdf.py`, `slides/pdf_generator.py` | Convert presentations to PDF via LibreOffice (`soffice`) |
| `slides/doi.py` | DOI / literature metadata lookup for annotations |
| `slides/page_navigator.py`, `slides/presentation_viewer.py`, `slides/slide_viewer.py` | Viewer components |
| `slides/version.py`, `slides/__init__.py` | Version metadata (`__version__` is the single source, read by hatch) |
| `tests/test_slidewalker.py` | Tests for folder walking and metadata extraction (incl. `.pptm` discovery) |
| `tests/test_keyvalue_parser.py`, `tests/test_tokens_from_notes.py` | Tests for the notes annotation parser |
| `tests/test_slide_names.py`, `tests/test_slide_ids.py` | Tests for slide naming / ids |
| `tests/test_pdfgenerator.py` | Tests for PDF generation |
| `tests/test_doi.py` | Tests for DOI lookup |
| `examples/semanticslides/SemanticSlides.pptx` | Bundled example deck used by the tests and README screenshot |

## Supported Input

Both `.pptx` and macro-enabled `.pptm` presentations are walked
(`SlideWalker` discovers `(".pptx", ".pptm")`; `~$` lock files are skipped).
python-pptx opens both package types.

## Coding Conventions

This project follows the [Agent/Guido/BITPlan](https://media.bitplan.com/index.php/Agent/Guido/BITPlan)
conventions. Key points; the wiki page is the canonical source.

### Style

- **Formatter**: `black` + `isort` — run `scripts/blackisort` before committing.
- **Line length**: 88 characters (black default).
- **Docstrings**: Google-style with type hints on public functions and classes.
- **Imports**: top-level, absolute; three groups (stdlib, third-party, local).
- **No ruff/flake8/pylint/mypy** unless explicitly configured.

### Naming

- **Classes**: PascalCase (`SlideWalker`, `PPT`, `Slide`)
- **Functions/methods**: snake_case for new code; legacy camelCase kept for compatibility
- **Constants**: UPPER_SNAKE_CASE
- **Test files**: `tests/test_<module>.py`; test classes `TestXxx` inheriting from `Basetest`
- **All output is English** (wiki, code, commit messages).

### Testing

- **Framework**: `unittest` (not pytest). Test classes inherit from `Basetest`.
- Run under the login-shell Python (3.12), e.g. `python -m unittest discover -s tests`
  or `scripts/test`. `scripts/test -g` uses `green`.
- **`scripts/test` must be green** before committing.

## Versioning

- `slides/__init__.py` `__version__` is the single source of truth (hatch reads it).
- Bump semantically: new feature → minor, fix → patch. Keep it **≥ the latest PyPI
  release** (a feature landed on top of the released `0.3.x` becomes `0.4.0`).
- Update `slides/version.py` `updated` to the ISO date on release-worthy changes.

## Quality Assurance

Run `checkos` to verify project compliance (README badges, workflows, pyproject,
scripts):

```bash
checkos -p pySemanticSlides --local
```

`build.yml` keeps a lean run matrix (`python-version: [ '3.12' ]`) while a commented
line carries the full `python-version: [ '3.10', '3.11', '3.12', '3.13' ]` range
that `checkos` substring-checks — mirror this pattern for the `os` matrix too.

## Running

```bash
# Install (editable for development)
pip install -e .

# Walk the example deck
slidewalker --rootPath examples/semanticslides -f json

# Format, test, check before committing
scripts/blackisort
scripts/test
checkos -p pySemanticSlides --local
```

## Dependencies

- `python-pptx` — read `.pptx` / `.pptm` packages
- `pyparsing` — parse notes annotations
- LibreOffice (`soffice`) — PDF generation
- `ngwidgets`, `pyLoDStorage`, `graphviz`, `isbnlib`, `bibtexparser`, `pylatexenc`,
  `tqdm`, `python-slugify` — see `pyproject.toml`
