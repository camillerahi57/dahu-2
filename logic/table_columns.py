from enum import StrEnum

from components.forms.new_library.fields import DepositTempField, \
    NominalThicknessField, DepositPowerField, DepositDurationField


class LibraryBrowserColumnName(StrEnum):
    made_on = 'Made on'
    lib_name = 'Label'
    inspect_link = 'Inspect Link'
    experimenter = 'Experimenter'
    comment = 'Comment'
    target = 'Target'
    is_archived = 'Is Archived'


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
    nominal_stoichio = 'Nominal stoichio.'
    details = 'Details'
    function = 'Function'
    thickness = f'Thickness ({NominalThicknessField.ui_unit:~P})'
    deposit_temp = f'Deposit Temp. ({DepositTempField.ui_unit:~P})'
    deposit_duration = f'Duration ({DepositDurationField.ui_unit:~P})'
    deposit_power = f'Power ({DepositPowerField.ui_unit:~P})'
