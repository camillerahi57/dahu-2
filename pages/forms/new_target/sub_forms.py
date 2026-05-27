import io
from datetime import datetime

import streamlit as st
from PIL import Image
from PIL.ImageFile import ImageFile
from streamlit_cropperjs import st_cropperjs

from components.pixel_selector import pixel_selector_button
from forms.new_target.fields import MadeAtField, ExperimenterEmailField, \
    TargetNameField, CommentField, PhotoUploadField, StoichiometryField, \
    NbOfVertexField, MillimeterEquivalenceField, PixelEquivalenceField, \
    PhotoDateField, CalibrationFactorField, CoordinateField, NbOfPatchField, \
    ShapeField, PreviousVersionField
from forms.shared2 import Form, StopPageLoad
from logic.constants import SessionKeys as Sk, NEW_TARGET
from logic.db_enums import PixelCoordinateSystem, ShapeType
from logic.functions import replace_file_name_extension
from logic.lab_modelization.db_models import Target, \
    DeteriorationState, Patch
from logic.math_tools import VertexList, Disc, Point, points_are_collinear
from logic.units import ur


class BasicInfoForm(Form):
    def __init__(self):
        col1, col2 = st.columns(2)
        with col1:
            made_on_fld = MadeAtField()
        with col2:
            email_fld = ExperimenterEmailField()
        target_name_fld = TargetNameField()

        previous_version_fld = PreviousVersionField()
        previous_name = previous_version_fld.value
        if previous_name == NEW_TARGET or not previous_version_fld.is_filled():
            previous_version = None
        else:
            previous_version = Target.from_name(previous_name)


        self.made_on = made_on_fld.value
        self.made_by_email = email_fld.value
        self.physical_name = target_name_fld.value
        self.previous_version = previous_version

        super().__init__(
            fields=[made_on_fld, email_fld, target_name_fld,
                    previous_version_fld],
            sub_forms=[]
        )

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''

    def to_target(self) -> Target:
        if not self.is_valid:
            raise StopPageLoad

        return Target(
            made_on=self.made_on,
            made_by_email=self.made_by_email,
            physical_name=self.physical_name,
            previous_version=self.previous_version,
        )


class PixelEquivalenceForm(Form):
    def __init__(self, target_img: ImageFile):
        st.subheader("Millimeter to pixel conversion")
        with st.container(horizontal=True, vertical_alignment='top'):
            st.write("_You can use the following tool:_")
            pixel_selector_button(target_img, 'px_equivalence')
            with st.container(width=150):
                millimeter_fld = MillimeterEquivalenceField()
            with st.container(width=150):
                pixel_fld = PixelEquivalenceField()
        if millimeter_fld.is_valid and pixel_fld.is_valid:
            millimeters = millimeter_fld.value * ur.millimeter
            pixels = pixel_fld.value * ur.pixel
            px_to_real_length_factor = (millimeters / pixels).magnitude

        else:
            px_to_real_length_factor = None
        self.factor = px_to_real_length_factor
        super().__init__(
            fields=[millimeter_fld, pixel_fld],
            sub_forms=[],
        )

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''


class UploadAndCropForm(Form):
    def __init__(self):
        sess = st.session_state

        if Sk.CROPPED_TARGET_IMG in sess:
            container = st.container(
                border=True, horizontal=True, vertical_alignment='center',
            width='content')
            with container:
                cropped_img = sess[Sk.CROPPED_TARGET_IMG]
                max_width = 300
                aspect_ratio = cropped_img.height / cropped_img.width
                if aspect_ratio > 1:
                    width = int(max_width / aspect_ratio)
                else:
                    width = max_width
                st.image(cropped_img, width=width)
                with st.container():
                    st.write("**Target cropped ✅**")
                    if st.button("Delete"):
                        del sess[Sk.CROPPED_TARGET_IMG]
                        del sess[Sk.UPLOADED_TARGET_IMG]
                        st.rerun()
            self.cropped_target_img: ImageFile = sess[Sk.CROPPED_TARGET_IMG]
            self.file_name = sess[Sk.TARGET_IMG_NAME]
            super().__init__([], [])

        elif Sk.UPLOADED_TARGET_IMG in sess:
            photo = sess[Sk.UPLOADED_TARGET_IMG]
            cropped_pic = st_cropperjs(
                pic=photo, btn_text="Select target", key=Sk.CROPPED_PIC)
            if cropped_pic:
                target_img = Image.open(io.BytesIO(cropped_pic))
                sess[Sk.CROPPED_TARGET_IMG] = target_img
                st.rerun()
            if st.button("Delete"):
                del sess[Sk.UPLOADED_TARGET_IMG]
                st.rerun()
            raise StopPageLoad

        else:
            photo_upload_fld = PhotoUploadField()
            if photo_upload_fld.value:
                sess[Sk.UPLOADED_TARGET_IMG] = photo_upload_fld.value.read()
                sess[Sk.TARGET_IMG_NAME] = photo_upload_fld.create_file_name()
                st.rerun()
            raise StopPageLoad

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''



class DeteriorationStateForm(Form):
    def __init__(self, target_date: datetime):
        photo_upload_form = UploadAndCropForm()
        target_img = photo_upload_form.cropped_target_img
        date_fld = PhotoDateField()

        st.divider()
        pixel_equivalence_form = PixelEquivalenceForm(target_img)

        st.divider()
        calibration_fld = CalibrationFactorField()
        comment_fld = CommentField()

        self.px_to_real_length_factor = pixel_equivalence_form.factor
        self.target_img = target_img
        self.photo_file_name = photo_upload_form.file_name
        self.state_date = date_fld.value
        self.calibration_factor = calibration_fld.value
        self.comment = comment_fld.value
        self.target_date = target_date

        super().__init__(
            fields=[date_fld, calibration_fld, comment_fld],
            sub_forms=[photo_upload_form, pixel_equivalence_form],
        )

    def _check_coherence(self) -> tuple[bool, str]:
        if self.state_date < self.target_date:
            return False, ('Picture date cannot be anterior to the date '
                           'the target was made.')
        return True, ''

    def to_deterioration_state(self, target: Target)\
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


class XYCoordinatesForm(Form):
    def __init__(self, key: str | int):
        coord_fld = CoordinateField(key)
        if coord_fld.is_valid:
            self.x, self.y = eval(coord_fld.value)
        else:
            self.x, self.y = None, None
        super().__init__(fields=[coord_fld], sub_forms=[], )

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''


class DiscPatchForm(Form):
    def __init__(self, key: str, target_img: ImageFile):
        st.write("Arbitrarily choose 3 points that are far apart "
                 "on the disc circumference:")

        with st.container(horizontal=True, gap='xxsmall'):
            pixel_selector_button(target_img, f'disc_px_select_{key}')
            point_1_form = XYCoordinatesForm(key=f'disc_1_{key}')
            point_2_form = XYCoordinatesForm(key=f'disc_2_{key}')
            point_3_form = XYCoordinatesForm(key=f'disc_3_{key}')

        self.pt_forms = [point_1_form, point_2_form, point_3_form]
        self.point_1 = Point(point_1_form.x, point_1_form.y)
        self.point_2 = Point(point_2_form.x, point_2_form.y)
        self.point_3 = Point(point_3_form.x, point_3_form.y)

        super().__init__(
            fields=[],
            sub_forms=[point_1_form, point_2_form, point_3_form],
        )

    def _check_coherence(self) -> tuple[bool, str]:
        distinct_points = {self.point_1, self.point_2, self.point_3}
        valid_coords = all(f.is_valid for f in self.pt_forms)
        if valid_coords:
            if len(distinct_points) < 3:
                return False, 'Circumference points must be distinct.'
            if points_are_collinear(self.point_1, self.point_2, self.point_3):
                return False, 'Circumference points cannot be collinear.'
        return True, ''


class PolygonPatchForm(Form):
    def __init__(self, key: str, target_img: ImageFile):
        with st.container(horizontal=True, vertical_alignment='center'):
            vertex_nb_fld = NbOfVertexField(key)

        xy_forms: list[XYCoordinatesForm] = []
        with st.container(horizontal=True, vertical_alignment='top'):
            pixel_selector_button(target_img, f'poly_px_select_{key}')
            for i in range(vertex_nb_fld.value):
                xy_forms.append(XYCoordinatesForm(key=f'poly_{i}'))

        vertices = []
        for form in xy_forms:
            vertices.append((form.x, form.y))

        self.vertices: VertexList = vertices
        self.xy_forms = xy_forms

        super().__init__(
            fields=[vertex_nb_fld],
            sub_forms=xy_forms,
        )

    def _check_coherence(self) -> tuple[bool, str]:
        distinct_points = set(self.vertices)
        if len(distinct_points) < 3 and all(f.is_valid for f in self.xy_forms):
            return False, 'Vertices must be distinct. Some points are equal.'
        return True, ''


class PatchForm(Form):
    def __init__(self, key: str, target_img: ImageFile):
        with st.container(border=True, width=99999):
            with st.container(horizontal=True):
                st.write("Shape:")
                shape_fld = ShapeField(key)
                stoichio_fld = StoichiometryField(key=key)

            shape = shape_fld.value

            match shape:
                case ShapeType.DISC:
                    form = DiscPatchForm(key, target_img)
                case ShapeType.POLYGON:
                    form = PolygonPatchForm(key, target_img)
                case _:
                    form = None

            self.form = form
            self.shape = shape
            self.stoichio = stoichio_fld.value

            if form is None:
                super().__init__([shape_fld, stoichio_fld], [])
            else:
                super().__init__([shape_fld, stoichio_fld], [form])

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''

    def to_patch_or_none(self, state: DeteriorationState) -> Patch | None:
        if not self.is_valid or self.shape not in ShapeType:
            return None

        return self.to_patch(state)

    def to_patch(self, state: DeteriorationState):
        if not self.is_valid:
            raise StopPageLoad
        if self.shape == ShapeType.DISC:
            form: DiscPatchForm = self.form
            disc = Disc.from_circumference_points(
                form.point_1,
                form.point_2,
                form.point_3,
            )
            return Patch.from_polygon(
                stoichio_str=self.stoichio,
                vertices=disc.to_vertices(),
                stack_idx=42,
                deterioration_state=state,
            )
        elif self.shape == ShapeType.POLYGON:
            form: PolygonPatchForm = self.form
            return Patch.from_polygon(
                stoichio_str=self.stoichio,
                vertices=form.vertices,
                stack_idx=42,
                deterioration_state=state,
            )
        else:
            raise RuntimeError(f'Invalid shape {self.shape}.')




class PatchListForm(Form):
    def __init__(self, target_img: ImageFile):
        st.subheader('Patches')
        with st.container(horizontal=True, vertical_alignment='center'):
            # disc_nb_fld = NbOfDiscField()
            # polygon_nb_fld = NbOfPolygonField()
            patch_nb_fld = NbOfPatchField()
        # disc_nb, polygon_nb = disc_nb_fld.value, polygon_nb_fld.value
        patch_nb = patch_nb_fld.value
        if not patch_nb_fld.is_valid:
            raise StopPageLoad

        self.patch_forms = [PatchForm(f'{i}', target_img)
                       for i in range(patch_nb)]

        super().__init__(fields=[patch_nb_fld], sub_forms=self.patch_forms)

    def _check_coherence(self) -> tuple[bool, str]:
        return True, ''

    def to_patches(self, state: DeteriorationState) \
            -> list[Patch | None]:
        return [form.to_patch_or_none(state)
                for form in self.patch_forms]


class RootForm(Form):
    def __init__(self):
        basic_info_form = BasicInfoForm()
        target = basic_info_form.to_target()

        state_form = DeteriorationStateForm(target.made_on)
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
        self.target = target
        self.target_img = state_form.target_img
        self.all_patches = all_patches
        self.filled_patches = filled_patches

        super().__init__(
            fields=[],
            sub_forms=[basic_info_form, state_form, patch_list_form],
        )


    def _check_coherence(self) -> tuple[bool, str]:
        missing_patch_nb = len(self.all_patches) - len(self.filled_patches)
        if missing_patch_nb > 0:
            return False, (f"Please enter data for all patches. "
                           f"{missing_patch_nb} are missing")
        return True, ''
