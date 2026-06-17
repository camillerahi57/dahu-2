from dataclasses import dataclass

from pint import UnitRegistry
from pint.registry import Unit, Quantity

from logic.constants import DB_UNIT_SYSTEM

ur = UnitRegistry(system=DB_UNIT_SYSTEM)


@dataclass
class _DatabaseUnits:
    length = ur.m
    rot_speed = ur.rad / ur.s
    voltage = ur.V
    current = ur.A
    angle = ur.rad
    deposit_rate = ur.m / ur.s
    flow = ur.m**3 / ur.s
    pressure = ur.Pa


def to_db_unit(quantity: Quantity = None, unit: Unit = None) -> Unit|float:
    assert quantity is not None or unit is not None
    assert quantity is None or unit is None
    if quantity is not None:  # If we want to convert a number.
        return quantity.to_base_units().magnitude
    else:  # If we want to convert a unit.
        ui_unity: Quantity = 1 * ui_unit  # noqa, wrong warning.
        db_unity = ui_unity.to_base_units()
        return db_unity.units


def from_db_unit(value: float, target_unit: Unit) -> float:
    db_unit = (1 * target_unit).to_base_units().units  # noqa, wrong warning.
    quantity = value * db_unit
    return quantity.to(target_unit).magnitude


# @dataclass
# class _UserInterfaceUnits:
#     length = ur.m
#     rot_speed = ur.rad / ur.s
#     voltage = ur.V
#     current = ur.A
#     angle = ur.rad
#     deposit_rate = ur.m / ur.s
#     flow = ur.m**3 / ur.s
#     pressure = ur.Pa

database_units = _DatabaseUnits()
