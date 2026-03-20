from uuid import uuid4

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.graph_objs import Scatter

from logic.constants import PATCH_FORMS_KEY, TARGET_FORM_STAGING_KEY, StorageKeys as Sk, FILE_STORAGE_PATH
from logic.db_schema import Target, db, Patch
from logic.forms.new_target import MadeAtField, ExperimenterEmailField, TargetNameField, CommentField, \
    StoichiometryField, DiscCenterX, DiscCenterY, RadiusField, RectangleFirstVertexX, RectangleFirstVertexY, \
    RectangleOppositeVertexX, RectangleOppositeVertexY, PhotoUploadField
from logic.functions import save_session_state, load_session_state, save_uploaded_file

sess = load_session_state('new_target.py')

if TARGET_FORM_STAGING_KEY not in sess:
    sess[TARGET_FORM_STAGING_KEY] = []

col1, col2 = st.columns(2)
with col1:
    made_at_fld = MadeAtField.input()
with col2:
    email_fld = ExperimenterEmailField.input()
target_name_fld = TargetNameField.input()
comment_fld = CommentField.input()
col1, col2 = st.columns(2)
with col1:
    photo_upload_fld = PhotoUploadField.input()
with col2:
    if photo_upload_fld.value:
        st.image(photo_upload_fld.value, width=200)

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

        fields_ = [stoichio_fld, x_pos_fld, y_pos_fld, radius_fld]
        all_fields_valid = all([fld.is_valid for fld in fields_])

        if st.button("Add Disc", disabled=not all_fields_valid):
            for fld in fields_:
                fld.remove_from_session()  # To have a new one in the next pop-up.
            self.stoichio = stoichio_fld.value
            self.x_pos = x_pos_fld.value
            self.y_pos = y_pos_fld.value
            self.radius = radius_fld.value
            sess_[PATCH_FORMS_KEY].append(self)
            st.rerun()

    def to_scatter(self, color_: str, name_: str):
        cx, cy, r = self.x_pos, self.y_pos, self.radius
        # Parametric circle as a closed Scatter trace
        theta = np.linspace(0, 2 * np.pi, 360)
        x = cx + r * np.cos(theta)
        y = cy + r * np.sin(theta)
        return Scatter(
            x=x,
            y=y,
            mode='lines',
            fill='toself',
            fillcolor=color_,
            opacity=1,
            line=dict(width=2, color='black'),
            showlegend=False,
            name=name_
        )


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

        fields_ = [stoichio_fld, vertex_1_x_fld, vertex_1_y_fld, vertex_2_x_fld, vertex_2_y_fld]
        all_fields_valid = all([fld.is_valid for fld in fields_])

        if st.button("Add Aligned Rectangle", disabled=not all_fields_valid):
            for fld in fields_:
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

    def to_scatter(self, color_: str, name_: str):
        vertices_ = self.vertices()
        # Closing the rectangle:
        vertices_.append(vertices_[0])
        x_coords, y_coords = zip(*vertices_)
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

    for patch_number, form in enumerate(sess[PATCH_FORMS_KEY]):
        col11, col12 = st.columns([85, 15])
        with col11:
            rectangle = Patch.colored_rectangle_html(form.stoichio)
            if form.__class__.__name__ == DiscForm.__name__:
                patch_str =  (f"**Disc**  |  *{form.stoichio}*  |  "
                              f"Center: ({form.x_pos:g}, {form.y_pos:g}) · Radius: {form.radius:g}")
            if form.__class__.__name__ == AlignedRectangleForm.__name__:
                patch_str = (f"**Rectangle**  |  *{form.stoichio}*  |  "
                              f"First vertex: ({form.vertex_1_x:g}, {form.vertex_1_y:g}) · "
                             f"Opposite vertex: ({form.vertex_2_x:g}, {form.vertex_2_y:g})")
            st.write(rectangle + ' ' + patch_str, unsafe_allow_html=True)
        with col12:
            if st.button("❌", key=f"patch_{patch_number}"):
                sess[PATCH_FORMS_KEY].pop(patch_number)
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
        color = Patch.plotly_color(form.stoichio)
        scatter = form.to_scatter(color, form.stoichio)
        fig.add_trace(scatter)
    st.plotly_chart(fig)


fields = [made_at_fld, email_fld, target_name_fld, comment_fld, photo_upload_fld]
all_flds_valid = all([fld.is_valid for fld in fields])
at_least_one_patch = len(sess[PATCH_FORMS_KEY]) > 0
can_submit = all_flds_valid and at_least_one_patch

if st.button("Submit", disabled=not can_submit):
    sess[Sk.LAST_EMAIL_USED] = email_fld.value  # Save last used email for future autofill.
    photo_file_path = save_uploaded_file(photo_upload_fld)
    target = Target.new(
        made_at=made_at_fld.value,
        made_by_email=email_fld.value,
        target_name=target_name_fld.value,
        comment=comment_fld.value,
        photo_path=photo_file_path,
    )

    with db.atomic():
        target.save()
        for patch_number, form in enumerate(sess[PATCH_FORMS_KEY]):
            # If disc:
            if form.__class__.__name__ == DiscForm.__name__:
                x_y_radius = form.x_pos, form.y_pos, form.radius
                patch, disc = Patch.new_disc_patch(
                    form.stoichio, x_y_radius, target, patch_number
                )
                # Save the patch (order matters):
                patch.save()
                disc.save()
            # If polygon:
            if form.__class__.__name__ == AlignedRectangleForm.__name__:
                vertices = form.vertices()
                patch, polygon, vertices = Patch.new_polygon_patch(
                    form.stoichio, vertices, patch_number, target
                )
                # Save the patch (order matters):
                patch.save()
                polygon.save()
                for v in vertices:
                    v.save()

    st.switch_page('target_added.py')


save_session_state(sess)