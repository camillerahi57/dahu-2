from dataclasses import dataclass

from pint import UnitRegistry

ur = UnitRegistry()


@dataclass
class _DahuUnit:
    length = ur.meter

dahu_unit = _DahuUnit()
