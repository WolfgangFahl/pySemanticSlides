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

class NicePageNavigator:
    """
    Reactive page navigator with button controls
    """

    def __init__(self,
        parent,
        target_object,
        total_pages: int,
        current_page_attr: str="current_page",
        on_page_change=None):
        """
        Initialize the reactive page navigator

        Args:
            parent: parent ui element
            target_object: Object that contains the current_page attribute
            current_page_attr: Name of the current page attribute to bind to
            total_pages: Total number of pages
            on_page_change: Function to be called when page changes with new page number
        """
        self.parent=parent
        self.target_object = target_object
        self.current_page_attr = current_page_attr
        self.total_pages = total_pages
        self.on_page_change_callback = on_page_change

    def get_current_page(self) -> int:
        """Get current page from target object"""
        return getattr(self.target_object, self.current_page_attr)

    def set_current_page(self, page: int):
        """Set current page on target object and trigger callback"""
        page = max(1, min(page, self.total_pages))
        setattr(self.target_object, self.current_page_attr, page)
        if self.on_page_change_callback:
            self.on_page_change_callback(page)

    def on_first_page(self):
        """Navigate to first page"""
        self.set_current_page(1)

    def on_previous_page(self):
        """Navigate to previous page"""
        current = self.get_current_page()
        self.set_current_page(current - 1)

    def on_fast_backward(self):
        """Navigate 10 pages backward"""
        current = self.get_current_page()
        self.set_current_page(current - 10)

    def on_next_page(self):
        """Navigate to next page"""
        current = self.get_current_page()
        self.set_current_page(current + 1)

    def on_fast_forward(self):
        """Navigate 10 pages forward"""
        current = self.get_current_page()
        self.set_current_page(current + 10)

    def on_last_page(self):
        """Navigate to last page"""
        self.set_current_page(self.total_pages)

    def render(self):
        """Render the reactive page navigator"""
        with self.parent:
            with ui.row().classes("items-center justify-center gap-2 my-4"):
                ui.button("⏮", on_click=self.on_first_page).props("flat dense").tooltip("First Page")
                ui.button("⏪", on_click=self.on_fast_backward).props("flat dense").tooltip("Fast Backward (-10)")
                ui.button("◀", on_click=self.on_previous_page).props("flat dense").tooltip("Previous Page")

                # Page indicator with number input
                ui.number(
                    value=self.get_current_page(),
                    min=1,
                    max=self.total_pages,
                    step=1
                ).bind_value(self.target_object, self.current_page_attr).on('update:model-value', lambda: self.on_page_change_callback(self.get_current_page()) if self.on_page_change_callback else None).props("dense outlined").style("width: 80px").classes("mx-2")

                ui.label(f"of {self.total_pages}").classes("mx-2")

                ui.button("▶", on_click=self.on_next_page).props("flat dense").tooltip("Next Page")
                ui.button("⏩", on_click=self.on_fast_forward).props("flat dense").tooltip("Fast Forward (+10)")
                ui.button("⏭", on_click=self.on_last_page).props("flat dense").tooltip("Last Page")