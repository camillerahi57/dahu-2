import io
from datetime import datetime
from uuid import uuid4

from PIL import Image

from components.forms.base_classes import Field, FieldType as Ft, Form, \
    PausePageRun
import streamlit as st

from components.forms.new_film_modif.fields import PatternLabelField
from components.streamlit_tools import sess
from logic.constants import SessionKeys as Sk
from logic.lab_modelization.db_models import UserUploadedFile, \
    IonEtchingPattern, IonBeamEtching


class PatternDiagramField(Field):
    type = Ft.OPTIONAL

    def _streamlit_input(self, prefill, key: str):
        return st.file_uploader('Select the pattern image',
                                type=['jpg', 'png', 'svg'], key=key)

    def _validate(self, input_) -> tuple[bool, str]:
        if input_ is None:
            return False, 'Please upload an image of the pattern.'
        return True, ''


class PatternDiagramForm(Form):
    def __init__(self, default_diagram: UserUploadedFile|None):
        upload_fld = None

        if Sk.USE_DEFAULT_PATTERN not in sess:
            sess[Sk.USE_DEFAULT_PATTERN] = True

        if default_diagram and sess[Sk.USE_DEFAULT_PATTERN]:
            default_diagram.retrieve_file_bytes()
            img_bytes = default_diagram.file_bytes
            img = Image.open(io.BytesIO(img_bytes))
            sess[Sk.UPLOADED_FILE] = img
            sess[Sk.FILE_NAME] = default_diagram.file_name
            sess[Sk.UPLOADED_AT] = default_diagram.upload_date

        if Sk.UPLOADED_FILE in sess:
            img = sess[Sk.UPLOADED_FILE]
            st.image(img, width=500)
            with st.container():
                st.write("**Uploaded pattern ✅**")
                if st.button("Delete"):
                    del sess[Sk.UPLOADED_FILE]
                    sess[Sk.USE_DEFAULT_PATTERN] = False
                    st.rerun()

        else:
            upload_fld = PatternDiagramField(form_default=None)
            if upload_fld.value:
                sess[Sk.UPLOADED_FILE] = upload_fld.value.read()
                sess[Sk.FILE_NAME] = upload_fld.value.name
                sess[Sk.UPLOADED_AT] = datetime.now()
                st.rerun()

        label_fld = PatternLabelField(
            form_default=None,
            db_default=default_diagram.label if default_diagram else None
        )

        self.file_name = sess.get(Sk.FILE_NAME)
        self.label = label_fld.value
        self.image: bytes = sess.get(Sk.UPLOADED_FILE)
        self.upload_date = sess.get(Sk.UPLOADED_AT)
        super().__init__(fields=[upload_fld, label_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_ion_etching_pattern(self, etching: IonBeamEtching)\
            -> IonEtchingPattern:
        if not self.is_valid:
            raise PausePageRun
        file_extension = self.file_name.split('.')[-1]

        pattern = IonEtchingPattern(
            label=self.label,
            file_name=f'{uuid4()}.{file_extension}',
            upload_date=self.upload_date,
            file_bytes=self.image,
            etching=etching,
        )
        pattern.file_bytes = self.image
        return pattern