from enum import Enum

from pint import UnitRegistry
from pint.registry import Quantity

ur = UnitRegistry()


class DahuUnit(Enum):
    length = ur.meter

    def from_(self, quantity: Quantity):
        return self.value.from_(quantity)
