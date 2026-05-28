import base64
import io
import re
from datetime import date as dt_date
from pathlib import Path
from time import sleep
from uuid import uuid4

import PIL
import numpy as np
import streamlit as st
from peewee import DateField
from streamlit.navigation.page import StreamlitPage
from streamlit_js_eval import streamlit_js_eval
from plotly.graph_objs import Scatter

from streamlit.runtime.state import SessionStateProxy
from streamlit_cookies_controller import CookieController

from logic.page_list import PageEnum
from logic.constants import (CookieKeys as Ck,
                             SessionKeys as Sk, FILE_STORAGE_PATH)


def highlight_rows(row) -> list[str]:
    if row.physical_name % 2 == 0:
        return ['background-color: white'] * len(row)
    else:
        return ['background-color: #f0f0f0'] * len(row)


def letter_count(text: str) -> int:
    upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return len(''.join(i for i in text if i.upper() in upper))


def new_controller() -> CookieController:
    controller = CookieController()  # It takes time to get it loaded.
    waited = 0
    while not controller.get('cookie_ready'):
        # In case it's the first time and the key has never been set:
        controller.set('cookie_ready', True)
        # In case the key has been set, but we have to wait:
        sleep(0.1)
        waited += 0.1
        if waited > 5:
            raise RuntimeError('Not able to load cookie')
    return controller


def disc_patch_to_scatter(x_y_radius: tuple[float, float, float], color_: str,
                          name_: str):
    cx, cy, r = x_y_radius
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
        line=dict(width=1, color='black'),
        showlegend=False,
        name=name_
    )


def polygon_patch_to_scatter(clock_wise_vertices: list[tuple[float, float]],
                             color_: str, name_: str):
    # return Scatter()
    vertices_ = clock_wise_vertices
    # Closing the rectangle:
    vertices_.append(vertices_[0])
    x_coords, y_coords = zip(*vertices_)
    return Scatter(
        x=x_coords, y=y_coords,
        mode='lines',
        fill='toself',
        fillcolor=color_,
        opacity=1,
        line=dict(width=1, color='black'),
        showlegend=False,
        name=name_,
    )


def load_session_state(page: StreamlitPage) -> SessionStateProxy:
    """Always start a page by colling this function, to reset the session.
    :rtype: SessionStateProxy
    """
    # TODO call this function in a custom switch_page function.
    sess = st.session_state
    if sess.get(Sk.PAGE_URL_PATH) != page.url_path:  # Page has changed.
        reset_session(sess)
        sess[Sk.PAGE_URL_PATH] = page.url_path
    add_cookie_data_to_session(sess)
    return sess


def add_cookie_data_to_session(sess: SessionStateProxy):
    controller = new_controller()
    for key in Ck:
        stored_value = controller.get(key)
        if stored_value is not None:
            sess[key] = stored_value


def reset_session(sess: SessionStateProxy):
    # page_name = sess.get(Sk.PAGE_URL_PATH)
    for key in sess:
        # if key in Ck or key.startswith(page_name):  # Y avait ça. Normal ?
        if key in Sk:
            del sess[key]


def refresh_page_in_browser():
    streamlit_js_eval(js_expressions="parent.window.location.reload()")


def save_session_state(sess: SessionStateProxy):
    controller = new_controller()
    for key in Ck:
        if key in sess:
            controller.set(key, sess[key])


def get_email_user_name(email_address: str) -> str:
    return re.match(r'[^@]+', email_address)[0]


def add_target_photo_to_fig(fig, uploaded_photo):
    img = PIL.Image.open(uploaded_photo)  # noqa
    w, h = img.size

    # Convert to base64 for Plotly
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()

    fig.add_layout_image(
        source=f"data:image/png;base64,{b64}",
        x=0,
        y=0,
        xref="x",
        yref="y",
        sizex=w,
        sizey=h,
        sizing="stretch",
        opacity=0.5,
        layer="above",  # On top of all scatters
    )

    fig.update_layout(
        xaxis=dict(range=[0, w]),
        yaxis=dict(range=[h, 0]),
    )


def is_valid_email_address(email_address: str) -> bool:
    # From https://stackoverflow.com/a/201378:
    email_regex = r"(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"  # noqa Long line.
    match = re.fullmatch(email_regex, email_address)
    return match is not None


def store_file(file_data: bytes, file_name: str = None) -> Path:
    if file_name is None:
        file_name = str(uuid4())
    file_path = FILE_STORAGE_PATH / file_name
    with open(file_path, "wb") as f:
        f.write(file_data)
    return file_path


def replace_file_name_extension(name: str, new_extension: str):
    new_extension = new_extension.removeprefix('.')
    parts = name.split(".")
    parts[-1] = new_extension
    return ".".join(parts)


def link_html(label: str, url: str):
    return f"<a href=\"{url}\" target=\"_self\">{label}</a>"


def email_html(email: str, label: str=None):
    if label is None:
        label = email
    return f'<a href="mailto:{email}">{label}</a>'


def extensive_date_str(date: DateField):
    return dt_date(date.year, date.month, date.day).strftime("%B %d, %Y")