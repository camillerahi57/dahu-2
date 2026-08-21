from dataclasses import dataclass, asdict

from streamlit import Page
from streamlit.navigation.page import StreamlitPage


@dataclass
class _Pages:
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

    restore_app_state: StreamlitPage = Page(
        '../pages/restore_app_state.py', url_path='restore_app_state',
        title='Restore App State', icon='🐐')

    test: StreamlitPage = Page(
        '../pages/test.py', url_path='test',
        title='Test Page', icon="🐐")

    def to_list(self) -> list[StreamlitPage]:
        """Add 'StreamlitPage' type hint to make it appear in the list."""
        return list(asdict(self).values())

    def from_url_path(self, url_path: str) -> StreamlitPage:
        for page in self.to_list():
            if page.url_path == url_path:
                return page
        raise RuntimeError(f'Page {url_path} not found.')


pages = _Pages()