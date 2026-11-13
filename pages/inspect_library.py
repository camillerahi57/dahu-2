"""Page showing one library: its film, files, modifications and
characterizations.

The library is chosen by the `lib_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.LIB`). The page shows:

- the comment, and Archive / Delete / Edit buttons;
- the film modifications (annealing, etchings) in order, each opening
  a dialog (a pop-up window) with its details;
- the characterizations, own and referenced (see `CharacReference`);
- the uploaded files;
- the film's info and its layer table, bottom (buffer side) layer
  first.

Opening the page updates `Library.last_inspected_at`, used to sort the
browse page.
"""
from datetime import datetime, timedelta

import streamlit as st
from pandas import DataFrame

from components.browsing import INSPECT_BUTTON_KEY
from components.forms.new_library.fields import DepositTempField
from components.general import (
    init_page, current_params, switch_page_bttn,
    switch_to_submit_successful, link_html, email_html, icon,
)
from components.inspection import inspect_page_header, show_film_layer
from components.library_files import file_list_container
from logic.constants import SessionKeys as Sk, IdType
from logic.global_variables import sess
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_enums import FilmModifType, CharacType
from logic.lab_modelization.db_models import (
    Library, Film, Substrate, FilmModification, \
    IonBeamEtching, WetEtching, Etching, Annealing, LiftOffEtching, Charac, Edx)
from logic.page_list import pages
from logic.table_columns import LibInspectColumnName as ColName

init_page(pages.inspect_lib)
lib_id = current_params()[IdType.LIB]
lib: Library = Library.get_by_id(lib_id)
film: Film = Film.get(Film.library == lib)
substrate: Substrate = Substrate.get_by_id(film.substrate)
layers = film.ordered_layers

target_link_htmls = [link_html(target.label, target.url())
                     for target in film.targets]

# Read from the session state (data Streamlit keeps between reruns of
# the page for this browser tab) by the film modification form fields.
# `new_film_modif.py` sets it too.
sess[Sk.CURRENT_FILM] = film

st.set_page_config(layout="wide", page_title=lib.label)


def dependent_lib_error(lib_: Library):
    """Explain why the library can't be deleted, with library links.

    Never shown for now: `Library.dependent_libraries` always returns
    an empty list, so `can_be_deleted` is always True.

    Args:
        lib_: The library the user tried to delete.
    """
    libs = lib_.dependent_libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other librarie(s) refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url})"
    st.error(markdown)


def etching_base_info(etching: Etching):
    """Draw what all etchings share: the pattern image and the recipe.

    Args:
        etching: The general etching row of the modification.
    """
    with st.container(horizontal=True, vertical_alignment='center'):
        has_pattern_str = 'Yes' if etching.has_a_pattern else 'No'
        st.write(f"**Has a pattern**: {has_pattern_str}.")
        if etching.pattern:
            st.image(etching.pattern.file_bytes)
        else:
            if etching.has_a_pattern:
                st.write('No pattern found.')

    with st.container(horizontal=True, vertical_alignment='center'):
        st.write(f"**Recipe:**")
        if etching.recipe:
            etching.recipe.download_bttn()
        else:
            st.write('No recipe found.')


def ion_beam_etch_info(process: IonBeamEtching):
    """Draw the ion beam etching settings and its plasma composition.

    Args:
        process: The ion beam etching to describe.
    """
    st.header(f"**Ion Beam Etching**")
    # Two newlines make a paragraph break in Markdown, so each value is
    # on its own line.
    st.write(process.data_string(separator='\n\n'))

    # Proportions are fractions that the form already normalized to sum
    # to 1, so dividing by their sum changes (almost) nothing.
    constituents = process.constituents
    proportion_sum = sum(const.proportion for const in constituents)
    constituents_str = ''
    for const in constituents:
        percent = const.proportion / proportion_sum * 100
        constituents_str += f"\n- {const.stoichio_str}: {percent:g}%"
    st.write(f"**Plasma constituents:**{constituents_str}")


def wet_etch_info(process: WetEtching):
    """Draw the wet etching settings.

    Args:
        process: The wet etching to describe.
    """
    st.header(f"**Wet Etching**")
    st.write(process.data_string(separator='\n\n'))

@st.dialog(title="Confirm")
def confirm_deletion_dialog(lib_: Library):
    """Ask for confirmation, then delete the library and all its data.

    Opens as a dialog. On confirmation, deletes the library with its
    film (layers and modifications), uploaded files (rows and files)
    and references to other characterizations, writing `AppLog` rows,
    then goes to the "submission successful" page. The film's own
    characterizations are not deleted, despite the message (see
    `DOC_NOTES.md`).

    Args:
        lib_: The library to delete.
    """
    st.error(f"Are you sure you want to **permanently** delete the "
             f"library **\"{lib_.label}\"**?\n\n**This will also delete:**\n"
             f"- Film data\n- Film characterizations\n- Film modifications\n"
             f"- Uploaded files for this library")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            # TODO `Film.delete_parts` deletes layers and
            #   modifications but not the film's own `Charac` rows, and `Charac.film`
            #   is `on_delete='RESTRICT'`. Deleting a library whose film has a
            #   characterization should raise an `IntegrityError`, although the
            #   dialog says characterizations are deleted. The deletion is not in
            #   `with db.atomic():`, so rows deleted before the error (uploaded files,
            #   layers...) stay deleted, and their files are already removed.
            lib_.delete_with_parts()
            switch_to_submit_successful(pages.browse_libs)


def on_delete():
    """Handle a click on "Delete Library" (see `inspect_page_header`).

    Opens the confirmation dialog, or shows an error if other libraries
    depend on this one (never the case for now, see
    `dependent_lib_error`).
    """
    if lib.can_be_deleted():
        confirm_deletion_dialog(lib)
    else:
        dependent_lib_error(lib)


def annealing_info(process: Annealing):
    """Draw the annealing settings, atmosphere and temperature profile.

    Args:
        process: The annealing to describe.
    """
    st.header('Annealing')
    st.write(process.data_string(separator='\n\n'))

    atmosphere_str = "**Atmosphere:**"
    for i_, stoichio in enumerate(process.phase_stoichio_strings()):
        atmosphere_str += f"\n- Phase {i_+1}: {stoichio}"
    st.write(atmosphere_str)

    st.plotly_chart(process.get_figure())


def lift_off_info(process: LiftOffEtching):
    """Draw the lift-off settings (ultrasound use and configuration).

    Args:
        process: The lift-off to describe.
    """
    st.write(f"**Used ultrasound**: {process.used_ultrasound}\n\n"
             f"**Ultrasound config**: {process.ultrasound_config}\n\n")


def edx_info(edx: Edx):
    """Draw the EDX instrument settings and the result per element.

    Atomic percents (min, max, mean over the measured positions) are
    shown only for quantified elements. The EDX feature is still in
    development; the units shown for the settings are known to be wrong
    (see the `*_quantity` properties of `Edx`).

    Args:
        edx: The EDX subtype row of the characterization.
    """
    st.write(f"**Electron energy**: {edx.electron_energy_quantity}\n\n"
             f"**Working distance**: {edx.working_distance_quantity}\n\n"
             f"**Magnification**: {edx.magnification}\n\n"
             f"**Acquisition duration**: {edx.acquisition_duration_quantity}")
    st.subheader("Elements")
    for element in edx.elements:
        if element.quantified:
            st.write(f"**{element.element}**\n"
                     f"- Minimum: {element.min_atom_percent} %\n"
                     f"- Maximum: {element.max_atom_percent} %\n"
                     f"- Mean: {element.mean_atom_percent} %\n"
                     f"- Xline: {element.x_line}")
        else:
            st.write(f"**{element.element}**\n"
                     f"- Quantified: {element.quantified}\n"
                     f"- Xline: {element.x_line}")


@st.dialog(title="Characterisation")
def charac_dialog(charac: Charac):
    """Show a characterization's details, with a Delete button.

    Opens as a dialog. Deleting removes the `Charac` row and its
    subtype in a transaction (a group of DB writes applied all at once,
    or not at all), then reruns the page. Its data file is kept. If
    other libraries reference it, a warning dialog asks first (see
    `charac_ref_delete`).

    Args:
        charac: The characterization, own or referenced.

    Raises:
        RuntimeError: For a `type_` with no display code yet (anything
            but EDX).
    """
    last_modif = charac.last_modif
    if last_modif is None:
        last_modif_str = "_Deposition (no film modification)_"
    else:
        last_modif_str = f"{last_modif.modif_number}. {last_modif.modif_type}"
    st.write(f"**Made on**: {charac.made_on}\n\n"
             f"**Made by**: {charac.made_by_email}\n\n"
             f"**Comment**: _{charac.comment}_\n\n"
             f"**Made after**: {last_modif_str}")
    st.subheader(charac.type_)
    match charac.type_:
        case CharacType.EDX:
            edx_info(charac.edx)
        case _:
            raise RuntimeError(f"Unknown charac type: {charac.type_}")

    st.divider()
    if st.button("Delete characterisation ❌"):
        if charac.refs:
            # TODO Cannot call a dialog inside another one.
            charac_ref_delete(charac)
        else:
            with db.atomic():
                charac.delete_with_parts()
            st.rerun()
    st.write("(files will not be deleted)")


@st.dialog(title="Warning")
def charac_ref_delete(charac: Charac):
    """Warn that other libraries use a characterization, then delete it.

    Called from `charac_dialog`, i.e. a dialog opened from inside
    another dialog (see `DOC_NOTES.md`). On confirmation, deletes the
    characterization and the references to it, in a transaction, then
    reruns the page.

    Args:
        charac: The characterization to delete.
    """
    warning_str = "⚠️ Other libraries reference to this characterisation:"
    for ref in charac.refs:
        warning_str += f"\n- {ref.lib.label}"
    st.warning(warning_str)
    if st.button("Confirm deletion"):
        with db.atomic():
            charac.delete_with_parts()
        st.rerun()



@st.dialog('Modification Process')
def film_modif_info(modif_: FilmModification):
    """Show a film modification's details, with a Delete button.

    Opens as a dialog. Draws the common info, then the part specific to
    `modif_type`. Deleting removes the modification and its subtype rows
    in a transaction (writes `AppLog` rows; `FilmModification`
    renumbers the later modifications) and reruns the page.

    Args:
        modif_: The modification to show.

    Raises:
        RuntimeError: For an unknown `modif_type`.
    """
    st.write(f"**Made on**&ensp;{modif_.made_on}&ensp;**by**&ensp;"
             f"{modif_.made_by_email}.\n\n"
             f"**Comment**: _{modif_.comment}_")
    process = modif_.modification_process()

    # The `process: X` lines below do nothing when run: they only tell
    # the IDE which subtype `process` is in each branch.
    if modif_.modif_type == FilmModifType.ANNEALING:
        process: Annealing
        annealing_info(process)

    elif modif_.modif_type == FilmModifType.ION_BEAM_ETCHING:
        process: IonBeamEtching
        etching_base_info(process.etching)
        ion_beam_etch_info(process)

    elif modif_.modif_type == FilmModifType.WET_ETCHING:
        process: WetEtching
        etching_base_info(process.etching)
        wet_etch_info(process)

    elif modif_.modif_type == FilmModifType.LIFT_OFF:
        process: LiftOffEtching
        etching_base_info(process.etching)
        lift_off_info(process)

    else:
        raise RuntimeError(f'Unknown modification type: {modif_.modif_type}')

    st.divider()
    if st.button("Delete film modification ❌"):
        with db.atomic():
            # TODO `Charac.last_modif` is
            #   `on_delete='RESTRICT'`, so deleting a modification that a
            #   characterization points to should fail with an `IntegrityError`.
            modif_.delete_with_parts()
        st.rerun()


def charac_card(label_: str):
    """Draw a bordered box with a centred title.

    Not called anywhere at the moment.

    Args:
        label_: Title written in the box.
    """
    with st.container(border=True, horizontal_alignment='center'):
        st.space()
        st.subheader(label_, text_alignment='center')
        st.space()


@st.dialog(title='Archive?')
def archive_dialog():
    """Ask for confirmation, then mark the library as archived.

    Opens as a dialog. Saving writes an `AppLog` row; the page is then
    rerun to show the "Archived" banner.
    """
    st.write("This will not delete the library, no data will be lost.")
    st.write("The library will simply be marked as 'Archived'.")
    if st.button("Confim"):
        lib.is_archived = True
        lib.save()
        st.rerun()


def film_modif_section():
    """Draw the row of film modification buttons, in order, and "Add".

    Each button opens `film_modif_info`. "Add" goes to the new film
    modification page for this film.
    """
    with (st.container(horizontal=True, vertical_alignment='center',
                      horizontal_alignment='left', border=True)):
        st.write("**Film modifications:**")

        modif_names = {
            FilmModifType.LIFT_OFF: '🔦 Lift off',
            FilmModifType.ANNEALING: '♨️ Annealing',
            FilmModifType.WET_ETCHING: '🧪 Wet etching',
            FilmModifType.ION_BEAM_ETCHING: '☄️ Ion beam etching',
        }
        modifs = film.ordered_modifs()
        for i, modif in enumerate(modifs):
            if i != 0:
                st.write("->")
            if st.button(f'{modif_names[modif.modif_type]}', key=f'btn_{i}'):
                film_modif_info(modif)
        # Empty container: a 300-pixel gap before the "Add" link.
        st.container(width=300)
        switch_page_bttn(
            pages.new_film_modif,
            label='**Add**',
            type_='tertiary',
            icon_=icon('add_2'),
            q_params={IdType.FILM: film.id}
        )


def charac_section():
    """Draw the row of characterization buttons, oldest first, and "Add".

    Own characterizations are in bold; referenced ones (made on another
    film, see `CharacReference`) end with `*`. Each button opens
    `charac_dialog`.
    """
    with (st.container(horizontal=True, vertical_alignment='center',
                      horizontal_alignment='left', border=True)):
        st.write("**Characterisations:**")

        charac_names = {
            CharacType.EDX: 'EDX',
            CharacType.PROFILO: 'PROFILO',
        }
        characs = lib.all_characs()

        for i, charac in enumerate(characs):
            # "direct charac" means not a reference charac.
            is_direct_charac = charac.film.id == film.id
            if is_direct_charac:
                bttn_label = f'**{charac_names[charac.type_]}**'
            else:
                bttn_label = f'{charac_names[charac.type_]}*'
            if st.button(bttn_label, key=f'char_btn_{i}'):
                charac_dialog(charac)
        # Empty container: a 300-pixel gap before the "Add" link.
        st.container(width=300)
        switch_page_bttn(
            # Temporary. Should be "new charac" page/dialog:
            pages.browse_libs,
            label='**Add**',
            type_='tertiary',
            icon_=icon('add_2'),
            q_params={}
        )
    st.write("_* reference characterisation_")


def page_body():
    """Draw the whole page.

    Side effects: may save the library (see below), and the Unarchive
    button saves it (writes an `AppLog` row) and reruns the page.
    """
    if lib.is_archived:
        # A huge width makes the banner as wide as the page.
        st.warning("📦 Archived", width=10_000)

    # Each save writes an `AppLog` row, and Streamlit reruns the page at
    # every click; saving at most every 5 minutes avoids filling the
    # logs.
    if datetime.now() - lib.last_inspected_at > timedelta(minutes=5):
        lib.last_inspected_at = datetime.now()
        lib.save()

    inspect_page_header('Library', lib.label, on_delete, None)
    if not lib.is_archived:
        with st.container(horizontal_alignment='right'):
            if st.button("Archive 📦"):
                archive_dialog()
    else:
        with st.container(horizontal_alignment='right'):
            if st.button("Unarchive 📤"):
                lib.is_archived = False
                lib.save()
                st.rerun()

    st.write(
        f"**Comment:** {lib.comment if lib.comment else '*empty*'}")

    switch_page_bttn(
        pages.edit_lib,
        label='Edit name or comment', icon_='✏️', q_params={IdType.LIB: lib.id}
    )

    film_modif_section()

    col1, col2 = st.columns([40, 60])

    with col1:
        file_list_container(list(lib.general_files), lib)

    with col2:
        with st.container(border=True):
            with st.container(horizontal_alignment='right'):
                switch_page_bttn(pages.edit_film,
                                 label="Edit film information",
                                 icon_='✏️',
                                 q_params={IdType.FILM: film.id})
            date_str = film.made_on.strftime("%B %d, %Y")
            st.write(f"Made on **{date_str}** by "
                     f"**{email_html(film.made_by_email)}**",
                     unsafe_allow_html=True)
            st.write(f"**Label written on sample:** {film.label}")
            st.write(f"**Substrate:** "
                     f"{link_html(substrate.label, substrate.url())}",
                     unsafe_allow_html=True)
            st.write(f"**Targets:** {', '.join(target_link_htmls)}",
                     unsafe_allow_html=True)
            with st.container(horizontal_alignment='right'):
                switch_page_bttn(pages.edit_film_layers, label="Edit layers",
                                 q_params={IdType.FILM: film.id}, icon_='✏️')

            st.write(f"**Layers**:")

            col_conf = st.column_config
            # A click on "Details" stores the clicked row under the
            # widget key `INSPECT_BUTTON_KEY`, then calls
            # `show_film_layer(layers)`, which reads that row.
            column_config = {
                ColName.function: col_conf.TextColumn(width='small'),
                ColName.nominal_stoichio: col_conf.TextColumn(width='small'),
                ColName.details: col_conf.ButtonColumn(
                    'Details', width='small', on_click=show_film_layer,
                    key=INSPECT_BUTTON_KEY, args=[layers]),
                ColName.deposit_temp: col_conf.NumberColumn(width='small'),
                ColName.deposit_duration: col_conf.NumberColumn(width='small'),
                ColName.deposit_power: col_conf.NumberColumn(width='small'),
            }

            # Column titles give the UI units. The temperature is
            # converted from K to °C; duration (s) and power (W) are
            # shown as stored, since their UI units are the SI ones.
            table_rows = [
                {
                    ColName.function: lay.function,
                    ColName.nominal_stoichio: lay.nominal_stoichio_str,
                    ColName.details: 'Details',
                    ColName.deposit_temp:
                        DepositTempField.to_ui_unit(lay.deposit_temp)[0],
                    ColName.deposit_duration: lay.sputtering.deposit_duration,
                    ColName.deposit_power: lay.sputtering.deposit_power,
                }
                for lay in layers
            ]
            st.dataframe(DataFrame(table_rows), hide_index=True,
                         column_config=column_config)


page_body()