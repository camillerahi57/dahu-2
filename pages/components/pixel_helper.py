"""The "Pixel Helper": a pop-up window showing the target photo, where
the user clicks pixels to read their coordinates and the distance
between two clicks, in pixels.

The target form (`components.forms.new_target.sub_forms`) uses it to
measure a length in pixels for the pixel/millimetre scale of the photo,
and to read the pixel coordinates of the patches drawn on it.
"""
from math import sqrt

import streamlit as st
from PIL.ImageFile import ImageFile
from streamlit import dialog
from streamlit_image_coordinates import streamlit_image_coordinates

from logic.constants import PIXEL_COORDS
from logic.constants import SessionKeys as Sk
from logic.global_variables import sess


@dialog("Pixel Helper")
def show_pixel_helper(target_img):
    """Open the pixel helper dialog (a pop-up window) on an image.

    A click on the image reruns only the dialog, not the whole page.
    The coordinates of the previous click are kept in the session state
    (Streamlit's per-tab dictionary that survives these reruns) to
    compute the distance.

    Side effect: writes `Sk.PREVIOUS_PIXEL_COORDS` in the session
    state.

    Args:
        target_img: The target photo (a PIL image).
    """
    st.write("**Click on a pixel to get its coordinates.**")
    st.write(f"**Click on two different pixels to get the distance between "
             f"them in pixels.**")
    st.write(f"You should not try to measure the diameter by eye, "
             f"because it's not precise enough.")
    st.write('You can zoom in and out with [Ctrl][+] and [Ctrl][-].')
    # Created before the image so that the results appear above it.
    coord_container = st.container(horizontal=True, vertical_alignment='center',
                                   border=True)
    # PNG, unlike JPEG, shows the photo's pixels unaltered.
    coords = streamlit_image_coordinates(
        target_img, use_column_width=True, cursor='crosshair',
        image_format='PNG', png_compression_level=0, key=PIXEL_COORDS
    )
    if coords:
        x, y = coords['x'], coords['y']
        # pyperclip.copy(f'{x} , {y}')  # TODO doesn't work, IDK why.
        with coord_container.container(border=False, width='content'):
            coord_container.write(f"Clicked at (x , y):   **{x} , {y}**")
        # with coord_container.container(width='content'):
        #     coord_container.success(f"Copied to clipboard.")
        if Sk.PREVIOUS_PIXEL_COORDS in sess:
            previous_x, previous_y = sess[Sk.PREVIOUS_PIXEL_COORDS]
            distance = round(sqrt((previous_x - x)**2 + (previous_y - y)**2))
            coord_container.write(f"Distance to previous click: **{distance}**"
                                  f" pixels.")
        sess[Sk.PREVIOUS_PIXEL_COORDS] = (x, y)


def pixel_helper_button(target_img: ImageFile, key: str = '0'):
    """Draw the "Pixel Helper" button, which opens `show_pixel_helper`.

    On each full page run, first forgets the clicks of the last time the
    dialog was open, so that a new dialog starts without a stale
    position or distance. (Clicks inside an open dialog rerun only the
    dialog, so they are not reset.)

    Side effect: deletes `PIXEL_COORDS` and `Sk.PREVIOUS_PIXEL_COORDS`
    from the session state.

    Args:
        target_img: The target photo.
        key: Makes the button's widget key unique when a page has
            several of these buttons.
    """
    if PIXEL_COORDS in st.session_state:
        del st.session_state[PIXEL_COORDS]  # Reset the coordinates first.
        if Sk.PREVIOUS_PIXEL_COORDS in st.session_state:
            del st.session_state[Sk.PREVIOUS_PIXEL_COORDS]

    if st.button('⏹️ Pixel Helper', key=f'pixel_helper_{key}'):
        show_pixel_helper(target_img)
