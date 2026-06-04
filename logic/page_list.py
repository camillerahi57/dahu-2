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
    new_charac: StreamlitPage = Page(
        '../pages/new_charac.py', url_path='new_charac',
        title='Add a New Characterization', icon="🐐")

    inspect_lib: StreamlitPage = Page(
        '../pages/inspect_library.py', url_path='inspect_lib',
        title='Library', icon="🐐")
    inspect_target: StreamlitPage = Page(
        '../pages/inspect_target.py', url_path='inspect_target',
        title='Target', icon="🐐")
    inspect_substrate: StreamlitPage = Page(
        '../pages/inspect_substrate.py', url_path='inspect_substrate',
        title='Substrate', icon="🐐")

    library_added: StreamlitPage = Page(
        '../pages/added_library.py', url_path='library_added',
        title='New Library Added', icon="🐐")
    target_added: StreamlitPage = Page(
        '../pages/added_target.py', url_path='target_added',
        title='New Target Added', icon="🐐")
    substrate_added: StreamlitPage = Page(
        '../pages/added_substrate.py', url_path='substrate_added',
        title='New Substrate Added', icon="🐐")
    submission_successful: StreamlitPage = Page(
        '../pages/submission_successful.py', url_path='submission_successful',
        title='Submission Successful', icon="🐐")

    deleted_lib: StreamlitPage = Page(
        '../pages/deleted_lib.py', url_path='deleted_lib',
        title='Library Deleted', icon="🐐")
    deleted_target: StreamlitPage = Page(
        '../pages/deleted_target.py', url_path='deleted_target',
        title='Target Deleted', icon="🐐")
    deleted_sub: StreamlitPage = Page(
        '../pages/deleted_sub.py', url_path='deleted_sub',
        title='Substrate Deleted', icon="🐐")
    deleted_state: StreamlitPage = Page(
        '../pages/deleted_deterioration_state.py', url_path='deleted_state',
        title='Deterioration State Deleted', icon="🐐")

    edit_target: StreamlitPage = Page(
        '../pages/edit_target.py', url_path='edit_target',
        title='Edit Target', icon='🐐')

    edit_state: StreamlitPage = Page(
        '../pages/edit_deterioration_state.py', url_path='edit_state',
        title='Edit Deterioration State', icon='🐐')

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