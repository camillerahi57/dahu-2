"""Column titles of the tables shown on the browsing and inspection pages.

Each class lists the columns of one table. The enum values are the titles
displayed in the web page; the pages also use the enum members as the
column keys of their `pandas` DataFrames and Streamlit column configs, so
a title is changed here only.

An enum (`StrEnum`) is a fixed list of named constants whose values are
strings.

Importing this module imports the library form fields, because some
titles contain the unit that the form uses (see `UnitField.ui_unit`).
"""

from enum import StrEnum

from components.forms.new_library.fields import DepositTempField, \
    NominalThicknessField, DepositPowerField, DepositDurationField


class LibraryBrowserColumnName(StrEnum):
    """Columns of the library table on the home page
    (`pages/browse_libs.py`)."""
    made_on = 'Made on'
    lib_name = 'Label'
    inspect_link = 'Inspect Link'  # Button opening the library page.
    experimenter = 'Experimenter'
    comment = 'Comment'
    target = 'Target'
    is_archived = 'Is Archived'


class TargetBrowserColumnName(StrEnum):
    """Columns of the target table (`pages/browse_targets.py`)."""
    made_on = 'Made on'
    made_by = 'Made by'
    label = 'Label'
    is_archived = 'Is Archived'
    inspect_link = 'Link'  # Button opening the target page.


class SubstrateBrowserColumnName(StrEnum):
    """Columns of the substrate table (`pages/browse_substrates.py`)."""
    label = 'Label'
    comment = 'Comment'
    inspect_link = 'Link'  # Button opening the substrate page.


class LibInspectColumnName(StrEnum):
    """Columns of the film layer table of the library page
    (`pages/inspect_library.py`).

    Titles of physical quantities end with the unit shown in the table,
    taken from the `ui_unit` of the form field used to enter the value.
    The `:~P` format asks Pint for the short, pretty form of the unit
    (e.g. "nm").
    """
    nominal_stoichio = 'Nominal stoichio.'
    details = 'Details'
    function = 'Function'
    thickness = f'Thickness ({NominalThicknessField.ui_unit:~P})'
    deposit_temp = f'Deposit Temp. ({DepositTempField.ui_unit:~P})'
    deposit_duration = f'Duration ({DepositDurationField.ui_unit:~P})'
    deposit_power = f'Power ({DepositPowerField.ui_unit:~P})'
