import streamlit as st
import plotly.graph_objects as go
from plotly.graph_objs import Scatter
from streamlit import text_input
from streamlit.runtime.state import SessionStateProxy

from logic.constants import ShapeType
from logic.db_schema import Stoichiometry, Patch, Disc, Polygon, Shape

sess = st.session_state

disc_example = "23.5, 48.1, 89.4\n41.8, 5, 4.1"


def disc_form():
    col1_, col2_, col3_ = st.columns(3)
    with col1_:
        x_pos = st.number_input("Disc center X position")
    with col2_:
        y_pos = st.number_input("Disc center Y position")
    with col3_:
        radius = st.number_input("Disc radius")

    if radius <= 0:
        st.text("⚠️ Radius must be strictly positive.")
        return None
    else:
        return Disc.create(center_x=x_pos, center_y=y_pos, radius=radius)


def polygon_form() -> Polygon | None:
    st.write()
    vertex_text = st.text_area(
        "Enter a list of vertices as one X,Y couple per line:",
        placeholder="Example for a triangle:\n\n21.6, 56.3\n41.3, 12\n20.3, 78",
        height=200,
    )
    polygon, msg = Polygon.from_text(vertex_text)
    if polygon is None:
        st.text(f"⚠️ {msg}")
        return None
    if len(list(polygon.vertices)) < 3:
        st.text("⚠️ Polygon must be at least 3 vertices.")
        return None
    else:
        return polygon


@st.dialog("New Disc Patch")
def new_patch(sess_: SessionStateProxy, is_disc: bool):
    stoichio_str = str(text_input("Enter patch stoichiometry."))
    is_valid_stoichio, msg = Stoichiometry.is_valid_stoichio(stoichio_str)
    if not is_valid_stoichio:
        if stoichio_str != '':
            st.write(f"⚠️ {msg}")

    shape_data = disc_form() if is_disc else polygon_form()

    if st.button("Add", disabled=not is_valid_stoichio or shape_data is None):
        if isinstance(shape_data, Polygon):
            shape = Shape.create(shape_type=ShapeType.POLYGON, polygon=shape_data)
        else:
            shape = Shape.create(shape_type=ShapeType.DISC, disc=shape_data)
        stoichio = Stoichiometry.from_str(stoichio_str)
        patch_ = Patch.create(stoichiometry=stoichio, shape=shape)
        sess_.patches.append(patch_)
        st.rerun()


col1, col2 = st.columns([100, 90])

with col1:
    if 'patches' not in sess:
        sess.patches = []

    st.title("Patches")

    for i, patch in enumerate(sess.patches):
        col11, col12 = st.columns([85, 15])
        with col11:
            rectangle = patch.stoichiometry.colored_rectangle_html()
            patch_info = (f"**{patch.shape.shape_type.capitalize()}**  |"
                          f"  *{patch.stoichiometry}*  |  {patch.shape}")
            st.write(rectangle + ' ' + patch_info, unsafe_allow_html=True)
        with col12:
            if st.button("❌", key=f"patch_{i}"):
                sess.patches.pop(i)
                st.rerun()

    if len(sess.patches) == 0:
        st.write("Start with the patches at the back, working towards the front.")

    st.divider()

    flex = st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="center")
    flex.subheader("**Add a patch:**", anchor='False', width=180)
    if flex.button("Disc"):
        new_patch(sess, is_disc=True)
    if flex.button("Polygon"):
        new_patch(sess, is_disc=False)

with col2:
    fig = go.Figure(
        [Scatter()],
        layout=go.Layout(xaxis={'showgrid': True}, yaxis={'scaleanchor':'x'}),
    )
    for patch in sess.patches:
        color = patch.stoichiometry.plotly_color()
        shape_type = patch.shape.shape_type
        stoichio = str(patch.stoichiometry)
        if shape_type == ShapeType.DISC:
            scatter = patch.shape.disc.to_scatter(color=color, name=stoichio)
        elif shape_type == ShapeType.POLYGON:
            scatter = patch.shape.polygon.to_scatter(color=color, name=stoichio)
        fig.add_trace(scatter)
    st.plotly_chart(fig)


    # polygon_scatters = [
    #     patch.shape.polygon.to_scatter(color=patch.stoichiometry.color())
    #     for patch in sess.patches
    #     if patch.shape.shape_type == ShapeType.POLYGON
    # ]
    # if len(polygon_scatters) == 0:
    #     polygon_scatters = [Scatter()]  # Default empty Scatter.
    #
    # fig = go.Figure(
    #     polygon_scatters,
    #     layout=go.Layout(xaxis={'showgrid': True}, yaxis={'scaleanchor':'x'}),
    # )
    #
    # for patch in sess.patches:
    #     if patch.shape.shape_type == ShapeType.DISC:
    #         patch.shape.disc.add_to_figure(fig, color=patch.stoichiometry.color())
    #
    # st.plotly_chart(fig)

