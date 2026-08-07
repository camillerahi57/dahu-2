# from dataclasses import dataclass
# from math import pi, cos, sin
#
# import plotly.graph_objects as go
# from plotly.graph_objs import Scatter
#
# from logic.functions import polygon_patch_to_scatter
from dataclasses import dataclass


# @dataclass
# class PolygonPatchData:
#     stoichio: str
#     vertices: list[tuple[float, float]]
#
#     def to_scatter(self):
#         color = Patch.plotly_color(stoichio)
#         return polygon_patch_to_scatter(ordered_vertices, color_=color,
#                                         name_=stoichio)


# @dataclass
# class PatchListData:
#     disc_patches: list[DiscPatchData]
#     polygon_patches: list[PolygonPatchData]
#
#     def to_figure(self):
#         from logic.lab_modelization.db_models import PatchModel
#
#         fig = go.Figure(
#             [Scatter()],
#             layout=go.Layout(
#                 xaxis={'showgrid': True, 'side': 'top'},
#                 yaxis={'scaleanchor': 'x', 'autorange': 'reversed'},
#             ),
#         )
#
#         for disc in self.disc_patches:
#             poly = disc.to_polygon_approx_data()
#             scatter = poly.to_scatter()
#             fig.add_trace(scatter)
#
#         for poly in self.polygon_patches:
#             scatter = PatchModel.data_to_scatter(
#                 poly.stoichio, poly.vertices)
#             fig.add_trace(scatter)
#
#         return fig


@dataclass
class MixtureConstituent:
    proportion: float
    stoichio: str