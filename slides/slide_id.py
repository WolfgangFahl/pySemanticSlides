"""
Created on 2025-06-05

@author: wf
"""
from slugify import slugify
from collections import Counter


class SlideId:
    """
    Generate slide IDs with local uniqueness
    """

    def __init__(self,
        ppt_max_length: int = 25,
        title_max_length: int = 45,
        page_digits: int = 3,
        min_title_length: int = 3):
        """
        Constructor

        Args:
            ppt_max_length(int): maximum length for presentation name slug
            title_max_length(int): maximum length for title slug
            page_digits(int): number of digits for page formatting
            min_title_length(int): minimum title length before using fallback
        """
        self.ppt_max_length = ppt_max_length
        self.title_max_length = title_max_length
        self.page_digits = page_digits
        self.min_title_length = min_title_length
        self.slide_registry = {}
        self.title_counts = Counter()

    def get_title_slug(self,title:str,slide_page:int):
        clean_title = title.replace('\n', ' ').strip()

        # Determine effective title
        if not clean_title or len(clean_title) < self.min_title_length:
            effective_title = f"slide{slide_page:03d}"
        else:
            effective_title = clean_title

        # Generate title slug
        title_slug = slugify(effective_title, max_length=self.title_max_length)
        return title_slug

    def register(self, ppt_name: str, slide_page: int, title: str):
        """
        Phase 1: Register slide and determine appropriate title
        """
        key = (ppt_name, slide_page)
        title_slug=self.get_title_slug(title, slide_page)
        # Count occurrences of this title slug
        self.title_counts[title_slug] += 1
        counter = self.title_counts[title_slug]

        # Build unique title slug with counter if needed
        if counter > 1:
            unique_title_slug = f"{title_slug}#{counter}"
        else:
            unique_title_slug = title_slug

        # Build slide ID: title_slug@page/ppt-slug-page
        ppt_slug = slugify(ppt_name, max_length=self.ppt_max_length)
        slide_id = f"{unique_title_slug}@{slide_page:0{self.page_digits}d}/{ppt_slug}"
        self.slide_registry[key] = slide_id

    def get_id(self, ppt_name: str, slide_page: int) -> str:
        """
        Phase 2: Lookup generated slide ID
        """
        key = (ppt_name, slide_page)
        slide_id= self.slide_registry.get(key, "")
        return slide_id