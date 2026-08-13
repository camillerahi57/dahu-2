import streamlit as st

from components.forms.base_classes import Form, \
    PausePageRun, FileUploadForm
from components.forms.new_film_modif.fields import ConstituentCountField, \
    PlasmaFormulaField, PlasmaProportionField, \
    HasPatternField
from logic.lab_modelization.db_models import EtchingPattern, IonBeamEtching, \
    PlasmaConstituent, FilmModification, Etching, EtchingRecipe
from logic.lab_modelization.other_classes import MixtureConstituent


class EtchingForm(Form):
    def __init__(self, default_etch: Etching|None):
        st.subheader("Recipe")
        if default_etch and default_etch.recipes:
            default_recipe = default_etch.recipes[0]
        else:
            default_recipe = None
        recipe_form = FileUploadForm(default_recipe, key='recipe_form')

        st.subheader("Pattern")

        pattern_form = EtchingPatternForm(default_etch)

        self.recipe_form = recipe_form
        self.pattern_form = pattern_form

        super().__init__(fields=[], sub_forms=[recipe_form, pattern_form])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_etching(self, film_modif: FilmModification) -> Etching:
        if not self.is_valid:
            raise PausePageRun

        etching = Etching(
            has_a_pattern=self.pattern_form.has_pattern,
            film_modif=film_modif,
        )

        if self.recipe_form.file_provided:
            recipe_upload = self.recipe_form.to_user_upload()
            recipe = EtchingRecipe(
                label=recipe_upload.label,
                file_name=recipe_upload.file_name,
                upload_date=recipe_upload.upload_date,
                etching=etching,
            )
            recipe.file_bytes = recipe_upload.file_bytes
        else:
            recipe = None

        pattern_form = self.pattern_form
        if (pattern_form.diagram_form
            and pattern_form.diagram_form.file_provided):

            pattern_upload = self.pattern_form.diagram_form.to_user_upload()
            pattern = EtchingPattern(
                label=pattern_upload.label,
                file_name=pattern_upload.file_name,
                upload_date=pattern_upload.upload_date,
                etching=etching,
            )
            pattern.file_bytes = pattern_upload.file_bytes
        else:
            pattern = None

        if pattern:
            etching.patterns = [pattern]
        if recipe:
            etching.recipes = [recipe]

        return etching


class EtchingPatternForm(Form):
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
            if default_etch and default_etch.patterns:
                default_pattern = default_etch.patterns[0]
            else:
                default_pattern = None
            diagram_form = FileUploadForm(default_pattern, key='pattern_form')
        else:
            diagram_form = None

        self.has_pattern = has_pattern
        self.diagram_form = diagram_form

        super().__init__(fields=[has_pattern_fld], sub_forms=[diagram_form])

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
