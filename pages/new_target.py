import plotly.graph_objects as go
import streamlit as st
from plotly.graph_objs import Scatter

from logic.constants import PATCH_FORMS_KEY, TARGET_FORM_STAGING_KEY
from logic.db_schema import Disc, Polygon, Vertex, Stoichiometry
from logic.forms.new_target import MadeAtField, ExperimenterEmailField, TargetNameField, CommentField, \
    StoichiometryField, DiscCenterX, DiscCenterY, RadiusField, RectangleFirstVertexX, RectangleFirstVertexY, \
    RectangleOppositeVertexX, RectangleOppositeVertexY
from logic.functions import save_session_state, load_session_state

sess = load_session_state('new_target.py')

if TARGET_FORM_STAGING_KEY not in sess:
    sess[TARGET_FORM_STAGING_KEY] = []

made_at = MadeAtField.input()
email_fld = ExperimenterEmailField.input()
target_name = TargetNameField.input()
comment = CommentField.input()

col1, col2 = st.columns([100, 90])


class DiscForm:
    @st.dialog("New Disc")
    def __init__(self):
        sess_ = st.session_state
        stoichio_fld = StoichiometryField.input()
        col1_, col2_, col3_ = st.columns(3)
        with col1_:
            x_pos_fld = DiscCenterX.input()
        with col2_:
            y_pos_fld = DiscCenterY.input()
        with col3_:
            radius_fld = RadiusField.input()

        fields = [stoichio_fld, x_pos_fld, y_pos_fld, radius_fld]
        all_fields_valid = all([fld.is_valid for fld in fields])

        if st.button("Add Disc", disabled=not all_fields_valid):
            for fld in fields:
                fld.remove_from_session()  # To have a new one in the next pop-up.
            self.stoichio = stoichio_fld.value
            self.x_pos = x_pos_fld.value
            self.y_pos = y_pos_fld.value
            self.radius = radius_fld.value
            sess_[PATCH_FORMS_KEY].append(self)
            st.rerun()

    def to_disc(self) -> Disc:
        return Disc.new(self.x_pos, self.y_pos, self.radius)

    def to_scatter(self, color_: str, name_: str):
        return self.to_disc().to_scatter(color_, name_)


class AlignedRectangleForm:
    @st.dialog("New Aligned Rectangle")
    def __init__(self):
        sess_ = st.session_state
        stoichio_fld = StoichiometryField.input()
        col1_, col2_ = st.columns(2)
        with col1_:
            vertex_1_x_fld = RectangleFirstVertexX.input()
        with col2_:
            vertex_1_y_fld = RectangleFirstVertexY.input()
        with col1_:
            vertex_2_x_fld = RectangleOppositeVertexX.input()
        with col2_:
            vertex_2_y_fld = RectangleOppositeVertexY.input()

        fields = [stoichio_fld, vertex_1_x_fld, vertex_1_y_fld, vertex_2_x_fld, vertex_2_y_fld]
        all_fields_valid = all([fld.is_valid for fld in fields])

        if st.button("Add Aligned Rectangle", disabled=not all_fields_valid):
            for fld in fields:
                fld.remove_from_session()
            self.stoichio = stoichio_fld.value
            self.vertex_1_x = vertex_1_x_fld.value
            self.vertex_1_y = vertex_1_y_fld.value
            self.vertex_2_x = vertex_2_x_fld.value
            self.vertex_2_y = vertex_2_y_fld.value
            sess_[PATCH_FORMS_KEY].append(self)
            st.rerun()

    def vertices(self) -> list[tuple[float, float]]:
        return [
            (self.vertex_1_x, self.vertex_1_y),
            (self.vertex_1_x, self.vertex_2_y),
            (self.vertex_2_x, self.vertex_2_y),
            (self.vertex_2_x, self.vertex_1_y),
        ]

    def to_polygon(self) -> tuple[Polygon, list[Vertex]]:
        return Polygon.from_aligned_rectangle_data(
            first_vertex=(self.vertex_1_x, self.vertex_1_y),
            opposite_vertex=(self.vertex_2_x, self.vertex_2_y),
        )

    def to_scatter(self, color_: str, name_: str):
        vertices = self.vertices()
        # Closing the rectangle:
        vertices.append(vertices[0])
        x_coords, y_coords = zip(*vertices)
        return Scatter(
            x=x_coords, y=y_coords,
            mode='lines',
            fill='toself',
            fillcolor=color_,
            opacity=1,
            line=dict(width=2, color='black'),
            showlegend=False,
            name=name_,
        )


with col1:
    st.title('Patches')
    if PATCH_FORMS_KEY not in sess:
        sess[PATCH_FORMS_KEY] = []

    for i, form in enumerate(sess[PATCH_FORMS_KEY]):
        col11, col12 = st.columns([85, 15])
        with col11:
            rectangle = Stoichiometry.from_str(form.stoichio).colored_rectangle_html()
            if form.__class__.__name__ == DiscForm.__name__:
                patch_str =  (f"**Disc**  |  *{form.stoichio}*  |  "
                              f"Center: ({form.x_pos:g}, {form.y_pos:g}) · Radius: {form.radius:g}")
            if form.__class__.__name__ == AlignedRectangleForm.__name__:
                patch_str = (f"**Rectangle**  |  *{form.stoichio}*  |  "
                              f"First vertex: ({form.vertex_1_x:g}, {form.vertex_1_y:g}) · "
                             f"Opposite vertex: ({form.vertex_2_x:g}, {form.vertex_2_y:g})")
            st.write(rectangle + ' ' + patch_str, unsafe_allow_html=True)
        with col12:
            if st.button("❌", key=f"patch_{i}"):
                sess[PATCH_FORMS_KEY].pop(i)
                st.rerun()
    if len(sess[PATCH_FORMS_KEY]) == 0:
        st.write("Start with the patches at the back, working towards the front.")

    st.divider()

    flex = st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="center")
    flex.subheader("**Add a patch:**", anchor='False', width=180)
    if flex.button("Disc"):
        DiscForm()
    if flex.button("Rectangle"):
        AlignedRectangleForm()

with col2:
    fig = go.Figure(
        [Scatter()],
        layout=go.Layout(xaxis={'showgrid': True}, yaxis={'scaleanchor':'x'}),
    )
    for form in sess[PATCH_FORMS_KEY]:
        form: DiscForm|AlignedRectangleForm
        color = Stoichiometry.from_str(form.stoichio).plotly_color()
        scatter = form.to_scatter(color, form.stoichio)
        fig.add_trace(scatter)
    st.plotly_chart(fig)


save_session_state(sess)