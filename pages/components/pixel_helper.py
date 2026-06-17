from math import sqrt

import pyperclip
from PIL.ImageFile import ImageFile
from streamlit import dialog
from streamlit_image_coordinates import streamlit_image_coordinates
import streamlit as st

from logic.constants import SessionKeys as Sk
from logic.constants import PIXEL_COORDS


@dialog("Pixel Helper")
def show_pixel_helper(target_img):
    sess = st.session_state
    st.write("**Click on a pixel to get its coordinates.**")
    st.write(f"**Click on two different pixels to get the distance between "
             f"them in pixels.**")
    st.write(f"You should not try to measure the diameter at a glance, "
             f"because it's not precise enough.")
    st.write('You can zoom in and out with [Ctrl][+] and [Ctrl][-].')
    coord_container = st.container(horizontal=True, vertical_alignment='center',
                                   border=True)
    coords = streamlit_image_coordinates(
        target_img, use_column_width=True, cursor='crosshair',
        image_format='PNG', png_compression_level=0, key=PIXEL_COORDS
    )
    if coords:
        x, y = coords['x'], coords['y']
        pyperclip.copy(f'{x} , {y}')
        with coord_container.container(border=False, width='content'):
            coord_container.write(f"Clicked at (x , y):   **{x} , {y}**")
        with coord_container.container(width='content'):
            coord_container.success(f"Copied to clipboard.")
        if Sk.PREVIOUS_PIXEL_COORDS in sess:
            previous_x, previous_y = sess[Sk.PREVIOUS_PIXEL_COORDS]
            distance = round(sqrt((previous_x - x)**2 + (previous_y - y)**2))
            coord_container.write(f"Distance to previous pixel: **{distance}**"
                                  f" pixels.")
        sess[Sk.PREVIOUS_PIXEL_COORDS] = (x, y)


def pixel_helper_button(target_img: ImageFile, key: str = '0'):
    if PIXEL_COORDS in st.session_state:
        del st.session_state[PIXEL_COORDS]  # Reset the coordinates first.
        del st.session_state[Sk.PREVIOUS_PIXEL_COORDS]

    if st.button('⏹️ Pixel Helper', key=f'pixel_helper_{key}'):
        show_pixel_helper(target_img)
