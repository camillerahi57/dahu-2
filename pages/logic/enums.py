from enum import StrEnum


class LibraryBrowserColumnName(StrEnum):
    made_on = 'Made on'
    lib_name = 'Name'
    inspect_link = 'Inspect Link'
    characs = 'Charac. Method'
    experimenter = 'Experimenter'
    comment = 'Comment'


class TargetBrowserColumnName(StrEnum):
    made_on = 'Made on'
    made_by = 'Made by'
    target_name = 'Target Name'
    comment = 'Comment'


# class CharacterizationMethod(StrEnum):
#     moke = 'MOKE'
#     edx = 'EDX'
#     profilo = 'Profilo'
#     xray = 'Xray'
