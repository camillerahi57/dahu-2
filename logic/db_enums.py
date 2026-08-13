from enum import StrEnum
from typing import Self





###################################################################
############################# WARNING #############################
###################################################################
# Modifying or deleting string values can cause DB mismatch. For example,
# if you rename 'polygon' to 'Polygon', all [shape_in_db ==
# ShapeType.POLYGON] comparisons will fail because it's comparing 'polygon'
# to 'Polygon'. That's why, if you rename an enum value (key/variable name
# change is ok), you must rename it everywhere in the DB (with a Python
# script). However, you can add new values without any problem.


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
    TUBE = 'Tube furnace'
    RTA = 'Rapid Thermal Annealing'


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
    COIL_2 = 'coil_2'


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


# Usage order: base -> acid -> solvent
# Available products: https://nanofab.neel.cnrs.fr/mg-chimie-liste-des-produits/
class EtchingBaseSuggestion(StrEnum):
    AMMONIA = "Ammonia"
    AR_300_44 = "AR 300-44"
    AR_300_46 = "AR 300-46"
    AR_300_47 = "AR 300-47"
    AZ_351_B = "AZ 351 B"
    AZ_400_K = "AZ 400 K"
    AZ_Developer = "AZ Developer"
    POTASSIUM_HYDROXIDE = "Potassium Hydroxide"
    KC_265 = "KC 265"
    KOH = "KOH"
    MA_D_533_S = "ma-D 533 S"
    MF_26_A = "MF 26 A"
    MF_319 = "MF 319"
    MICROPOSIT_CONCENTRATED_DEVELOPER = "Microposit Concentrated Developer"
    MR_D_526_S = "mr-D 526 S"
    MR_REM_700 = "mr-Rem 700"
    TECHNISTRIP_NF52 = "Technistrip NF52"
    TMAH = "TMAH"


class EtchingAcidSuggestion(StrEnum):
    ACETIC_ACID_CH3COOH_100 = "100% Acetic Acid (CH3COOH)"
    HYDROCHLORIC_ACID_HCL_36 = "36% Hydrochloric Acid (HCl)"
    CITRIC_ACID_MONOHYDRATE_C6H8O7 = "Citric Acid Monohydrate (C6H8O7)"
    ORTHOPHOSPHORIC_ACID_H3PO4 = "Orthophosphoric Acid (H3PO4)"
    HYDROFLUORIC_ACID_HF = "Hydrofluoric Acid (HF)"
    NITRIC_ACID_65_HNO3 = "Nitric Acid 65% (HNO3)"
    PERCHLORIC_ACID_HCLO4 = "Perchloric Acid (HClO4)"
    PHOSPHORIC_ACID_85 = "Phosphoric Acid (85%)"
    SULFURIC_ACID_95_H2SO4 = "Sulfuric Acid (95%) (H2SO4)"
    ALUMINUM_ETCH_TYPE_A = "Aluminum Etch Type A"
    ALUMINUM_ETCH_TYPE_B = "Aluminum Etch Type B"
    ALUMINUM_ETCH_TYPE_D = "Aluminum Etch Type D"
    AMMONIA_NH3 = "Ammonia (NH3)"
    OXIDE_ETCHING_BUFFER_NH4F_HF_7_1 = "Oxide Etching Buffer (NH4F/HF) 7:1"
    OXIDE_ETCHING_BUFFER_NH4F_HF_10_1 = "Oxide Etching Buffer (NH4F/HF) 10:1"
    CHROME_ETCH_18 = "Chrome Etch 18"
    FECL3 = "FeCl3"
    AMMONIUM_FLUORIDE_NH4F = "Ammonium Fluoride (NH4F)"
    GOLD_ETCH_TYPE_TFA = "Gold Etch Type TFA"
    KI_I2 = "KI + I2"
    NICKEL_ETCH_TFB = "Nickel Etch TFB"
    NICKEL_ETCH_TFG = "Nickel Etch TFG"
    HYDROGEN_PEROXIDE_30_H2O2 = "Hydrogen Peroxide 30% (H2O2)"
    SILOX_VAPOX_ETCHANT_III = "Silox Vapox Etchant III"
    AMMONIUM_SULFIDE_NH4_2S = "Ammonium Sulfide ((NH4)2S)"
    TANTALUM_NITRIDE_ETCH_1_1_1 = "Tantalum Nitride Etch  1-1-1"
    TANTALUM_NITRIDE_ETCH_SIE_8607 = "Tantalum Nitride Etch SIE-8607"


class EtchingSolventSuggestion(StrEnum):
    ETHANOL = "Ethanol"
    ACETONE = "Acetone"
    ISOPROPYL_ALCOHOL_IPA = "Isopropyl alcohol (IPA)"
    N_METHYL_2_PYRROLIDONE_NMP_REMOVER1165 = ("N-Methyl-2-pyrrolidone (NMP) = "
                                              "Remover1165")
    REMOVER_PG = "Remover PG"
    ETHYL_LACTATE_AR_600_09 = "Ethyl lactate (AR 600-09...)"
    METHYL_ISOBUTYL_KETONE_MIBK = "Methyl isobutyl ketone (MIBK)"
    QSR_5_D2 = "QSR-5 D2"
    SU8_DEVELOPER = "SU8 developer"
    SU8_2000_THINNER = "SU8 2000 Thinner"
    AR_300_70 = "AR 300-70"
    MR_REM_660 = "mr-Rem 660"
    CYCLOHEXANE = "Cyclohexane"


class XrayType(StrEnum):
    SMART_LAB = 'smart_lab'
    ESRF = 'esrf'


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
