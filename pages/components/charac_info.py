"""Drawing of what a characterization (`Charac`) holds, as read-only text.

Used by the "Characterisations" dialogs of the library page and by the
preview of the "new characterization" form. Each kind of
characterization has its own drawing function here (`edx_info`...),
which `CHARAC_TYPES` (in `forms/new_charac/sub_forms.py`) lists.
"""
import streamlit as st
from pandas import DataFrame

from components.general import email_html, extensive_date_str, link_html
from logic.lab_modelization.db_models import Charac, Edx, FilmModification


def modif_label(modif: FilmModification | None) -> str:
    """Name a film modification by its position in the film's history.

    Args:
        modif: The modification, or None for the film as deposited.

    Returns:
        E.g. `'2. Wet etching'`; `'Initial state (as deposited)'` for
        None. Positions start at 1 (the DB's `modif_number` starts at
        0).
    """
    if modif is None:
        return 'Initial state (as deposited)'
    type_name = str(modif.modif_type).replace('_', ' ').capitalize()
    return f'{modif.modif_number + 1}. {type_name}'


def file_size_str(n_bytes: int) -> str:
    """Write a file size in a readable unit.

    Args:
        n_bytes: Size in bytes.

    Returns:
        E.g. `'5.12 GB'` (decimal units: 1 GB = 10^9 bytes).
    """
    size = float(n_bytes)
    for unit in ('bytes', 'kB', 'MB'):
        if size < 1000:
            return f'{size:.3g} {unit}'
        size /= 1000
    return f'{size:.3g} GB'


def charac_general_info(charac: Charac, show_film_link: bool = False):
    """Draw what every characterization has: date, author, comment...

    Args:
        charac: The characterization.
        show_film_link: True to also name the film it was made on, with
            a link to that film's library. For a characterization the
            library only references (made on another film).
    """
    comment = charac.comment if charac.comment else '*empty*'
    lines = [
        f"**Made on**: {extensive_date_str(charac.made_on)}",
        f"**Made by**: {email_html(charac.made_by_email)}",
        f"**Last film modification before it**: "
        f"{modif_label(charac.last_modif)}",
        f"**Comment**: {comment}",
    ]
    if show_film_link:
        film = charac.film
        lines.insert(0, f"**Made on film**: "
                        f"{link_html(film.label, film.library.url)}")
    st.write('\n\n'.join(lines), unsafe_allow_html=True)


def edx_info(edx: Edx):
    """Draw the EDX instrument settings and the result per element.

    Atomic percents (min, max, mean over the measured positions) are
    only available for quantified elements: the others were detected
    but not quantified, and their cells are empty.

    Args:
        edx: The EDX subtype row of the characterization. It can be
            unsaved, as long as its `elements` list is set (the form
            preview does so).
    """
    energy = edx.electron_energy_quantity
    distance = edx.working_distance_quantity
    duration = edx.acquisition_duration_quantity
    # `~P`: Pint's short and "pretty" format, e.g. keV.
    st.write(
        f"**Electron energy**: {energy.magnitude:.6g} {energy.units:~P}"
        f"\n\n**Working distance**: "
        f"{distance.magnitude:.6g} {distance.units:~P}"
        f"\n\n**Magnification**: {edx.magnification:g}"
        f"\n\n**Acquisition duration**: "
        f"{duration.magnitude:.6g} {duration.units:~P}")

    st.write("**Elements**")
    # A saved `Edx` gives a query; make it a list to read it twice.
    elements = list(edx.elements)
    rows = [
        {
            'Element': element.element,
            'X-ray line': element.x_line,
            'Min (at. %)': element.min_atom_percent,
            'Max (at. %)': element.max_atom_percent,
            'Mean (at. %)': element.mean_atom_percent,
        }
        for element in elements
    ]
    st.dataframe(DataFrame(rows), hide_index=True)
    if not all(element.quantified for element in elements):
        st.caption("Empty values: element detected but not quantified.")


def edx_charac_info(charac: Charac):
    """Draw the EDX part of a characterization (see `edx_info`).

    Args:
        charac: A characterization of type EDX.
    """
    edx_info(charac.edx)
    with st.container(horizontal=True, horizontal_alignment='distribute'):
        size = 600
        for fig in charac.figures(size=size):
            with st.container(width=size, height=size):
                st.plotly_chart(fig)
