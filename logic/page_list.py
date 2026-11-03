"""The list of every page of the app.

Each page file in `pages/` must be registered here; `entry_point.py`
passes them all to `st.navigation`. Use `pages.<name>` wherever a page
is needed (`init_page`, `switch_page_bttn`...), instead of a file path.
"""
from dataclasses import dataclass, asdict
from typing import Iterable

from streamlit import Page
from streamlit.navigation.page import StreamlitPage


@dataclass
class _Pages:
    """Registry of the app's pages, one attribute per page.

    A dataclass is a class whose attributes are declared as annotated
    class variables; Python writes `__init__` for it. Here every
    attribute's default is a `st.Page`, built once when this module is
    imported.

    File paths are relative to `pages/` (hence `../pages/...`).
    `url_path` is the part of the URL after the domain; other code finds
    pages by it (see `from_url_path`), so changing one breaks saved
    links. `st.Page` raises at startup if a file is missing.
    """
    browse_libs: StreamlitPage = Page(
        '../pages/browse_libs.py', url_path='browse_libs',
        title='Browse Libraries', icon="🐐")
    browse_targets: StreamlitPage = Page(
        '../pages/browse_targets.py', url_path='browse_targets',
        title='Browse Targets', icon="🐐")
    browse_substrates: StreamlitPage = Page(
        '../pages/browse_substrates.py', url_path='browse_substrates',
        title='Browse Substrates', icon="🐐")
    browse_patterns: StreamlitPage = Page(
        '../pages/browse_patterns.py', url_path='browse_patterns',
        title="Browse Patterns", icon="🐐")
    browse_recipes: StreamlitPage = Page(
        '../pages/browse_recipes.py', url_path='browse_recipes',
        title="Browse Recipes", icon="🐐")

    new_lib: StreamlitPage = Page(
        '../pages/new_lib.py', url_path='new_library',
        title='Add a New Library', icon="🐐")
    new_target: StreamlitPage = Page(
        '../pages/new_target.py', url_path='new_target',
        title='Add a New Target', icon="🐐")
    new_state: StreamlitPage = Page(
        '../pages/new_deterioration_state.py', url_path='new_state',
        title='Add a New Target Deterioration State', icon="🐐")
    new_substrate: StreamlitPage = Page(
        '../pages/new_substrate.py', url_path='new_substrate',
        title='Add a New Substrate', icon="🐐")
    new_film_modif: StreamlitPage = Page(
        '../pages/new_film_modif.py', url_path='new_film_modif',
        title='Add a New Film Modification', icon="🐐")
    new_lib_file_upload: StreamlitPage = Page(
        '../pages/new_lib_file_upload.py', url_path='new_lib_file_upload',
        title='Add a New File to Library', icon="🐐")
    new_pattern: StreamlitPage = Page(
        '../pages/new_pattern.py', url_path='new_pattern',
        title='New Pattern', icon="🐐")
    new_recipe: StreamlitPage = Page(
        '../pages/new_recipe.py', url_path='new_recipe',
        title='New Recipe', icon="🐐")

    inspect_lib: StreamlitPage = Page(
        '../pages/inspect_library.py', url_path='inspect_lib',
        title='Library', icon="🐐")
    inspect_target: StreamlitPage = Page(
        '../pages/inspect_target.py', url_path='inspect_target',
        title='Target', icon="🐐")
    inspect_substrate: StreamlitPage = Page(
        '../pages/inspect_substrate.py', url_path='inspect_substrate',
        title='Substrate', icon="🐐")

    submission_successful: StreamlitPage = Page(
        '../pages/submission_successful.py', url_path='submission_successful',
        title='Submission Successful', icon="🐐")

    edit_target: StreamlitPage = Page(
        '../pages/edit_target.py', url_path='edit_target',
        title='Edit Target', icon='🐐')
    edit_state: StreamlitPage = Page(
        '../pages/edit_deterioration_state.py', url_path='edit_state',
        title='Edit Deterioration State', icon='🐐')
    edit_lib: StreamlitPage = Page(
        '../pages/edit_lib.py', url_path='edit_lib',
        title='Edit Library', icon='🐐')
    edit_film: StreamlitPage = Page(
        '../pages/edit_film.py', url_path='edit_film',
        title='Edit Film', icon='🐐')
    edit_film_layers: StreamlitPage = Page(
        '../pages/edit_film_layers.py', url_path='edit_film_layers',
        title='Edit Film Layers', icon='🐐')
    edit_substrate: StreamlitPage = Page(
        '../pages/edit_substrate.py', url_path='edit_substrate',
        title='Edit Substrate', icon='🐐')

    admin: StreamlitPage = Page(
        '../pages/admin.py', url_path='admin',
        title='Admin', icon='🐐')
    view_logs: StreamlitPage = Page(
        '../pages/view_logs.py', url_path='view_logs',
        title='Logs', icon='🐐')

    test: StreamlitPage = Page(
        '../pages/test.py', url_path='test',
        title='Test Page', icon="🐐")

    def __iter__(self) -> Iterable[StreamlitPage]:
        """Add 'StreamlitPage' type hint to make it appear in the iteration.

        Lets `for page in pages` and `list(pages)` go through every page.

        Returns:
            An iterator over the pages, in declaration order.
        """
        return iter(asdict(self).values())

    def from_url_path(self, url_path: str) -> StreamlitPage:
        """Finds a page by its `url_path`.

        Used by `switch_page_bttn` when it is given a URL path string.

        Args:
            url_path: The page's `url_path`, e.g. `'inspect_lib'`.

        Returns:
            The matching page.

        Raises:
            RuntimeError: No page has this `url_path`.
        """
        for page in self:
            if page.url_path == url_path:
                return page
        raise RuntimeError(f'Page {url_path} not found.')


# The single instance to import: `from logic.page_list import pages`.
pages = _Pages()


