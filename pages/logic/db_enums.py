from enum import StrEnum


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
    DC = 'dc'
    RF = 'rf'


class FilmModifType(StrEnum):
    ANNEALING = 'annealing'
    WET_ETCHING = 'wet_etching'
    ION_BEAM_ETCHING = 'ion_etching'
    PATTERNING = 'patterned'


class PixelCoordinateSystem(StrEnum):
    X_Y_EQ_W_H_ORIGIN_TOP_LEFT = "x,y=width,height;origin-top-left"


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
    K = 'k'
    L = 'l'
    M = 'm'


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