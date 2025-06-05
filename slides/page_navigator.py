"""
Created on 2025-05-16

@author: wf
"""

from ngwidgets.widgets import Link
from nicegui import ui


class PageNavigator:
    """
    Simple page navigator with URL generation callback
    """

    def __init__(self, current_page: int, total_pages: int, url_for_page):
        """
        Initialize the page navigator

        Args:
            current_page: Current page number (1-based)
            total_pages: Total number of pages
            url_for_page: Callback function that returns URL for a given page number
        """
        self.current_page = current_page
        self.total_pages = total_pages
        self.url_for_page = url_for_page

    def generate_markup(self) -> str:
        """Generate HTML markup for page navigation"""

        def get_link(page, symbol, tooltip) -> str:
            page_url = self.url_for_page(page)
            link = Link.create(page_url, symbol)
            if tooltip:
                pass
            return link

        # provide a page nav
        markup = f"""<div class="page-nav" style="display: flex; align-items: center; justify-content: center; gap: 15px; margin: 10px 0;">"""
        markup += get_link(1, "⏮", f"First Page (1/{self.total_pages})")
        markup += get_link(
            max(1, self.current_page - 10), "⏪", "Fast Backward (Jump -10 Pages)"
        )
        markup += get_link(max(1, self.current_page - 1), "◀", "Previous Page")
        markup += f"<span>Page {self.current_page} of {self.total_pages}</span>"
        markup += get_link(
            min(self.total_pages, self.current_page + 1), "▶", "Next Page"
        )
        markup += get_link(
            min(self.total_pages, self.current_page + 10),
            "⏩",
            "Fast Forward (Jump +10 Pages)",
        )
        markup += get_link(
            self.total_pages, "⏭", f"Last Page ({self.total_pages}/{self.total_pages})"
        )
        markup += "</div>"
        return markup

    def render(self):
        """Render the page navigator with a single HTML call"""
        markup = self.generate_markup()
        ui.html(markup)
