import io

import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from plotly.graph_objs import Scatter
from streamlit_cropperjs import st_cropperjs
from streamlit_image_coordinates import streamlit_image_coordinates

from logic.constants import CookieKeys as Ck, SessionKeys as Sk
from logic.db_enums import ShapeType
from logic.db_schema import Target, db, Patch
from logic.form_fields.new_target import MadeAtField, ExperimenterEmailField, \
    TargetNameField, CommentField, \
    PhotoUploadField, \
    TargetDiameterMillimeters, TargetDiameterInPixels, \
    PatchText
from logic.functions import save_session_state, load_session_state, \
    store_file


@st.dialog("How to")
def guide():
    st.write(
        "For each patch, write one line like:\n\n"
        "**[disc or polygon]** / **[stoichiometry]** "
        "/ **X1,Y1** / **X2,Y2** / ... / **XN,YN**")
    st.subheader("What are these X,Y points?")
    st.write(
        "- **If it's a disc**, chose any 3 points on the circumference "
        "that are pretty far from each other.")
    st.write(
        "- **If it's a polygon**, write down the X,Y coordinates of each "
        "vertex of the polygon."
    )
    st.subheader("Example")
    st.write(
        "A target is always a disc with patches on it. "
        "Let's say we have 2 patches. One Nd disc patch, and "
        "one Fe rectangle patch. Here is the text you should "
        "write:"
    )
    st.code(PatchText.EXAMPLE)


sess = load_session_state('new_target.py')
# st.set_page_config(layout="wide")

col1, col2 = st.columns(2)
with col1:
    made_on_fld = MadeAtField.input()
with col2:
    email_fld = ExperimenterEmailField.input()
target_name_fld = TargetNameField.input()
comment_fld = CommentField.input()
col1, col2 = st.columns(2)
with col1:
    photo_upload_fld = PhotoUploadField.input()
with col2:
    if Sk.TARGET_IMG not in sess:
        if photo_upload_fld.value:
            photo = photo_upload_fld.value.read()
            with st.container(width=300):
                cropped_pic = st_cropperjs(pic=photo, btn_text="Select target",
                                           key="foo")
                if cropped_pic:
                    target_img = Image.open(io.BytesIO(cropped_pic))
                    sess[Sk.TARGET_IMG] = target_img
    else:
        target_img = sess[Sk.TARGET_IMG]
        st.container(height=50, border=False)
        st.write("**Target cropped ✅**")

fields = [made_on_fld, email_fld, target_name_fld, comment_fld,
          photo_upload_fld]
can_create_target = all(fld.is_valid for fld in fields)
if can_create_target and Sk.TARGET_IMG in sess:
    target = Target.new(
        made_on=made_on_fld.value,
        made_by_email=email_fld.value,
        physical_name=target_name_fld.value,
        comment=comment_fld.value,
        photo_file_name=photo_upload_fld.create_file_name(),
    )

    coords = streamlit_image_coordinates(
        target_img, use_column_width=True, cursor='crosshair',
        image_format='PNG', png_compression_level=0)

    st.write("**Click on the above image to get pixel coordinates.**")
    if coords:
        with st.container(border=True, width='content'):
            st.write(f"Clicked at:   **{coords['x']},{coords['y']}**")

    col1, col2 = st.columns([100, 40])
    with col1:
        st.title('Patches')
        if st.button("How to write patch data"):
            guide()
        patch_txt_fld = PatchText.input()
        try:
            patches = Patch.from_patch_text(patch_txt_fld.value, target)
            is_valid_text = True
        except Exception as e:  # noqa
            if patch_txt_fld.value != '':
                st.warning(str(e))
            patches = []
            is_valid_text = False

    with col2:
        fig = go.Figure(
            [Scatter()],
            layout=go.Layout(
                xaxis={'showgrid': True, 'side': 'top'},
                yaxis={'scaleanchor': 'x', 'autorange': 'reversed'},
            ),
            # layout=go.Layout(
            #     xaxis={'showgrid': True, 'side': 'top', 'range': [0, 100]},
            #     yaxis={'scaleanchor': 'x', 'range': [100, 0]},
            # ),
        )

        for patch in patches:
            scatter = patch.to_scatter()
            fig.add_trace(scatter)
        st.plotly_chart(fig)


    for patch in patches:
        rectangle = Patch.colored_rectangle_html(patch.stoichio)
        if patch.shape_type == ShapeType.DISC:
            disc = patch.disc
            x, y, r = disc.center_px_x, disc.center_px_y, disc.radius_in_px
            patch_str = '  |  '.join([
                '**Disc**',
                f'*{patch.stoichio}*',
                f"Center: **{x:.0f},{y:.0f}** · Radius: **{r:.0f}**"
            ])
        elif patch.shape_type == ShapeType.POLYGON:
            poly = patch.polygon
            vertices_text = ' — '.join(
                [f'**{v.pixel_x},{v.pixel_y}**'
                 for v in poly.ordered_vertices()])
            patch_str = '  |  '.join([
                "**Polygon**",
                f"*{patch.stoichio}*",
                f"Vertices: {vertices_text}"
            ])
        else:
            raise RuntimeError(f'Unknown shape type: {patch.shape_type}')
        st.write(rectangle + ' ' + patch_str, unsafe_allow_html=True)

    # TODO Mettre target state proprement sur le schéma
    st.divider()

    fields += [patch_txt_fld]

    if len(patches) > 0 and all(f.is_valid for f in fields):
        with st.container(horizontal=True, vertical_alignment='center'):
            pixel_diameter_fld = TargetDiameterInPixels.input()
            real_diameter_fld = TargetDiameterMillimeters.input()
        target_patch = patches[0]
        has_coherent_diameter = (
            pixel_diameter_fld.is_coherent_with_1st_patch(target_patch)
        )
        pixel_diameter_fld.show_coherence_warning(target_patch)
        st.divider()
        fields += [pixel_diameter_fld, real_diameter_fld]
        all_flds_valid = all(fld.is_valid for fld in fields)
        can_submit = all_flds_valid and has_coherent_diameter

        if st.button("Submit", disabled=not can_submit, type="primary"):
            sess[Ck.LAST_EMAIL_USED] = email_fld.value  # Save last used email for
            # future autofill.

            with db.atomic():  # Save everything in a single transaction
                # (everything or nothing).
                target.save()
                for patch in patches:
                    patch.save()
                    if patch.shape_type == ShapeType.DISC:
                        patch.disc.save()
                    if patch.shape_type == ShapeType.POLYGON:
                        patch.polygon.save()
                        for v in patch.polygon.ordered_vertices():
                            v.save()
                # If the transaction has not failed at this point:
                store_file(photo_upload_fld.value.getvalue(),
                           target.photo_file_name)

            save_session_state(sess)
            st.switch_page('target_added.py')
