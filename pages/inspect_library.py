import streamlit as st
from pandas import DataFrame

from components.forms.new_film_modif.fields import PressureField
from components.streamlit_tools import (
    sess, init_page, current_params, switch_button, switch_to_submit_successful)
from logic.page_list import pages
from logic.components import inspect_page_header
from logic.constants import SessionKeys as Sk, DOMAIN, IdType
from logic.db_enums import FilmModifType
from logic.lab_modelization.db_models import (
    Library, Film, Substrate, FilmModification, \
    Annealing, IonBeamEtching, WetEtching, db)
from logic.functions import link_html, email_html
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
            lib_.delete_instance(recursive=True)
            switch_to_submit_successful(pages.browse_libs)
            # st.switch_page('deleted_lib.py')


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
    st.write(f"**Made on**&ensp;{modif_.made_on}&ensp;**by**&ensp;"
             f"{modif_.made_by_email}.\n\n"
             f"**Comment**: {modif_.comment}")
    process = modif_.modification_process()

    if isinstance(process, Annealing):
        pressure_unit_str = f'{PressureField.ui_unit:P}'
        st.write(f"**Pressure:** {process.pressure} {pressure_unit_str}\n\n"
                 f"**Furnace:** {process.furnace}")
        st.plotly_chart(process.get_figure())

    elif isinstance(process, IonBeamEtching):
        st.write(f"**Duration:** {process.duration} &ensp; · &ensp;"
                 f"**Flow:** {process.flow} &ensp; · &ensp;"
                 f"**Incidence angle:** "
                 f"{process.incidence_angle} &ensp; · &ensp;"
                 f"**Rotation:** {process.rotation} &ensp; · &ensp;"
                 f"**Power:** {process.power} &ensp; · &ensp;"
                 f"**Pressure:** {process.pressure}")
        constituents = process.constituents
        proportion_sum = sum(const.proportion for const in constituents)
        constituents_str = ''
        for const in constituents:
            percent = const.proportion / proportion_sum * 100
            constituents_str += f"\n- {const.stoichio_str}: {percent:g}%"
        st.write(f"**Plasma constituents:**{constituents_str}")
        if process.patterns:
            pattern = process.patterns[0]
            pattern.retrieve_file_bytes()
            st.image(pattern.file_bytes, width=500)

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
        with db.atomic():
            modif_.delete_instance(recursive=True)
        st.rerun()

def card(label_: str):
    with st.container(border=True, horizontal_alignment='center'):
        st.space()
        st.subheader(label_, text_alignment='center')
        st.space()


inspect_page_header('Library', lib.label, on_delete, None)
st.write(
    f"**Comment:** {lib.comment if lib.comment else '*empty*'}")

# if st.button('✏️ Edit name or comment', key='edit_lib'):
#     st.switch_page(page=pages.edit_lib, query_params={IdType.LIB: lib.id})
switch_button(
    pages.edit_lib,
    label='✏️ Edit name or comment',
    q_params={IdType.LIB: lib.id},
)

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
    # if st.button('➕**Add**', type='tertiary'):
    #     st.switch_page(
    #         pages.new_film_modif,
    #         query_params={IdType.FILM: film.id}
    #     )
    switch_button(pages.new_film_modif, label='➕**Add**', type_='tertiary',
                  q_params={IdType.FILM: film.id})

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
        with st.container(horizontal_alignment='right'):
            switch_button(pages.edit_film,
                          label="✏️ Edit film information",
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
            switch_button(pages.edit_film_layers, label="✏️ Edit layers",
                          q_params={IdType.FILM: film.id})
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
