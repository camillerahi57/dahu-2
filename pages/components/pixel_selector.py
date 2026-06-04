import pyperclip
from PIL.ImageFile import ImageFile
from streamlit import dialog
from streamlit_image_coordinates import streamlit_image_coordinates
import streamlit as st

from logic.constants import PIXEL_COORDS


@dialog("Pixel Selector")
def show_pixel_selector(target_img):
    coords = streamlit_image_coordinates(
        target_img, use_column_width=True, cursor='crosshair',
        image_format='PNG', png_compression_level=0, key=PIXEL_COORDS
    )
    st.write("**Click on a pixel to get its coordinates.**")
    if coords:
        x, y = coords['x'], coords['y']
        pyperclip.copy(f'{x}, {y}')
        with st.container(horizontal=True, vertical_alignment='center'):
            with st.container(border=True, width='content'):
                st.write(f"Clicked at:   **{x}, {y}**")
            with st.container(width='content'):
                st.success(f"Copied to clipboard.")


def pixel_selector_button(target_img: ImageFile, key: str = '0'):
    if PIXEL_COORDS in st.session_state:
        del st.session_state[PIXEL_COORDS]  # Reset the coordinates first.

    if st.button('⏹️ Pixel Selector', key=f'pixel_selector_{key}'):
        show_pixel_selector(target_img)
