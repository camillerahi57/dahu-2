from dataclasses import dataclass


@dataclass
class MixtureConstituent:
    proportion: float
    stoichio: str