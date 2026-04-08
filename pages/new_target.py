import plotly.graph_objects as go
import streamlit as st
from plotly.graph_objs import Scatter

from logic.constants import SessionKeys as Sk, CookieKeys as Ck
from logic.db_schema import Target, db, Patch, Polygon
from logic.form_fields.new_target import MadeAtField, ExperimenterEmailField, \
    TargetNameField, CommentField, \
    StoichiometryField, DiscCenterX, DiscCenterY, RadiusField, \
    RectangleFirstVertexX, RectangleFirstVertexY, \
    RectangleOppositeVertexX, RectangleOppositeVertexY, PhotoUploadField, \
    TargetDiameterMillimeters, PolygonDataText
from logic.functions import save_session_state, load_session_state, \
    disc_patch_to_scatter, \
    polygon_patch_to_scatter, store_file

sess = load_session_state('new_target.py')

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
        all_fields_valid = all(fld.is_valid for fld in fields_)

        if st.button("Add Disc", disabled=not all_fields_valid):
            for fld in fields_:
                fld.remove_from_session()  # To have a new one in the next
                # pop-up.
            self.stoichio = stoichio_fld.value
            self.x_pos = x_pos_fld.value
            self.y_pos = y_pos_fld.value
            self.radius = radius_fld.value
            sess_[Sk.PATCH_FORMS].append(self)
            st.rerun()

    def to_scatter(self, color_: str, name_: str):
        x_y_radius_ = self.x_pos, self.y_pos, self.radius
        return disc_patch_to_scatter(x_y_radius_, color_, name_)


class PolygonForm:
    @st.dialog("New Polygon")
    def __init__(self):
        sess_ = st.session_state
        stoichio_fld = StoichiometryField.input()
        polygon_text = PolygonDataText.input()
        can_submit_ = stoichio_fld.is_valid and polygon_text.is_valid
        if st.button("Add Polygon", disabled=not can_submit_):
            stoichio_fld.remove_from_session()
            polygon_text.remove_from_session()
            self.stoichio = stoichio_fld.value
            self.polygon_text = polygon_text.value
            sess_[Sk.PATCH_FORMS].append(self)
            st.rerun()

    def vertices(self):
        return Polygon.polygon_text_to_vertices(self.polygon_text)

    def to_scatter(self, color_: str, name_: str):
        vertices_ = self.vertices()
        return polygon_patch_to_scatter(vertices_, color_, name_)


class AlignedRectangleForm:
    @st.dialog("New Aligned Rectangle")
    def __init__(self):
        sess_ = st.session_state
        stoichio_fld = StoichiometryField.input()
        st.subheader("First Vertex:")
        col1_, col2_ = st.columns(2)
        with col1_:
            vertex_1_x_fld = RectangleFirstVertexX.input()
        with col2_:
            vertex_1_y_fld = RectangleFirstVertexY.input()
        st.subheader("Opposite Vertex:")
        col1_, col2_ = st.columns(2)
        with col1_:
            vertex_2_x_fld = RectangleOppositeVertexX.input()
        with col2_:
            vertex_2_y_fld = RectangleOppositeVertexY.input()

        fields_ = [stoichio_fld, vertex_1_x_fld, vertex_1_y_fld, vertex_2_x_fld,
                   vertex_2_y_fld]
        all_fields_valid = all(fld.is_valid for fld in fields_)

        if st.button("Add Aligned Rectangle", disabled=not all_fields_valid):
            for fld in fields_:
                fld.remove_from_session()
            self.stoichio = stoichio_fld.value
            self.vertex_1_x = vertex_1_x_fld.value
            self.vertex_1_y = vertex_1_y_fld.value
            self.vertex_2_x = vertex_2_x_fld.value
            self.vertex_2_y = vertex_2_y_fld.value
            sess_[Sk.PATCH_FORMS].append(self)
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
        return polygon_patch_to_scatter(vertices_, color_, name_)


with col1:
    st.title('Patches')
    if Sk.PATCH_FORMS not in sess:
        sess[Sk.PATCH_FORMS] = []

    for patch_number, form in enumerate(sess[Sk.PATCH_FORMS]):
        col11, col12 = st.columns([85, 15])
        with col11:
            rectangle = Patch.colored_rectangle_html(form.stoichio)
            if form.__class__.__name__ == DiscForm.__name__:
                patch_str = (f"**Disc**  |  *{form.stoichio}*  |  "
                             f"Center: ({form.x_pos:g}, {form.y_pos:g}) · "
                             f"Radius: {form.radius:g}")
            if form.__class__.__name__ == AlignedRectangleForm.__name__:
                patch_str = (f"**Rectangle**  |  *{form.stoichio}*  |  "
                             f"First vertex: ({form.vertex_1_x:g}, "
                             f"{form.vertex_1_y:g}) · "
                             f"Opposite vertex: ({form.vertex_2_x:g}, "
                             f"{form.vertex_2_y:g})")
            if form.__class__.__name__ == PolygonForm.__name__:
                vertices_text = ' '.join(
                    [f'({x}, {y})' for x, y in form.vertices()])
                patch_str = (f"**Polygon**  |  *{form.stoichio}*  |  "
                             f"{vertices_text}")
            st.write(rectangle + ' ' + patch_str, unsafe_allow_html=True)
        with col12:
            if st.button("❌", key=f"patch_{patch_number}"):
                sess[Sk.PATCH_FORMS].pop(patch_number)
                st.rerun()
    if len(sess[Sk.PATCH_FORMS]) == 0:
        st.markdown("- Start with the patches at the back.\n"
                    "- The target base is the first patch.\n"
                    "- Open the target photo with Microsoft Paint to get "
                    "pixel positions (on the bottom left).")

    st.divider()

    st.subheader("**Add a patch:**", anchor='False', width=180)
    flex = st.container(horizontal=True, horizontal_alignment="left",
                        vertical_alignment="center")
    if flex.button("Disc"):
        DiscForm()
    if flex.button("Rectangle"):
        AlignedRectangleForm()
    if flex.button("Polygon"):
        PolygonForm()

with col2:
    fig = go.Figure(
        [Scatter()],
        layout=go.Layout(
            xaxis={'showgrid': True, 'side': 'top', 'range': [0, 100]},
            yaxis={'scaleanchor': 'x', 'range': [100, 0]},
        ),
    )

    for form in sess[Sk.PATCH_FORMS]:
        form: DiscForm | AlignedRectangleForm
        color = Patch.plotly_color(form.stoichio)
        scatter = form.to_scatter(color, form.stoichio)
        fig.add_trace(scatter)

    # if photo_upload_fld.value: # Not working (not the right positions and
    # orientation (André's image received on 2026-03-23)).
    # add_target_photo_to_fig(fig, photo_upload_fld.value)

    st.plotly_chart(fig)

target_diameter = TargetDiameterMillimeters.input()
st.divider()
fields = [made_at_fld, email_fld, target_name_fld, comment_fld,
          photo_upload_fld, target_diameter]
all_flds_valid = all(fld.is_valid for fld in fields)
at_least_one_patch = len(sess[Sk.PATCH_FORMS]) > 0
can_submit = all_flds_valid and at_least_one_patch

if st.button("Submit", disabled=not can_submit, type="primary"):
    sess[
        Ck.LAST_EMAIL_USED] = email_fld.value  # Save last used email for
    # future autofill.
    target = Target.new(
        made_at=made_at_fld.value,
        made_by_email=email_fld.value,
        physical_name=target_name_fld.value,
        comment=comment_fld.value,
        photo_file_name=photo_upload_fld.create_file_name(),
    )

    with db.atomic():  # Save everything in a single transaction (everything
        # or nothing).
        target.save()
        for patch_number, form in enumerate(sess[Sk.PATCH_FORMS]):
            is_target_base = patch_number == 0
            # If disc:
            if form.__class__.__name__ == DiscForm.__name__:
                x_y_radius = form.x_pos, form.y_pos, form.radius
                patch, disc = Patch.new_disc_patch(
                    form.stoichio, x_y_radius, target, patch_number,
                    is_target_base
                )
                # Save the patch (order matters):
                patch.save()
                disc.save()
            # If polygon:
            if form.__class__.__name__ in [AlignedRectangleForm.__name__,
                                           PolygonForm.__name__]:
                vertices = form.vertices()
                patch, polygon, vertices = Patch.new_polygon_patch(
                    form.stoichio, vertices, patch_number, target,
                    is_target_base
                )
                # Save the patch (order matters):
                patch.save()
                polygon.save()
                for v in vertices:
                    v.save()
        # If the transaction has not failed at this point:
        store_file(photo_upload_fld.value.getvalue(), target.photo_file_name)

    save_session_state(sess)
    st.switch_page('target_added.py')
