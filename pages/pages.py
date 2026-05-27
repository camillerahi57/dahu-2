from enum import Enum

from streamlit import Page


class PageEnum(Enum):
    browse_libs = Page(
        'browse_libs.py', url_path='browse_libs',
        title='Browse Libraries', icon="🐐")
    browse_targets = Page(
        'browse_targets.py', url_path='browse_targets',
        title='Browse Targets', icon="🐐")
    browse_substrates = Page(
        'browse_substrates.py', url_path='browse_substrates',
        title='Browse Substrates', icon="🐐")

    new_lib = Page(
        'new_lib.py', url_path='new_library',
        title='Add a New Library', icon="🐐")
    new_target = Page(
        'new_target.py', url_path='new_target',
        title='Add a New Target', icon="🐐")
    new_substrate = Page(
        'new_substrate.py', url_path='new_substrate',
        title='Add a New Substrate', icon="🐐")
    new_charac = Page(
        'new_charac.py', url_path='new_charac',
        title='Add a New Characterization', icon="🐐")

    inspect_lib = Page(
        'inspect_library.py', url_path='inspect_lib',
        title='Library', icon="🐐")
    inspect_target = Page(
        'inspect_target.py', url_path='inspect_target',
        title='Target', icon="🐐")
    inspect_substrate = Page(
        'inspect_substrate.py', url_path='inspect_substrate',
        title='Substrate', icon="🐐")

    library_added = Page(
        'added_library.py', url_path='library_added',
        title='New Library Added', icon="🐐")
    target_added = Page(
        'added_target.py', url_path='target_added',
        title='New Target Added', icon="🐐")
    substrate_added = Page(
        'added_substrate.py', url_path='substrate_added',
        title='New Substrate Added', icon="🐐")

    deleted_lib = Page(
        'deleted_lib.py', url_path='deleted_lib',
        title='Library Deleted', icon="🐐")
    deleted_target = Page(
        'deleted_target.py', url_path='deleted_target',
        title='Target Deleted', icon="🐐")
    deleted_sub = Page(
        'deleted_sub.py', url_path='deleted_sub',
        title='Substrate Deleted', icon="🐐")

    test = Page(
        'test.py', url_path='test',
        title='Test Page', icon="🐐")
