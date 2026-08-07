from enum import StrEnum
from typing import Self


# BE CAREFUL:
#
# Modifying string values can cause DB mismatch. For example, if you rename
# 'polygon' to 'Polygon', all [shape_type == 'polygon'] comparisons,
# where shape_type is ShapeType.POLYGON (which is now 'Polygon'), could fail
# because of this change. That's why, if you rename an enum value (key is
# ok), you must rename it everywhere in the DB

class ShapeType(StrEnum):
    POLYGON = 'polygon'
    DISC = 'disc'


class SputteringSystem(StrEnum):
    TRIODE = 'triode'
    MAGNETRON = 'magnetron'


class FilmLayerFunction(StrEnum):
    BUFFER = 'buffer'
    ACTIVE = 'active'
    CAPPING = 'capping'


class MagnetronSputteringGenerator(StrEnum):
    RF_1 = 'RF-1'
    RF_2 = 'RF-2'
    RF_3 = 'RF-3'
    RF_4 = 'RF-4'
    DC_1 = 'DC-1'
    DC_2 = 'DC-2'
    DC_3 = 'DC-3'
    DC_4 = 'DC-4'
    DC_5 = 'DC-5'
    DC_6 = 'DC-6'
    DC_7 = 'DC-7'
    DC_8 = 'DC-8'


class FilmModifType(StrEnum):
    LIFT_OFF = 'lift_off'
    ANNEALING = 'annealing'
    WET_ETCHING = 'wet_etching'
    ION_BEAM_ETCHING = 'ion_etching'


etching_types = {FilmModifType.LIFT_OFF, FilmModifType.WET_ETCHING,
                 FilmModifType.ION_BEAM_ETCHING}


class PixelCoordinateSystem(StrEnum):
    PLOTLY = "x,y=w,h;both-positive;top-left-origin"


class Furnace(StrEnum):
    FURNACE_1 = 'furnace_1'
    FURNACE_2 = 'furnace_2'  # TODO Replace names.


class CharacType(StrEnum):
    MOKE = 'moke'
    PROFILO = 'profilo'
    VSM_SQUID = 'vsm_squid'
    EDX = 'edx'
    XRAY = 'xray'
    IMAGING = 'imaging'


class MokeMachine(StrEnum):
    S_MOKE = 's_moke'
    NEW_MOKE = 'new_moke'


class CoilModel(StrEnum):
    COIL_1 = 'coil_1'
    COIL_2 = 'coil_2'  # TODO Replace names.


class XLine(StrEnum):
    K = 'K'
    L = 'L'
    M = 'M'


class SweepType(StrEnum):
    FIELD_SWEEP = 'field_sweep'
    TEMPERATURE_SWEEP = 'temperature_sweep'


class SampleHolderType(StrEnum):
    QUARTZ = 'quartz'
    STRAW = 'straw'
    PLEXI = 'plexi'


class VsmSquidOrientation(StrEnum):
    IN_PLANE = 'in_plane'
    OUT_OF_PLANE = 'out_of_plane'


class XrayType(StrEnum):
    SMART_LAB = 'smart_lab'
    ESRF = 'esrf'


class EtchingDevelopers(StrEnum):
    pass
    # TODO Bases from https://nanofab.neel.cnrs.fr/mg-chimie-liste-des-produits/


class StoichioOf(StrEnum):
    SUBSTRATE_LAYER = 'substrate_layer'
    PATCH = 'patch'
    NOMINAL_FILM_LAYER = 'nominal_film_layer'
    ANNEALING_ATMOSPHERE = 'annealing_atmosphere'
    ACID_CONSTITUENT = 'acid_constituent'


class MagnetronMachineModel(StrEnum):
    DP850 = 'Allianceconcept_DP850'


class ChemicalElement(StrEnum):
    ASTATINE = 'At'
    FRANCIUM = 'Fr'
    FERMIUM = 'Fm'
    MENDELEVIUM = 'Md'
    NOBELIUM = 'No'
    LAWRENCIUM = 'Lr'
    RUTHERFORDIUM = 'Rf'
    DUBNIUM = 'Db'
    SEABORGIUM = 'Sg'
    BOHRIUM = 'Bh'
    HASSIUM = 'Hs'
    MEITNERIUM = 'Mt'
    DARMSTADTIUM = 'Ds'
    ROENTGENIUM = 'Rg'
    COPERNICIUM = 'Cn'
    NIHONIUM = 'Nh'
    FLEROVIUM = 'Fl'
    MOSCOVIUM = 'Mc'
    LIVERMORIUM = 'Lv'
    TENNESSINE = 'Ts'
    OGANESSON = 'Og'
    LITHIUM = 'Li'
    BERYLLIUM = 'Be'
    BORON = 'B'
    CARBON = 'C'
    SODIUM = 'Na'
    MAGNESIUM = 'Mg'
    ALUMINIUM = 'Al'
    SILICON = 'Si'
    PHOSPHORUS = 'P'
    SULFUR = 'S'
    POTASSIUM = 'K'
    CALCIUM = 'Ca'
    SCANDIUM = 'Sc'
    TITANIUM = 'Ti'
    VANADIUM = 'V'
    CHROMIUM = 'Cr'
    MANGANESE = 'Mn'
    IRON = 'Fe'
    COBALT = 'Co'
    NICKEL = 'Ni'
    COPPER = 'Cu'
    ZINC = 'Zn'
    GALLIUM = 'Ga'
    GERMANIUM = 'Ge'
    ARSENIC = 'As'
    SELENIUM = 'Se'
    RUBIDIUM = 'Rb'
    STRONTIUM = 'Sr'
    YTTRIUM = 'Y'
    ZIRCONIUM = 'Zr'
    NIOBIUM = 'Nb'
    MOLYBDENUM = 'Mo'
    TECHNETIUM = 'Tc'
    RUTHENIUM = 'Ru'
    RHODIUM = 'Rh'
    PALLADIUM = 'Pd'
    SILVER = 'Ag'
    CADMIUM = 'Cd'
    INDIUM = 'In'
    TIN = 'Sn'
    ANTIMONY = 'Sb'
    TELLURIUM = 'Te'
    IODINE = 'I'
    CAESIUM = 'Cs'
    BARIUM = 'Ba'
    LANTHANUM = 'La'
    CERIUM = 'Ce'
    PRASEODYMIUM = 'Pr'
    NEODYMIUM = 'Nd'
    PROMETHIUM = 'Pm'
    SAMARIUM = 'Sm'
    EUROPIUM = 'Eu'
    GADOLINIUM = 'Gd'
    TERBIUM = 'Tb'
    DYSPROSIUM = 'Dy'
    HOLMIUM = 'Ho'
    ERBIUM = 'Er'
    THULIUM = 'Tm'
    YTTERBIUM = 'Yb'
    LUTETIUM = 'Lu'
    HAFNIUM = 'Hf'
    TANTALUM = 'Ta'
    TUNGSTEN = 'W'
    RHENIUM = 'Re'
    OSMIUM = 'Os'
    IRIDIUM = 'Ir'
    PLATINUM = 'Pt'
    GOLD = 'Au'
    THALLIUM = 'Tl'
    LEAD = 'Pb'
    BISMUTH = 'Bi'
    POLONIUM = 'Po'
    RADIUM = 'Ra'
    ACTINIUM = 'Ac'
    THORIUM = 'Th'
    PROTACTINIUM = 'Pa'
    URANIUM = 'U'
    NEPTUNIUM = 'Np'
    PLUTONIUM = 'Pu'
    AMERICIUM = 'Am'
    CURIUM = 'Cm'
    BERKELIUM = 'Bk'
    CALIFORNIUM = 'Cf'
    EINSTEINIUM = 'Es'
    BROMINE = 'Br'
    MERCURY = 'Hg'
    HYDROGEN = 'H'
    HELIUM = 'He'
    NITROGEN = 'N'
    OXYGEN = 'O'
    FLUORINE = 'F'
    NEON = 'Ne'
    CHLORINE = 'Cl'
    ARGON = 'Ar'
    KRYPTON = 'Kr'
    XENON = 'Xe'
    RADON = 'Rn'

    @classmethod
    def from_short(cls, short: str) -> Self:
        return short_to_enum_elements[short]

    @staticmethod
    def all_short_str():
        return short_to_enum_elements.keys()


short_to_enum_elements = {
    element.value: element
    for element in ChemicalElement
}
