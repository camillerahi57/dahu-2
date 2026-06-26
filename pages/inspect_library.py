import streamlit as st
from pandas import DataFrame

from components.forms.new_film_modif.fields import PressureField
from logic.page_list import pages
from logic.components import inspect_page_header
from logic.constants import LIB_ID_URL_KEY, SessionKeys as Sk, DOMAIN, \
    FILM_ID_URL_KEY
from logic.db_enums import FilmModifType
from logic.lab_modelization.db_models import (
    Library, Film, Substrate, FilmModification,\
    Annealing, IonBeamEtching, WetEtching)
from logic.functions import link_html, email_html, \
    new_session_state
from logic.table_columns import LibInspectColumnName as ColName


lib_id = st.query_params[LIB_ID_URL_KEY]
lib: Library = Library.get_by_id(lib_id)
film: Film = Film.get(Film.library == lib)
substrate: Substrate = Substrate.get_by_id(film.substrate)
layers = film.ordered_layers

target_link_htmls = [link_html(target.label, target.url())
                     for target in film.targets]

sess = new_session_state(pages.inspect_lib)
sess[Sk.CURRENT_FILM] = film

st.set_page_config(layout="wide", page_title=lib.label)


def dependent_lib_error(lib_: Library):
    libs = lib_.dependent_libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other libraries refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.label}]({lib_.url()})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog(lib_: Library):
    st.error(f"Are you sure you want to **permanently** delete the "
             f"library **\"{lib_.label}\"**?\n\n**This will also delete:**\n"
             f"- Film data\n- Film characterizations\n- Film modifications\n"
             f"- Uploaded data for this library")
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button('I confirm'):
            lib_.delete_instance()
            st.switch_page('deleted_lib.py')


def on_delete():
    if lib.can_be_deleted():
        confirm_deletion_dialog(lib)
    else:
        dependent_lib_error(lib)


MODIF_NAMES = {
    FilmModifType.LIFT_OFF: 'Lift off',
    FilmModifType.ANNEALING: 'Annealing',
    FilmModifType.WET_ETCHING: 'Wet etching',
    FilmModifType.ION_BEAM_ETCHING: 'Ion beam etching',
}

@st.dialog('Modification Process')
def film_modif_info(modif_: FilmModification):
    st.write(f"**Made on**: {modif_.made_on}\n\n"
             f"**Made by**: {modif_.made_by_email}")
    process = modif_.modification_process()

    if isinstance(process, Annealing):
        pressure_unit_str = f'{PressureField.ui_unit:P}'
        st.write(f"**Pressure:** {process.pressure} {pressure_unit_str}\n\n"
                 f"**Furnace:** {process.furnace}")
        st.plotly_chart(process.get_figure())

    # elif isinstance(process, Patterning):
    #     st.write(f"**Diagram name:** {process.diagram_file_name}")
    #     st.image(process.image_path())

    elif isinstance(process, IonBeamEtching):
        st.write(f"**Duration:** {process.duration}\n\n"
                 f"**Flow:** {process.flow}\n\n"
                 f"**Incidence angle:** {process.incidence_angle}\n\n"
                 f"**Rotation:** {process.rotation}\n\n"
                 f"**Power:** {process.power}\n\n"
                 f"**Pressure:** {process.pressure}")
        constituents = process.constituents
        proportion_sum = sum(const.proportion for const in constituents)
        constituents_str = ''
        for const in constituents:
            percent = const.proportion / proportion_sum * 100
            constituents_str += f"\n- {const.stoichio_str}: {percent:g}%"
        st.write(f"**Plasma constituents:**{constituents_str}")

    elif isinstance(process, WetEtching):
        st.write(f"**Recipe:** {process.recipe_file_name}")
        constituents = process.constituents
        proportion_sum = sum(const.proportion for const in constituents)
        constituents_str = ''
        for const in constituents:
            percent = const.proportion / proportion_sum * 100
            constituents_str += f"- {const.stoichio_str}: {percent:g}%\n\n"
        st.write(f"**Acid constituents:**\n\n{constituents_str}")

    else:
        raise RuntimeError(f'Unknown modification type: {modif_}')

    st.divider()
    if st.button("Delete film modification ❌"):
        modif_.delete_instance(recursive=True)
        st.rerun()

def card(label_: str):
    with st.container(border=True, horizontal_alignment='center'):
        st.space()
        st.subheader(label_, text_alignment='center')
        st.space()


inspect_page_header('Library', lib.label, on_delete, lambda: None,
                    pages.browse_libs)

with (st.container(horizontal=True, vertical_alignment='center',
                  horizontal_alignment='left', border=True)):
    st.write("**Film modifications:**")
    modifs = film.ordered_modifs()
    for i, modif in enumerate(modifs):
        if i != 0:
            st.write("->")
        if st.button(f'{MODIF_NAMES[modif.modif_type]}', key=f'btn_{i}'):
            film_modif_info(modif)
    st.container(width=300)
    if st.button('➕**Add**', type='tertiary'):
        st.switch_page(
            pages.new_film_modif,
            query_params={FILM_ID_URL_KEY: film.id}
        )

col1, col2 = st.columns([40, 60])

with col1:
    with st.container(horizontal=True, vertical_alignment='center'):
        with st.container(border=True, horizontal_alignment='center'):
            label = '➕**Add new characterization**'
            url = f'http://{DOMAIN}/new_charac'  # noqa
            st.space()
            st.markdown(link_html(label, url), unsafe_allow_html=True,
                        text_alignment='center')
            st.space()
        card('MOKE')
        card('PROFILO')
    with st.container(horizontal=True, vertical_alignment='center'):
        card('X-RAY')
        card('MOKE-2')
        card('EDX')

with col2:
    with st.container(border=True):
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
        st.write(
            f"**Comment:** {lib.comment if lib.comment else '*No comment.*'}")
        st.write(f"**Layers**:")
        table_rows = [
            {
                ColName.nominal_stoichio: lay.nominal_stoichio_str,
                ColName.deposit_temp: lay.deposit_temp,
                ColName.deposit_duration: lay.sputtering.deposit_duration,
                ColName.deposit_power: lay.sputtering.deposit_power,
            }
            for lay in layers
        ]
        st.dataframe(DataFrame(table_rows), hide_index=True, )
