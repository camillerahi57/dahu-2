"""Conversions between the units shown in the UI and those of the DB.

The database stores every physical quantity in SI base units (meter,
second, kilogram, kelvin, ampere, radian...). The forms show other units
(mm, minutes, degrees Celsius...). This module holds the Pint objects
and the functions that convert from one to the other. Pint is the
library that attaches units to numbers: a `Quantity` is a number with a
unit, a `Unit` is a unit alone.

Most code does not call these functions directly: the form field classes
do it (see `UnitField` in `components.forms.base_classes`).
"""
from dataclasses import dataclass

from pint import UnitRegistry
from pint.facets.plain import PlainUnit
from pint.registry import Unit, Quantity

from logic.constants import DB_UNIT_SYSTEM

# The registry is Pint's catalogue of units. Use this one everywhere:
# quantities made with different registries cannot be combined.
ur = UnitRegistry(system=DB_UNIT_SYSTEM)
ur.default_format = 'P'  # Or '~P' for short version.
# Default value of `AppMetadata.db_units_description`: it is stored in the
# DB so that whoever reads the DB file alone knows which units it holds.
db_units_explanation = """All units in DB are SI. All quantities are converted 
to SI using Pint's `to_base_units` method, with 
`ur = UnitRegistry(system='SI')`."""


def to_db_unit(*, unit: Unit)\
        -> Unit|float|PlainUnit:  # TODO remove float.
    """Gives the database unit that goes with a unit.

    For example `ur.mm` gives meter and `ur.cm**3 / ur.min` gives
    cubic meter per second. The result tells the dimension (length,
    time...) of `unit` through its DB unit.

    Args:
        unit: Any unit (not a quantity).

    Returns:
        The unit, in the form of SI base units.
    """
    ui_unity: Quantity = 1 * unit  # noqa, wrong warning.
    db_unity = ui_unity.to_base_units()
    return db_unity.units


def to_db_magnitude(quantity: Quantity) -> float:
    """Converts a quantity to its number in the database unit.

    This is how a value typed in a form (in the UI unit) becomes what is
    stored. Offset units are handled: 20 degrees Celsius gives 293.15
    (kelvin).

    Args:
        quantity: A number with its unit, in any unit.

    Returns:
        The number to store, in SI base units.
    """
    return quantity.to_base_units().magnitude


def from_db_unit(db_value: float|None, target_unit: Unit) -> Quantity|None:
    """Converts a value from the database into another unit.

    This is how a stored value is turned into what the forms show. Use
    `.magnitude` on the result to get the plain number.

    Args:
        db_value: Value as stored, in the database unit of
            `target_unit` (see `to_db_unit`), or None.
        target_unit: The unit wanted, usually the `ui_unit` of a field.

    Returns:
        The value as a quantity in `target_unit`, or None if `db_value`
        is None.
    """
    if db_value is None:
        return None
    db_unit = (1 * target_unit).to_base_units().units  # noqa, wrong warning.
    db_quantity = db_value * db_unit
    return db_quantity.to(target_unit)


@dataclass
class _DatabaseUnits:
    """Here we always put an arbitrary unit of the right dimension to get
    the database unit for that specific dimension.

    A dataclass is a class meant to hold values; there is a single
    instance, `db_units`. Use it to say "this number is in the DB unit of
    a length" without repeating `ur.meter`, for example
    `ur.Quantity(value, db_units.length)`.

    Attributes:
        length: Unit of a length (meter).
        time: Unit of a duration or timestamp (second).
        pressure: Unit of a pressure (pascal).
        temperature: Unit of a temperature (kelvin).
        current: Unit of an electric current (ampere).
        voltage: Unit of a voltage (volt, written in SI base units:
            kg m^2 A^-1 s^-3).
        flow: Unit of a volumetric flow (cubic meter per second).
        angle: Unit of an angle (radian).
        rot_speed: Unit of a rotation speed (radian per second).
    """
    length = to_db_unit(unit=ur.meter)
    time = to_db_unit(unit=ur.second)
    pressure = to_db_unit(unit=ur.Pa)
    temperature = to_db_unit(unit=ur.K)
    current = to_db_unit(unit=ur.A)
    voltage = to_db_unit(unit=ur.V)
    flow = to_db_unit(unit=ur.m**3 / ur.s)
    angle = to_db_unit(unit=ur.rad)
    rot_speed = to_db_unit(unit=ur.rad / ur.s)

# The single instance of `_DatabaseUnits`, imported by `db_models`.
db_units = _DatabaseUnits()
