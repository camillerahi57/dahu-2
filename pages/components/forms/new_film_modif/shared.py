import streamlit as st

from components.forms.base_classes import Form, \
    PausePageRun
from components.forms.new_film_modif.fields import ConstituentCountField, \
    PlasmaFormulaField, PlasmaProportionField, \
    HasPatternField, SelectPatternLabelField, SelectRecipeLabelField
from logic.lab_modelization.db_models import Pattern, IonBeamEtching, \
    PlasmaConstituent, FilmModification, Etching, Recipe
from logic.lab_modelization.other_classes import MixtureConstituent


class EtchingForm(Form):
    def __init__(self, default_etch: Etching|None):

        st.subheader("Recipe")
        recipe_label_fld = SelectRecipeLabelField(
            form_default=None,
            db_default=default_etch.recipe if default_etch else None,
        )

        st.subheader("Pattern")
        pattern_form = PatternForm(default_etch)

        self.recipe_label = recipe_label_fld.value
        self.has_pattern = pattern_form.has_pattern
        self.pattern_label = pattern_form.pattern_label

        super().__init__(fields=[recipe_label_fld], sub_forms=[pattern_form])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_etching(self, film_modif: FilmModification) -> Etching:
        if not self.is_valid:
            raise PausePageRun

        pattern, recipe = None, None

        if self.pattern_label:
            pattern = (Pattern.select()
                       .where(Pattern.label == self.pattern_label)
                       .get())

        if self.recipe_label:
            recipe = (Recipe.select()
                      .where(Recipe.label == self.recipe_label)
                      .get())

        etching = Etching(
            has_a_pattern=self.has_pattern,
            film_modif=film_modif,
            pattern=pattern,
            recipe=recipe,
        )
        return etching


class PatternForm(Form):
    def __init__(self, default_etch: Etching|None):
        has_pattern_fld = HasPatternField(
            form_default=None,
            db_default=default_etch.has_a_pattern
                if default_etch else None,
        )
        if not has_pattern_fld.is_filled:
            raise PausePageRun

        has_pattern = has_pattern_fld.value == HasPatternField.Option.YES
        if has_pattern:
            has_default_pattern = default_etch and default_etch.pattern
            db_default_label = default_etch.pattern.label \
                if has_default_pattern else None
            pattern_fld = SelectPatternLabelField(
                form_default=None,
                db_default=db_default_label,
            )
        else:
            pattern_fld = None

        self.has_pattern = has_pattern
        self.pattern_label = pattern_fld.value if pattern_fld else None

        super().__init__(fields=[has_pattern_fld, pattern_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


# class DiagramForm(Form):
#     def __init__(self, default_diagram: UserUploadedFile|None):
#         upload_fld = None
#
#         if Sk.USE_DEFAULT_PATTERN not in sess:
#             sess[Sk.USE_DEFAULT_PATTERN] = True
#
#         if default_diagram and sess[Sk.USE_DEFAULT_PATTERN]:
#             default_diagram.retrieve_file_bytes()
#             img_bytes = default_diagram.file_bytes
#             img = Image.open(io.BytesIO(img_bytes))
#             sess[Sk.UPLOADED_FILE] = img
#             sess[Sk.FILE_NAME] = default_diagram.file_name
#             sess[Sk.UPLOADED_AT] = default_diagram.upload_date
#
#         with st.container(horizontal=True):
#             if Sk.UPLOADED_FILE in sess:
#                 img = sess[Sk.UPLOADED_FILE]
#                 st.image(img, width=500)
#                 with st.container():
#                     st.write("**Uploaded pattern ✅**")
#                     if st.button("Delete"):
#                         del sess[Sk.UPLOADED_FILE]
#                         sess[Sk.USE_DEFAULT_PATTERN] = False
#                         st.rerun()
#
#             else:
#                 upload_fld = PatternDiagramField(form_default=None)
#                 if upload_fld.value:
#                     sess[Sk.UPLOADED_FILE] = upload_fld.value.read()
#                     sess[Sk.FILE_NAME] = upload_fld.value.name
#                     sess[Sk.UPLOADED_AT] = datetime.now()
#                     st.rerun()
#
#             if Sk.UPLOADED_FILE in sess:
#                 label_fld = PatternLabelField(
#                     form_default=None,
#                     db_default=default_diagram.label
#                         if default_diagram else None
#                 )
#             else:
#                 label_fld = None
#
#         label = label_fld.value if label_fld else None
#
#         self.file_name = sess.get(Sk.FILE_NAME)
#         self.label = label
#         self.image: bytes = sess.get(Sk.UPLOADED_FILE)
#         self.upload_date = sess.get(Sk.UPLOADED_AT)
#         super().__init__(fields=[upload_fld, label_fld], sub_forms=[])
#
#     def _is_coherent(self) -> tuple[bool, str]:
#         return True, ''
#
#     def to_etching_pattern(self, etching: Etching)\
#             -> EtchingPattern:
#         if not self.is_valid:
#             raise PausePageRun
#
#         pattern = EtchingPattern(
#             label=self.label,
#             file_name=f'{rand_str()}_{self.file_name}',
#             upload_date=self.upload_date,
#             etching=etching,
#         )
#         pattern.file_bytes = self.image
#         return pattern


class ConstituentListForm(Form):
    def __init__(self, default_constituents: list[MixtureConstituent]|None,
                 title: str):
        st.title(title)
        count_fld = ConstituentCountField(
            form_default=1,
            db_default=len(default_constituents) if default_constituents
                else None,
        )
        constituent_forms: list[ConstituentForm] = []
        for i in range(count_fld.value):
            if not default_constituents:
                db_formula, db_proportion = None, None
            else:
                try:
                    db_formula = default_constituents[i].stoichio
                    db_proportion = default_constituents[i].proportion
                except IndexError:
                    db_formula, db_proportion = None, None
            form = ConstituentForm(db_formula, db_proportion, key=f'const_{i}')
            constituent_forms.append(form)

        self.formula_list = [(f.formula, f.proportion)
                             for f in constituent_forms]
        super().__init__(fields=[count_fld], sub_forms=constituent_forms)

    def _is_coherent(self) -> tuple[bool, str]:
        # Making sure all formulas are different:
        formula_set = set(self.formula_list)
        if len(formula_set) != len(self.formula_list):
            return False, 'Some formulas are identical.'
        return True, ''

    def to_plasma(self, ion_beam_etching: IonBeamEtching) \
            -> list[PlasmaConstituent]:
        if not self.is_valid:
            raise PausePageRun
        proportion_sum = sum(prop for _, prop in self.formula_list)
        return [
            PlasmaConstituent.from_stoichio(
                formula,
                proportion / proportion_sum,
                ion_beam_etching)
            for formula, proportion in self.formula_list
        ]


class ConstituentForm(Form):
    def __init__(self, stoichio_from_db: str | None,
                 proportion_from_db: float | None, key: str|int):
        with st.container(horizontal=True):
            formula_fld = PlasmaFormulaField(
                form_default='',
                db_default=stoichio_from_db,
                key=f'formula_{key}',
            )
            proportion_fld = PlasmaProportionField(
                form_default=None,
                db_default=proportion_from_db,
                key=f'proportion_{key}'
            )

        self.formula: str = formula_fld.value
        self.proportion: float = proportion_fld.value

        super().__init__(fields=[formula_fld, proportion_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''
