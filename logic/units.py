from dataclasses import dataclass

from pint import UnitRegistry
from pint.registry import Unit, Quantity

from logic.constants import DB_UNIT_SYSTEM

ur = UnitRegistry(system=DB_UNIT_SYSTEM)
ur.default_format = 'P'  # Or '~P' for short version.


def to_db_unit(quantity: Quantity = None, unit: Unit = None) -> Unit|float:
    """Convert either a quantity or a unit to the equivalent database unit."""
    assert quantity is not None or unit is not None
    assert quantity is None or unit is None
    if quantity is not None:  # If we want to convert a number.
        return quantity.to_base_units().magnitude
    else:  # If we want to convert a unit.
        ui_unity: Quantity = 1 * unit  # noqa, wrong warning.
        db_unity = ui_unity.to_base_units()
        return db_unity.units


def from_db_unit(db_value: float|None, target_unit: Unit) -> Quantity|None:
    """Returns a float that is the value from the database unit to the target
    unit."""
    if db_value is None:
        return None
    db_unit = (1 * target_unit).to_base_units().units  # noqa, wrong warning.
    db_quantity = db_value * db_unit
    return db_quantity.to(target_unit)


@dataclass
class _DatabaseUnits:
    """Here we always put an arbitrary unit of the right dimension to get
    the database unit for that specific dimension."""
    length = to_db_unit(unit=ur.meter)
    time = to_db_unit(unit=ur.second)
    pressure = to_db_unit(unit=ur.Pa)
    temperature = to_db_unit(unit=ur.K)
    current = to_db_unit(unit=ur.A)
    voltage = to_db_unit(unit=ur.V)
    flow = to_db_unit(unit=ur.m**3 / ur.s)
    angle = to_db_unit(unit=ur.rad)
    rot_speed = to_db_unit(unit=ur.rad / ur.s)

# TODO Stop using this.
db_units = _DatabaseUnits()