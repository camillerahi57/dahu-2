"""Plain Python classes of the data model that are not database tables.
"""

from dataclasses import dataclass


@dataclass
class MixtureConstituent:
    """One component of a mixture, e.g. one gas of the plasma of an ion
    beam etching.

    A dataclass is a class whose `__init__` is written automatically from
    its annotated attributes. It is built by
    `IonBeamEtching.to_mixture_constituents` from a `PlasmaConstituent`
    row and its formula, and `ConstituentListForm` uses it to prefill the
    constituents of an existing etching.

    Attributes:
        proportion: Share of this constituent in the mixture, as a
            fraction (`PlasmaConstituent.from_stoichio` asserts
            0 < proportion <= 1). No unit.
        stoichio: Chemical formula of the constituent, as written in the
            form (e.g. "Ar").
    """
    proportion: float
    stoichio: str
