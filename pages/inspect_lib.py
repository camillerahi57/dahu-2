import streamlit as st
from pandas import DataFrame

from logic.components import inspect_page_header
from logic.constants import LIB_ID_URL_KEY, SessionKeys as Sk
from logic.db_enums import FilmModifType
from logic.db_schema import Library, Film, Substrate, Target, FilmModification,\
    Annealing, Patterning, IonBeamEtching, WetEtching
from logic.functions import link_html, email_html, \
    load_session_state
from logic.sub_forms.new_film_modif import ModifData
from logic.table_columns import LibInspectColumnName as ColName


lib_id = st.query_params[LIB_ID_URL_KEY]
lib: Library = Library.get_by_id(lib_id)
film: Film = Film.get(Film.library == lib)
substrate: Substrate = Substrate.get_by_id(film.substrate)
layers = film.layers
targets: set[Target] = set(lay.target for lay in layers)
target_link_htmls = [link_html(target.physical_name, target.url())
                     for target in targets]
layers = reversed(list(layers))

sess = load_session_state('inspect_lib.py')
sess[Sk.CURRENT_FILM] = film

st.set_page_config(layout="wide", page_title=lib.name)


def dependent_lib_error(lib_: Library):
    libs = lib_.dependent_libraries()
    markdown = (f"The library cannot be deleted because {len(libs)} "
                f"other libraries refer to some of its characterizations:")
    for lib_ in libs:
        markdown += f"\n- [{lib_.name}]({lib_.url()})"
    st.error(markdown)


@st.dialog(title="Confirm")
def confirm_deletion_dialog(lib_: Library):
    st.error(f"Are you sure you want to **permanently** delete the "
             f"library **\"{lib_.name}\"**?\n\n**This will also delete:**\n"
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
    FilmModifType.ANNEALING: 'Annealing',
    FilmModifType.PATTERNING: 'Patterning',
    FilmModifType.ION_BEAM_ETCHING: 'Ion beam etching',
    FilmModifType.WET_ETCHING: 'Wet etching',
}

@st.dialog('Modification Process')
def film_modif_info(modif_: FilmModification):
    st.write(f"**Made on**: {modif_.made_on}\n\n"
             f"**Made by**: {modif_.made_by_email}")
    process = modif_.modification_process()

    if isinstance(process, Annealing):
        st.write(f"**Temperature:** {process.temperature}\n\n"
                 f"**Duration:** {process.duration}\n\n"
                 f"**Pressure:** {process.pressure}\n\n"
                 f"**Furnace:** {process.furnace}")

    elif isinstance(process, Patterning):
        st.write(f"**Diagram name:** {process.diagram_file_name}")
        st.image(process.image_path())

    elif isinstance(process, IonBeamEtching):
        st.write(f"**Depth:** {process.depth}\n\n"
                 f"**Duration:** {process.duration}\n\n"
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
            constituents_str += f"\n- {const.formula}: {percent:g}%"
        st.write(f"**Plasma constituents:**{constituents_str}")

    elif isinstance(process, WetEtching):
        st.write(f"**Depth:** {process.depth}\n\n"
                 f"**Duration:** {process.duration}\n\n"
                 f"**Temperature:** {process.temperature}")
        constituents = process.constituents
        proportion_sum = sum(const.proportion for const in constituents)
        constituents_str = ''
        for const in constituents:
            percent = const.proportion / proportion_sum * 100
            constituents_str += f"{const.formula}: {percent:g}%\n\n"
        st.write(f"**Acid constituents:**\n\n{constituents_str}")

    else:
        raise RuntimeError(f'Unknown modification type: {modif_}')

    st.divider()
    if st.button("Delete film modification ❌"):
        modif_.delete_instance()
        st.rerun()

def card(label: str):
    with st.container(border=True, horizontal_alignment='center'):
        st.space()
        st.subheader(label, text_alignment='center')
        st.space()


inspect_page_header('Library', lib.name, on_delete, lambda: None,
                    'browse_libs.py')

with (st.container(horizontal=True, vertical_alignment='center',
                  horizontal_alignment='left', border=True)):
    st.write("**Film modifications:**")
    modifs = film.ordered_modifs()
    for i, modif in enumerate(modifs):
        if st.button(f'{i+1} -> {MODIF_NAMES[modif.modif_type]}'):
            film_modif_info(modif)
    st.container(width=300)
    if st.button('➕**Add**', type='tertiary'):
        ModifData.form()

col1, col2 = st.columns([40, 60])

with col1:
    with st.container(horizontal=True, vertical_alignment='center'):
        card('EDX')
        card('MOKE')
        card('PROFILO')
    with st.container(horizontal=True, vertical_alignment='center'):
        card('X-RAY')
        card('MOKE-2')
        card('EDX-2')

with col2:
    with st.container(border=True):
        date_str = film.made_on.strftime("%B %d, %Y")
        st.write(f"Made on **{date_str}** by "
                 f"**{email_html(film.made_by_email)}**",
                 unsafe_allow_html=True)
        st.write(f"**Label written on sample:** {film.physical_name}")
        st.write(f"**Substrate:** "
                 f"{link_html(substrate.name, substrate.url())}",
                 unsafe_allow_html=True)
        st.write(f"**Target:** {', '.join(target_link_htmls)}",
                 unsafe_allow_html=True)
        st.write(
            f"**Comment:** {lib.comment if lib.comment else '*No comment.*'}")
        st.write(f"**Layers**:")
        table_content = [
            {
                ColName.stoichio: lay.stoichiometry,
                ColName.deposit_temp: lay.deposit_temp,
                ColName.deposit_duration: lay.deposit_duration,
                ColName.deposit_power: lay.deposit_power,
            }
            for lay in layers
        ]
        st.dataframe(DataFrame(table_content), hide_index=True, )