from enum import StrEnum


class LibraryBrowserColumnName(StrEnum):
    made_on = 'Made on'
    lib_name = 'Name'
    inspect_link = 'Inspect Link'
    # characs = 'Charac. Methods'
    experimenter = 'Experimenter'
    comment = 'Comment'
    target = 'Target'
    # TODO Download button


class TargetBrowserColumnName(StrEnum):
    made_on = 'Made on'
    made_by = 'Made by'
    physical_name = 'Physical Name'
    comment = 'Comment'
    inspect_link = 'Link'


class SubstrateBrowserColumnName(StrEnum):
    name = 'Name'
    comment = 'Comment'
    inspect_link = 'Link'


class LibInspectColumnName(StrEnum):
    stoichio = 'Stoichio.'
    thickness = 'Thickness'
    deposit_temp = 'Deposit Temp.'
    deposit_duration = 'Duration'
    deposit_power = 'Power'
