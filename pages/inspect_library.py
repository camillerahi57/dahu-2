"""Page showing one library: its film, files, modifications and
characterizations.

The library is chosen by the `lib_id` query parameter (a `name=value`
pair after the `?` of the URL, see `IdType.LIB`). The page shows:

- the comment, and Archive / Delete / Edit buttons;
- the film modifications (annealing, etchings) in order, each opening
  a dialog (a pop-up window) with its details;
- the characterizations, own (in bold) and referenced (marked `*`, see
  `CharacReference`), each opening a dialog with its details and a
  Delete or Remove reference button; "Add" opens a dialog to record a
  new one or to reference one made on another film;
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
from components.charac_info import charac_general_info, file_size_str
from components.forms.new_charac.sub_forms import CHARAC_TYPES
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
from logic.lab_modelization.db_enums import FilmModifType
from logic.lab_modelization.db_models import (
    Library, Film, Substrate, FilmModification, \
    IonBeamEtching, WetEtching, Etching, Annealing, LiftOffEtching, Charac,
    CharacReference)
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

    Shown when other libraries reference one of this library's
    characterizations (see `Library.dependent_libraries`).

    Args:
        lib_: The library the user tried to delete.
    """
    libs = lib_.dependent_libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other librarie(s) use some of its characterizations as "
                f"references. Remove these references first:")
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

    Opens as a dialog. On confirmation, deletes in a transaction the
    library with its film (layers, modifications and characterizations
    with their data files), uploaded files (rows and files) and
    references to other characterizations, writing `AppLog` rows, then
    goes to the "submission successful" page. Files are removed from
    `user_data/` for good, even if the transaction fails afterwards.

    Args:
        lib_: The library to delete.
    """
    st.error(f"Are you sure you want to **permanently** delete the "
             f"library **\"{lib_.label}\"**?\n\n**This will also delete:**\n"
             f"- Film data\n- Film modifications\n"
             f"- Film characterizations, **with their data files**\n"
             f"- Uploaded files for this library")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            with db.atomic():
                lib_.delete_with_parts()
            switch_to_submit_successful(pages.browse_libs)


def on_delete():
    """Handle a click on "Delete Library" (see `inspect_page_header`).

    Opens the confirmation dialog, or shows an error if other libraries
    depend on this one (see `dependent_lib_error`).
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


def charac_details(charac: Charac, is_own: bool):
    """Draw everything the DB knows about a characterization.

    Common info, then what is specific to its type (see
    `CHARAC_TYPES`).

    Args:
        charac: The characterization, own or referenced.
        is_own: True if it was made on this library's film; False if it
            was made on another film (a link to that film's library is
            then shown).
    """
    spec = CHARAC_TYPES[charac.type_]
    st.subheader(spec.name)
    charac_general_info(charac, show_film_link=not is_own)
    st.divider()
    spec.draw_info(charac)


def charac_download_button(charac: Charac):
    """Draw the button that downloads the characterization's data file.

    Shows a warning instead if the file is missing from `user_data/`.

    The file can be several GB, and the dialog is redrawn at every
    click. So the file is neither read nor given to Streamlit here:
    `data` is a function (`Path.read_bytes`) that Streamlit only calls
    when the user clicks the button (it then holds the file in memory
    to send it, so the download starts after a few seconds per GB).

    Args:
        charac: The characterization.
    """
    file = charac.file
    path = file.get_path()
    if not path.is_file():
        st.warning('The data file is missing from the server.')
        return
    size = file_size_str(path.stat().st_size)
    # `on_click='ignore'`: a click must not rerun the dialog.
    st.download_button(
        f'Download data file ({file.original_file_name}, {size})',
        data=path.read_bytes,
        file_name=file.download_file_name,
        icon=icon('download'),
        on_click='ignore',
        key=f'charac_download_{charac.id}',
        help='A big file can take a while to start downloading: the '
             'server reads it when you click.',
    )


def confirmation_requested(charac: Charac) -> bool:
    """Tell whether the user already clicked the first button (Delete,
    or Remove reference) for this characterization.

    The dialog is rerun at every click, and a button is only True during
    the run that follows its click, so the click is remembered in the
    session state (see `SessionKeys.CONFIRM_CHARAC_ACTION`).

    Args:
        charac: The characterization shown in the dialog.

    Returns:
        True if the confirmation part must be drawn.
    """
    return sess.get(Sk.CONFIRM_CHARAC_ACTION) == charac.id


def open_charac_dialog(charac: Charac):
    """Open `charac_dialog` from a clean state.

    Forgets a confirmation the user started and abandoned earlier, so
    that a dialog never opens already asking "are you sure?".

    Args:
        charac: The characterization to show.
    """
    sess.pop(Sk.CONFIRM_CHARAC_ACTION, None)
    charac_dialog(charac)


def charac_delete_section(charac: Charac):
    """Draw the Delete button of a characterization made on this film,
    and, once clicked, the warnings and the confirmation button.

    Confirming deletes, in a transaction, the characterization, its
    subtype rows, the references other libraries hold to it, and its
    data file (the row and the file in `user_data/`, for good), then
    reruns the page.

    Args:
        charac: A characterization made on this library's film.
    """
    if st.button('Delete ❌', key=f'charac_delete_{charac.id}'):
        sess[Sk.CONFIRM_CHARAC_ACTION] = charac.id
    if not confirmation_requested(charac):
        return

    st.error(
        f"⚠️ **The data file \"{charac.file.original_file_name}\" and all "
        f"the data extracted from it will be PERMANENTLY deleted from the "
        f"server.** This cannot be undone, except by restoring a backup "
        f"(which would also undo everything done since).")
    libs = charac.referencing_libs()
    if libs:
        # Markdown links open in a new tab, so the dialog stays open.
        links = '\n'.join(f"- [{lib_.label}]({lib_.url})" for lib_ in libs)
        plural = len(libs) > 1
        st.warning(
            f"⚠️ **{len(libs)} other librar{'ies' if plural else 'y'} "
            f"{'use' if plural else 'uses'} this characterisation as a "
            f"reference.** The reference will be removed from "
            f"{'each of them' if plural else 'it'}:\n\n{links}")
    if st.button('Yes, permanently delete this characterisation and its '
                 'file', type='primary', key=f'charac_confirm_{charac.id}'):
        with db.atomic():
            charac.delete_with_parts()
        sess.pop(Sk.CONFIRM_CHARAC_ACTION, None)
        st.rerun()


def charac_unreference_section(charac: Charac):
    """Draw the "Remove reference" button of a characterization made on
    another film, and, once clicked, the explanation and the
    confirmation button.

    Confirming deletes this library's `CharacReference` to the
    characterization, in a transaction, then reruns the page. The
    characterization itself and its file are kept.

    Args:
        charac: A characterization made on another film, referenced by
            this library.
    """
    if st.button('Remove reference', key=f'charac_unref_{charac.id}'):
        sess[Sk.CONFIRM_CHARAC_ACTION] = charac.id
    if not confirmation_requested(charac):
        return

    other_lib = charac.film.library
    st.info(
        "This only removes the link between this library and the "
        "characterisation. The characterisation and its file are kept in "
        "the library it was made on.")
    st.write(f"Library it was made on: "
             f"{link_html(other_lib.label, other_lib.url)}",
             unsafe_allow_html=True)
    if st.button('Confirm: remove reference', type='primary',
                 key=f'charac_unref_confirm_{charac.id}'):
        with db.atomic():
            for ref in (CharacReference.select()
                        .where(CharacReference.charac == charac,
                               CharacReference.lib == lib)):
                ref.delete_with_parts()
        sess.pop(Sk.CONFIRM_CHARAC_ACTION, None)
        st.rerun()


@st.dialog(title='Characterisation', width='large')
def charac_dialog(charac: Charac):
    """Show a characterization's details, with its Delete or Remove
    reference button.

    Opens as a dialog (a pop-up window), through `open_charac_dialog`.
    Draws the details, the download button for the data file, then:

    - if the characterization was made on this film: Delete, see
      `charac_delete_section`;
    - if it was made on another film: Remove reference, see
      `charac_unreference_section`. The details then link to the
      library of that film.

    A dialog cannot open another dialog, which is why the confirmation
    is drawn in this one.

    Args:
        charac: The characterization, own or referenced.
    """
    is_own = charac.film.id == film.id
    charac_details(charac, is_own)
    charac_download_button(charac)
    st.divider()
    if is_own:
        charac_delete_section(charac)
    else:
        charac_unreference_section(charac)


def characs_available_for_reference(other_film: Film) -> list[Charac]:
    """List the characterizations of another film that this library
    could reference.

    Args:
        other_film: The film the characterizations were made on.

    Returns:
        Its own characterizations (not the ones it references), minus
        those this library already references, oldest first.
    """
    already_referenced = [ref.charac_id for ref in lib.refs]
    return list(
        Charac.select()
        .where(Charac.film == other_film,
               Charac.id.not_in(already_referenced))
        .order_by(Charac.made_on, Charac.id))


def reference_picker():
    """Draw the steps to reference a characterization of another film:
    choose the film, then the characterization, then confirm.

    Only the films made with exactly the same targets are offered (see
    `Film.films_with_same_targets`). Confirming saves a
    `CharacReference` for this library, then reruns the page. Meant to
    be called inside `add_charac_dialog`.
    """
    same_target_films = film.films_with_same_targets()
    if not same_target_films:
        st.info("No other film was made with exactly the same targets "
                f"({', '.join(film.target_labels) or 'none'}).")
        return
    film_labels = {f.id: f"{f.label} (library: {f.library.label})"
                   for f in same_target_films}
    other_film_id = st.selectbox(
        "Films made with the same targets:", options=list(film_labels),
        index=None, format_func=lambda id_: film_labels[id_],
        key='ref_film_select')
    if other_film_id is None:
        return

    # Only the types the app can display are offered.
    characs = [c for c in characs_available_for_reference(
        Film.get_by_id(other_film_id)) if c.type_ in CHARAC_TYPES]
    if not characs:
        st.info("This film has no characterisation of its own that this "
                "library does not already reference.")
        return
    charac_labels = {
        c.id: f"{CHARAC_TYPES[c.type_].name} · {c.made_on} · "
              f"{c.made_by_email}" + (f" · {c.comment}" if c.comment else "")
        for c in characs}
    charac_id = st.selectbox(
        "Characterisation:", options=list(charac_labels), index=None,
        format_func=lambda id_: charac_labels[id_], key='ref_charac_select')
    if charac_id is None:
        return

    charac = Charac.get_by_id(charac_id)
    with st.expander("Details", expanded=False):
        charac_details(charac, is_own=False)
    if st.button('Confirm', type='primary', key='ref_confirm'):
        CharacReference(charac=charac, lib=lib).save()
        st.rerun()


@st.dialog(title='Add a characterisation')
def add_charac_dialog():
    """Ask where the new characterization was made, then go on.

    Opens as a dialog (a pop-up window).

    - "On this film": a link to the new characterization page (see
      `pages/new_charac.py`), where the data is entered.
    - "On another film": the choice is made right here, see
      `reference_picker`.
    """
    this_film = 'On this film'
    other_film = 'On another film (reuse its measurement)'
    origin = st.radio("Where was the characterisation made?",
                      [this_film, other_film], index=None,
                      key='add_charac_origin')
    if origin == this_film:
        switch_page_bttn(
            pages.new_charac, label='Continue',
            q_params={IdType.FILM: film.id}, icon_=icon('arrow_forward'))
    elif origin == other_film:
        reference_picker()


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
    # `Charac.last_modif` is `on_delete='RESTRICT'`: the DB refuses to
    # delete a modification that a characterization points to.
    characs = list(modif_.characs)
    if characs:
        st.warning(
            f"This modification cannot be deleted: {len(characs)} "
            f"characterisation(s) were made after it (it is their last "
            f"film modification). Delete them first.")
    elif st.button("Delete film modification ❌"):
        with db.atomic():
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


# Button label of each modification type: the emoji, a space, the name.
# `charac_section` reuses the emoji (the part before the first space).
MODIF_NAMES = {
    FilmModifType.LIFT_OFF: '🔦 Lift off',
    FilmModifType.ANNEALING: '♨️ Annealing',
    FilmModifType.WET_ETCHING: '🧪 Wet etching',
    FilmModifType.ION_BEAM_ETCHING: '☄️ Ion beam etching',
}


def film_modif_section():
    """Draw the row of film modification buttons, in order, and "Add".

    Each button opens `film_modif_info`. "Add" goes to the new film
    modification page for this film.
    """
    with (st.container(horizontal=True, vertical_alignment='center',
                      horizontal_alignment='left', border=True)):
        st.write("**Film modifications:**")

        modif_names = MODIF_NAMES
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
            q_params={IdType.FILM: film.id},
        )


def charac_section():
    """Draw the row of characterization buttons, oldest first, and "Add".

    Characterizations made on this film are in bold; referenced ones
    (made on another film, see `CharacReference`) end with `*`. Each
    button opens `charac_dialog`; "Add" opens `add_charac_dialog`.
    A button is prefixed with the emoji of the last film modification
    made before the measurement (none if measured as deposited).
    """
    characs = [c for c in lib.all_characs() if c.type_ in CHARAC_TYPES]
    with (st.container(horizontal=True, vertical_alignment='center',
                      horizontal_alignment='left', border=True)):
        st.write("**Characterisations:**")

        for charac in characs:
            # "own" means made on this library's film, not a reference.
            is_own = charac.film_id == film.id
            name = CHARAC_TYPES[charac.type_].name
            # Emoji of the last modification before the measurement;
            # nothing if the film was measured as deposited.
            if charac.last_modif is not None:
                modif_name = MODIF_NAMES[charac.last_modif.modif_type]
                name = f'{modif_name.split()[0]}{name}'
            bttn_label = f'**{name}**' if is_own else f'{name}*'
            if st.button(bttn_label, key=f'charac_btn_{charac.id}',
                         help=f'{charac.made_on} · {charac.made_by_email}'):
                open_charac_dialog(charac)
        # Empty container: a gap before the "Add" button.
        st.container(width=300)
        if st.button('**Add**', type='tertiary', icon=icon('add_2'),
                     key='charac_add_btn'):
            add_charac_dialog()
    if any(charac.film_id != film.id for charac in characs):
        st.write("_* reference characterisation (made on another film)_")


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
    charac_section()

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