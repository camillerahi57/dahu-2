import streamlit as st

from components.forms.new_deterioration_state.fields import MadeAtField, \
    ExperimenterEmailField, \
    CommentField, CalibrationFactorField
from components.forms.new_target.sub_forms import PixelEquivalenceForm, UploadAndCropForm,\
    PatchListForm
from components.forms.shared2 import Form, StopPageLoad
from logic.db_enums import PixelCoordinateSystem
from logic.functions import replace_file_name_extension
from logic.lab_modelization.db_models import Target, \
    DeteriorationState


class DeteriorationStateForm(Form):
    def __init__(self):
        col1, col2 = st.columns(2)
        with col1:
            made_on_fld = MadeAtField()
        with col2:
            email_fld = ExperimenterEmailField()

        photo_upload_form = UploadAndCropForm()
        target_img = photo_upload_form.cropped_target_img

        st.divider()
        pixel_equivalence_form = PixelEquivalenceForm(target_img)

        st.divider()
        calibration_fld = CalibrationFactorField()
        comment_fld = CommentField()

        self.px_to_real_length_factor = pixel_equivalence_form.factor
        self.target_img = target_img
        self.photo_file_name = photo_upload_form.file_name
        self.calibration_factor = calibration_fld.value
        self.comment = comment_fld.value
        self.state_date = made_on_fld.value
        self.made_by_email = email_fld.value

        super().__init__(
            fields=[made_on_fld, email_fld, calibration_fld, comment_fld],
            sub_forms=[photo_upload_form, pixel_equivalence_form],
        )

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''

    def to_deterioration_state(self, target: Target) \
            -> DeteriorationState:
        if not self.is_valid:
            raise StopPageLoad
        coord_system = PixelCoordinateSystem.X_Y_EQ_W_H_ORIGIN_TOP_LEFT
        photo_file_name = replace_file_name_extension(
            self.photo_file_name, 'png'
        )
        return DeteriorationState(
            date=self.state_date,
            px_to_real_length_factor=self.px_to_real_length_factor,
            photo_file_name=photo_file_name,
            calibration_factor=self.calibration_factor,
            comment=self.comment,
            pixel_coordinate_system=coord_system,
            target=target,
            made_by_email=target.made_by_email,
        )


class RootForm(Form):
    def __init__(self, target: Target):
        state_form = DeteriorationStateForm()
        st.divider()
        state = state_form.to_deterioration_state(target)
        target.states = [state]

        patch_list_form = PatchListForm(state_form.target_img)
        all_patches = patch_list_form.to_patches(state)
        filled_patches = [p for p in all_patches if p is not None]
        state.patches = filled_patches

        with st.container(horizontal=True, vertical_alignment='top'):
            patch_fig = state.to_figure()
            st.plotly_chart(patch_fig)

        st.divider()
        self.target_img = state_form.target_img
        self.state = state
        self.all_patches = all_patches
        self.filled_patches = filled_patches

        super().__init__(
            fields=[],
            sub_forms=[state_form, patch_list_form],
        )

    def _check_coherence(self) -> tuple[bool, str]:
        missing_patch_nb = len(self.all_patches) - len(self.filled_patches)
        if missing_patch_nb > 0:
            return False, (f"Please enter data for all patches. "
                           f"{missing_patch_nb} are missing")
        return True, ''
