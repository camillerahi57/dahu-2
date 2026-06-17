from enum import StrEnum


class LibraryBrowserColumnName(StrEnum):
    made_on = 'Made on'
    lib_name = 'Label'
    inspect_link = 'Inspect Link'
    # characs = 'Charac. Methods'
    experimenter = 'Experimenter'
    comment = 'Comment'
    target = 'Target'
    # TODO Download button


class TargetBrowserColumnName(StrEnum):
    made_on = 'Made on'
    made_by = 'Made by'
    label = 'Label'
    # comment = 'Comment'
    inspect_link = 'Link'


class SubstrateBrowserColumnName(StrEnum):
    label = 'Label'
    comment = 'Comment'
    inspect_link = 'Link'


class LibInspectColumnName(StrEnum):
    stoichio = 'Stoichio.'
    thickness = 'Thickness'
    deposit_temp = 'Deposit Temp.'
    deposit_duration = 'Duration'
    deposit_power = 'Power'
