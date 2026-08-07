from enum import StrEnum

from components.forms.new_library.fields import DepositTempField, \
    NominalThicknessField, DepositPowerField, DepositDurationField
from components.forms.new_substrate.fields import ThicknessField


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
    nominal_stoichio = 'Nominal stoichio.'
    thickness = f'Thickness ({NominalThicknessField.ui_unit})'
    deposit_temp = f'Deposit Temp. ({DepositTempField.ui_unit})'
    deposit_duration = f'Duration ({DepositDurationField.ui_unit})'
    deposit_power = f'Power ({DepositPowerField.ui_unit})'
