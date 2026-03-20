from enum import StrEnum
from pathlib import Path
from typing import Self


LIB_ID_URL_KEY = 'lib_id'
DOMAIN = 'localhost:8501'
PAGE_NAME_KEY = 'page_name_key'
PATCH_FORMS_KEY = 'patch_forms_key'
TARGET_FORM_STAGING_KEY = 'target_form_save_key'  # Where we store the list of object
# that will be saved when the new target form is submitted.
FILE_STORAGE_PATH = Path(r"C:\Users\Camille.RAHI\Documents\Documents\Code\dahu-2-storage")


class ShapeType(StrEnum):
    POLYGON = 'polygon'
    DISC = 'disc'


class StorageKeys(StrEnum):
    """Keys are hard coded random strings, so that if we rename the variable for an
    update, we'll still access the value from old version with the same key."""

    LAST_EMAIL_USED = '4f89qv6sdw531xcs6qqf4c5q6d8zs4cD'
    LIB_FILTERS = 'f4ze86sd4c+e1v68rrf46sdw1cqz568fc4'
    TARGET_FILTERS = 'd48qz6f4cdsv1r3e54g68e6rq4<3q1dz'

    # Put last used email here and implement it.
    # Also, is deletion cascading?


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