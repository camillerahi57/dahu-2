import streamlit as st
from pandas import DataFrame

from components.browsing import INSPECT_BUTTON_KEY
from components.forms.new_library.fields import DepositTempField
from components.library_files import file_list_container
from components.general import (
    sess, init_page, current_params, switch_page_bttn,
    switch_to_submit_successful, link_html, email_html,
)
from components.inspection import inspect_page_header, show_film_layer
from logic.constants import SessionKeys as Sk, IdType
from logic.db_enums import FilmModifType
from logic.lab_modelization.db_models import (
    Library, Film, Substrate, FilmModification, \
    IonBeamEtching, WetEtching, db, Etching, Annealing, LiftOffEtching)
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

sess[Sk.CURRENT_FILM] = film

st.set_page_config(layout="wide", page_title=lib.label)


def dependent_lib_error(lib_: Library):
    libs = lib_.dependent_libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other librarie(s) refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url()})"
    st.error(markdown)


def etching_base_info(etching: Etching):
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
    st.header(f"**Ion Beam Etching**")
    st.write(process.data_string(separator='\n\n'))

    constituents = process.constituents
    proportion_sum = sum(const.proportion for const in constituents)
    constituents_str = ''
    for const in constituents:
        percent = const.proportion / proportion_sum * 100
        constituents_str += f"\n- {const.stoichio_str}: {percent:g}%"
    st.write(f"**Plasma constituents:**{constituents_str}")


def wet_etch_info(process: WetEtching):
    st.header(f"**Wet Etching**")
    st.write(process.data_string(separator='\n\n'))

@st.dialog(title="Confirm")
def confirm_deletion_dialog(lib_: Library):
    st.error(f"Are you sure you want to **permanently** delete the "
             f"library **\"{lib_.label}\"**?\n\n**This will also delete:**\n"
             f"- Film data\n- Film characterizations\n- Film modifications\n"
             f"- Uploaded files for this library")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            lib_.delete_with_parts()
            switch_to_submit_successful(pages.browse_libs)


def on_delete():
    if lib.can_be_deleted():
        confirm_deletion_dialog(lib)
    else:
        dependent_lib_error(lib)


def annealing_info(process: Annealing):
    st.header('Annealing')
    st.write(process.data_string(separator='\n\n'))

    atmosphere_str = "**Atmosphere:**"
    for i_, stoichio in enumerate(process.phase_stoichio_strings()):
        atmosphere_str += f"\n- Phase {i_+1}: {stoichio}"
    st.write(atmosphere_str)

    st.plotly_chart(process.get_figure())


def lift_off_info(process: LiftOffEtching):
    st.write(f"**Used ultrasound**: {process.used_ultrasound}\n\n"
             f"**Ultrasound config**: {process.ultrasound_config}\n\n")


@st.dialog('Modification Process')
def film_modif_info(modif_: FilmModification):
    st.write(f"**Made on**&ensp;{modif_.made_on}&ensp;**by**&ensp;"
             f"{modif_.made_by_email}.\n\n"
             f"**Comment**: _{modif_.comment}_")
    process = modif_.modification_process()

    if modif_.modif_type == FilmModifType.ANNEALING:
        annealing_info(process)

    elif modif_.modif_type == FilmModifType.ION_BEAM_ETCHING:
        etching_base_info(process.etching)
        ion_beam_etch_info(process)

    elif modif_.modif_type == FilmModifType.WET_ETCHING:
        etching_base_info(process.etching)
        wet_etch_info(process)

    elif modif_.modif_type == FilmModifType.LIFT_OFF:
        etching_base_info(process.etching)
        lift_off_info(process)

    else:
        raise RuntimeError(f'Unknown modification type: {modif_.modif_type}')

    st.divider()
    if st.button("Delete film modification ❌"):
        with (db.atomic()):
            modif_.delete_with_parts()
        st.rerun()


def charac_card(label_: str):
    with st.container(border=True, horizontal_alignment='center'):
        st.space()
        st.subheader(label_, text_alignment='center')
        st.space()


@st.dialog(title='Archive?')
def archive_dialog():
    st.write("This will not delete the library, no data will be lost.")
    st.write("The library will simply be marked as 'Archived'.")
    if st.button("Confim"):
        lib.is_archived = True
        lib.save()
        st.rerun()


def page_body():
    if lib.is_archived:
        st.warning("📦 Archived", width=10_000)

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
        label='Edit name or comment', icon='✏️', q_params={IdType.LIB: lib.id}
    )

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
        st.container(width=300)
        switch_page_bttn(
            pages.new_film_modif,
            label='**Add**',
            type_='tertiary',
            icon='➕',
            q_params={IdType.FILM: film.id}
        )

    col1, col2 = st.columns([40, 60])

    with col1:
        file_list_container(list(lib.general_files), lib)

    with col2:
        with st.container(border=True):
            with st.container(horizontal_alignment='right'):
                switch_page_bttn(pages.edit_film,
                                 label="Edit film information",
                                 icon='✏️',
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
                                 q_params={IdType.FILM: film.id}, icon='✏️')

            st.write(f"**Layers**:")

            col_conf = st.column_config
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