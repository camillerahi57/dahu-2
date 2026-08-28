import io
from datetime import datetime
from types import SimpleNamespace

import streamlit as st
from PIL import Image
from PIL.ImageFile import ImageFile
from streamlit_cropperjs import st_cropperjs

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_target.fields import MadeAtField, \
    MadeByField, \
    TargetLabelField, CommentField, PhotoUploadField, StoichiometryField, \
    VertexCountField, MillimeterEquivalenceField, PixelEquivalenceField, \
    PhotoDateField, CalibrationFactorField, CoordinateField, PatchCountField, \
    ShapeField, PreviousVersionField, HasCommentField, IsBasePatchField, \
    IsCorrectFigureField, HasCorrectOrientationField
from components.general import sess, cookies
from components.pixel_helper import pixel_helper_button
from logic.constants import SessionKeys as Sk, NEW_TARGET, CookieKeys as Ck
from logic.lab_modelization.db_enums import PixelCoordinateSystem, ShapeType
from logic.lab_modelization.db_models import Target, \
    DeteriorationState, Patch, Vertex, TargetPhoto
from logic.math_tools import VertexList, Disc, Point, points_are_collinear
from logic.units import ur, to_db_unit
from logic.utils import get_file_extension


class BasicInfoForm(Form):
    def __init__(self, default_target: Target = None):
        col1, col2 = st.columns(2)
        with col1:
            made_on_fld = MadeAtField(
                form_default=None,
                db_default=default_target.made_on
                    if default_target else None,
            )
        with col2:
            email_fld = MadeByField(
                form_default=cookies.get(Ck.LAST_EMAIL_USED),
                db_default=default_target.made_by_email
                    if default_target else None,
            )
        target_label_fld = TargetLabelField(
            form_default='',
            db_default=default_target.label
                if default_target else None,
        )

        if default_target is None:
            previous_version_name = None
        elif default_target.previous_version is None:
            previous_version_name = NEW_TARGET
        else:
            previous_version_name = default_target.previous_version.label
        previous_version_fld = PreviousVersionField(
            form_default=previous_version_name
        )

        previous_name = previous_version_fld.value
        if previous_name == NEW_TARGET or not previous_version_fld.is_filled:
            built_from = None
        else:
            built_from = Target.from_label(previous_name)

        self.made_on = made_on_fld.value
        self.made_by_email = email_fld.value
        self.label = target_label_fld.value
        self.built_from = built_from
        self.default_target = default_target

        super().__init__(
            fields=[made_on_fld, email_fld, target_label_fld,
                    previous_version_fld],
            sub_forms=[]
        )

    def _is_coherent(self) -> tuple[bool, str]:
        default, built_from = self.default_target, self.built_from
        if default is not None and built_from is not None:
            if default.id == built_from.id:
                return False, ("Target cannot have itself as a built-from "
                               "target.")
        return True, ''

    def to_target(self, is_archived: bool, id_: int = None) -> Target:
        if not self.is_valid:
            raise PausePageRun

        target = Target(
            made_on=self.made_on,
            made_by_email=self.made_by_email,
            label=self.label,
            previous_version=self.built_from,
            is_archived=is_archived,
        )
        if id_ is not None:
            target.id = id_

        return target


class PixelEquivalenceForm(Form):
    def __init__(self, target_img: ImageFile,
                 default_state: DeteriorationState | None):
        if default_state:
            default_db_length = to_db_unit(100 * ur.mm)  # Only ratio is
            # stored in DB, so we arbitrarily chose a length to show it's
            # equivalent in pixels.
        else:
            default_db_length = None

        with st.container(horizontal=True, vertical_alignment='top'):
            st.write("_You can use the following tool:_")
            pixel_helper_button(target_img, 'px_equivalence')

            with st.container(width=150):
                millimeter_fld = MillimeterEquivalenceField(
                    form_default=None,
                    db_default=default_db_length
                )

            with st.container(width=150):
                pixel_fld = PixelEquivalenceField(
                    form_default=None,
                    db_default=None
                        if default_state is None
                        else default_db_length / default_state.length_per_px
                )

        if millimeter_fld.is_valid and pixel_fld.is_valid:
            length = millimeter_fld.in_db_unit
            pixels = pixel_fld.value
            length_per_px = length / pixels
        else:
            length_per_px = None

        self.ratio = length_per_px

        super().__init__(
            fields=[millimeter_fld, pixel_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


class UploadAndCropForm(Form):
    def __init__(self, default_state: DeteriorationState | None):  # noqa
        self._seed_default_photo_if_needed(default_state)

        if Sk.CROPPED_TARGET_IMG in sess:
            self._init_from_cropped_image()  # super().__init__ called here.
            return

        if Sk.UPLOADED_TARGET_IMG in sess:
            self._show_cropper()
            raise PausePageRun

        self._show_upload_field()
        raise PausePageRun

    @staticmethod
    def _seed_default_photo_if_needed(default_state):
        """If we have a default state and haven't opted out, try to preload
        its photo into session state so the user doesn't have to upload."""
        if default_state is None:
            return
        if Sk.USE_DEFAULT_TARGET_PIC not in sess:
            sess[Sk.USE_DEFAULT_TARGET_PIC] = True
        if not sess[Sk.USE_DEFAULT_TARGET_PIC]:
            return

        path = default_state.photos[0].get_path()
        try:
            img = Image.open(path)
        except FileNotFoundError:
            sess[Sk.USE_DEFAULT_TARGET_PIC] = False
            return

        sess[Sk.CROPPED_TARGET_IMG] = img
        sess[Sk.UPLOADED_TARGET_IMG] = img.tobytes()
        sess[Sk.IMG_FILE_NAME] = default_state.photos[0].original_file_name

    def _init_from_cropped_image(self):
        """A cropped image exists: show its preview and build the form
        fields."""
        cropped_img = sess[Sk.CROPPED_TARGET_IMG]

        container = st.container(
            border=True, horizontal=True, vertical_alignment='center',
            width='content')
        with container:
            aspect_ratio = cropped_img.height / cropped_img.width
            thumbnail_w = 300
            thumbnail_h = round(thumbnail_w * aspect_ratio)
            st.image(cropped_img.resize((thumbnail_w, thumbnail_h)))
            with st.container():
                st.write("**Target cropped ✅**")
                if st.button("❌ Delete photo"):
                    del sess[Sk.CROPPED_TARGET_IMG]
                    del sess[Sk.UPLOADED_TARGET_IMG]
                    sess[Sk.USE_DEFAULT_TARGET_PIC] = False
                    st.rerun()

        has_correct_orientation_fld = HasCorrectOrientationField(
            key='correct_orientation', form_default=False)

        self.cropped_target_img: ImageFile = cropped_img
        self.file_name = sess[Sk.IMG_FILE_NAME]
        super().__init__([has_correct_orientation_fld], [])

    @staticmethod
    def _show_cropper():
        """An image was uploaded but not cropped yet: run the cropper UI."""
        photo = sess[Sk.UPLOADED_TARGET_IMG]
        st.warning("**Keep only what you think is relevant in the image.**")
        cropped_pic = st_cropperjs(
            pic=photo, btn_text="Select target", key=Sk.CROPPED_PIC)
        if cropped_pic:
            sess[Sk.CROPPED_TARGET_IMG] = Image.open(io.BytesIO(cropped_pic))
            st.rerun()
        if st.button("Delete"):
            del sess[Sk.UPLOADED_TARGET_IMG]
            st.rerun()

    @staticmethod
    def _show_upload_field():
        """Nothing uploaded yet: show the file uploader."""
        photo_upload_fld = PhotoUploadField(form_default=None)
        if photo_upload_fld.value:
            sess[Sk.UPLOADED_TARGET_IMG] = photo_upload_fld.value.read()
            sess[Sk.IMG_FILE_NAME] = photo_upload_fld.file_name
            st.rerun()

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


class StateForm(Form):
    def __init__(self, target_date: datetime,
                 default_state: DeteriorationState | None):
        db_has_comment = None
        if default_state:
            if default_state.comment != '':
                db_has_comment = HasCommentField.Option.YES
            else:
                db_has_comment = HasCommentField.Option.NO

        photo_upload_form = UploadAndCropForm(default_state)
        target_img = photo_upload_form.cropped_target_img

        date_fld = PhotoDateField(
            form_default=None,
            db_default=None
                if default_state is None
                else default_state.date
        )

        st.divider()
        pixel_equivalence_form = PixelEquivalenceForm(target_img, default_state)

        st.divider()
        calibration_fld = CalibrationFactorField(
            form_default=0.,
            db_default=None
                if default_state is None
                else default_state.calibration_factor_comment
        )
        st.divider()
        st.write("**Any comment about this target?**")
        has_comment_fld = HasCommentField(
            form_default=None,
            db_default=db_has_comment
        )
        if not has_comment_fld.is_valid:
            raise PausePageRun
        if has_comment_fld.value == HasCommentField.Option.YES:
            comment_fld = CommentField(
                form_default='',
                db_default=None if default_state is None
                    else default_state.comment
            )
            comment = comment_fld.value
        else:
            comment_fld = None
            comment = ''

        self.length_per_px = pixel_equivalence_form.ratio
        self.target_img = target_img

        self.img_format = get_file_extension(photo_upload_form.file_name)
        buffer = io.BytesIO()
        target_img.save(buffer, format=self.img_format)
        self.img_bytes = buffer.getvalue()

        self.photo_file_name = photo_upload_form.file_name
        self.state_date = date_fld.value
        self.calibration_factor = calibration_fld.value
        self.comment = comment
        self.target_date = target_date

        super().__init__(
            fields=[date_fld, calibration_fld, comment_fld, has_comment_fld],
            sub_forms=[photo_upload_form, pixel_equivalence_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        if self.state_date < self.target_date:
            return False, ('Picture date cannot be anterior to the date '
                           'the target was made.')
        return True, ''

    def to_deterioration_state(self, target: Target, email: str = None) \
            -> DeteriorationState:
        if not self.is_valid:
            raise PausePageRun
        coord_system = PixelCoordinateSystem.PLOTLY
        made_by_email = target.made_by_email if email is None else email
        state = DeteriorationState(
            date=self.state_date,
            length_per_px=self.length_per_px,
            calibration_factor_comment=self.calibration_factor,
            comment=self.comment,
            pixel_coordinate_system=coord_system,
            target=target,
            made_by_email=made_by_email,
        )
        photo_label = f'{target.label}_{self.state_date:%Y-%m-%d_%H-%M-%S}'
        photo_upload = TargetPhoto(
            label=photo_label,
            internal_file_name=TargetPhoto.new_internal_file_name(
                photo_label, self.photo_file_name),
            original_file_name=self.photo_file_name,
            upload_date=datetime.now(),
            target_state=state,
        )
        photo_upload.file_bytes = self.img_bytes
        state.photos = [photo_upload]
        return state


class XYCoordinatesForm(Form):
    def __init__(self, key: str | int, default_vertex: Vertex | None):
        if default_vertex:
            x = round(default_vertex.pixel_x)
            y = round(default_vertex.pixel_y)
            couple = str((x, y)).removeprefix('(').removesuffix(')')
        else:
            couple = ''
        coord_fld = CoordinateField(key, form_default=str(couple))
        if coord_fld.is_valid:
            self.x, self.y = eval(coord_fld.value)
        else:
            self.x, self.y = None, None
        super().__init__(fields=[coord_fld], sub_forms=[], )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''


class DiscPatchForm(Form):
    def __init__(self, key: str, target_img: ImageFile,
                 default_patch: Patch | None):
        st.write("Arbitrarily choose 3 points that are far apart "
                 "on the disc circumference:")

        class Default(SimpleNamespace):
            vertex1 = None
            vertex2 = None
            vertex3 = None

        if default_patch:
            vertices = default_patch.vertices
            vertex_count = len(vertices)
            Default.vertex1 = vertices[0]
            Default.vertex2 = vertices[vertex_count // 3]
            Default.vertex3 = vertices[vertex_count * 2 // 3]

        with st.container(horizontal=True, gap='xxsmall'):
            pixel_helper_button(target_img, f'disc_px_select_{key}')
            point_1_form = XYCoordinatesForm(
                key=f'disc_1_{key}',
                default_vertex=Default.vertex1,
            )
            point_2_form = XYCoordinatesForm(
                key=f'disc_2_{key}',
                default_vertex=Default.vertex2,
            )
            point_3_form = XYCoordinatesForm(
                key=f'disc_3_{key}',
                default_vertex=Default.vertex3,
            )

        self.pt_forms = [point_1_form, point_2_form, point_3_form]
        self.point_1 = Point(point_1_form.x, point_1_form.y)
        self.point_2 = Point(point_2_form.x, point_2_form.y)
        self.point_3 = Point(point_3_form.x, point_3_form.y)

        super().__init__(
            fields=[],
            sub_forms=[point_1_form, point_2_form, point_3_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        distinct_points = {self.point_1, self.point_2, self.point_3}
        valid_coords = all(f.is_valid for f in self.pt_forms)
        if valid_coords:
            if len(distinct_points) < 3:
                return False, 'Circumference points must be distinct.'
            if points_are_collinear(self.point_1, self.point_2, self.point_3):
                return False, 'Circumference points cannot be collinear.'
        return True, ''


class PolygonPatchForm(Form):
    def __init__(self, key: str, target_img: ImageFile,
                 default_patch: Patch | None):
        default_vertices = None if default_patch is None \
            else default_patch.vertices

        with st.container(horizontal=True, vertical_alignment='center'):
            vertex_count_fld = VertexCountField(
                key,
                form_default=3,
                db_default=None if default_patch is None
                    else len(default_patch.vertices)
            )

        xy_forms: list[XYCoordinatesForm] = []
        with st.container(horizontal=True, vertical_alignment='top'):
            pixel_helper_button(target_img, f'poly_px_select_{key}')
            for i in range(vertex_count_fld.value):
                if default_vertices is not None and i < len(default_vertices):
                    default_vertex = default_vertices[i]
                else:
                    default_vertex = None
                default_vertex: Vertex|None
                xy_form = XYCoordinatesForm(key=f'poly_{key}_{i}',
                                            default_vertex=default_vertex)
                xy_forms.append(xy_form)

        vertices = []
        for form in xy_forms:
            vertices.append((form.x, form.y))

        self.vertices: VertexList = vertices
        self.xy_forms = xy_forms

        super().__init__(
            fields=[vertex_count_fld],
            sub_forms=xy_forms,
        )

    def _is_coherent(self) -> tuple[bool, str]:
        distinct_points = set(self.vertices)
        if len(distinct_points) < 3 and all(f.is_valid for f in self.xy_forms):
            return False, 'Vertices must be distinct. Some points are equal.'
        return True, ''


class PatchForm(Form):
    def __init__(self, key: str, target_img: ImageFile,
                 default_patch: Patch | None,
                 is_first_patch: bool, stack_idx: int):
        if default_patch is None:
            default_shape = None
        elif len(default_patch.vertices) > 100:
            default_shape = ShapeType.DISC
        else:
            default_shape = ShapeType.POLYGON

        with st.container(border=True, width=99999):
            is_base_patch_fld = IsBasePatchField(
            f'is_base_{key}',
                form_default=False,
                db_default=is_first_patch if default_patch else False,
                # We assume that the first patch is the base patch when
                # editing an existing target.
            )
            with st.container(horizontal=True):
                st.write("Shape:")
                shape_fld = ShapeField(
                    key,
                    form_default=default_shape
                )
                stoichio_fld = StoichiometryField(
                    key=key,
                    form_default='',
                    db_default=None if default_patch is None
                        else default_patch.stoichio_str()
                )

            shape = shape_fld.value

            match shape:
                case ShapeType.DISC:
                    form = DiscPatchForm(key, target_img, default_patch)
                case ShapeType.POLYGON:
                    form = PolygonPatchForm(key, target_img, default_patch)
                case _:
                    form = None

            self.form = form
            self.shape = shape
            self.stoichio = stoichio_fld.value
            self.stack_idx = stack_idx
            self.updated_patch = default_patch
            self.is_base_patch = is_base_patch_fld.value

            super().__init__([shape_fld, stoichio_fld, is_base_patch_fld],
                             [form])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''

    def to_patch_or_none(self, state: DeteriorationState) -> Patch | None:
        if not self.is_valid or self.shape not in ShapeType:
            return None

        return self.to_patch(state)

    def to_patch(self, state: DeteriorationState)\
            -> Patch | None:
        if not self.is_valid:
            raise PausePageRun
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
                stack_idx=self.stack_idx,
                deterioration_state=state,
            )
        elif self.shape == ShapeType.POLYGON:
            form: PolygonPatchForm = self.form
            return Patch.from_polygon(
                stoichio_str=self.stoichio,
                vertices=form.vertices,
                stack_idx=self.stack_idx,
                deterioration_state=state,
            )
        else:
            raise RuntimeError(f'Invalid shape {self.shape}.')


class PatchListForm(Form):
    def __init__(self, target_img: ImageFile,
                 default_state: DeteriorationState | None):
        default_patches = None if default_state is None \
            else default_state.patches

        st.subheader('Patches')
        with st.container(horizontal=True, vertical_alignment='center'):
            patch_count_fld = PatchCountField(
                form_default=0,
                db_default=None if default_state is None
                    else len(default_state.patches)
            )
        patch_count = patch_count_fld.value
        if not patch_count_fld.is_valid:
            raise PausePageRun

        st.divider(width=50)
        patch_forms: list[PatchForm] = []
        for i in range(patch_count):
            if default_patches is not None and i < len(default_patches):
                default_state = default_patches[i]
            else:
                default_state = None
            default_state: Patch | None
            patch_form = PatchForm(f'{i}', target_img,
                                   default_patch=default_state,
                                   is_first_patch=(i==0),
                                   stack_idx=i)
            patch_forms.append(patch_form)

        self.patch_forms = patch_forms

        super().__init__(fields=[patch_count_fld], sub_forms=self.patch_forms)

    def _is_coherent(self) -> tuple[bool, str]:
        base_patch_count = len([f for f in self.patch_forms if f.is_base_patch])
        zero_patch = len(self.patch_forms) == 0
        if base_patch_count != 1 and not zero_patch:
            return False, (f"There must be exactly one *base* patch. "
                           f"Got: {base_patch_count}.")
        if not zero_patch and not self.patch_forms[0].is_base_patch:
            return False, ("Base patch must be the bottom one "
                           "(first in the list).")
        return True, ''

    def to_patches(self, state: DeteriorationState) \
            -> list[Patch | None]:
        return [form.to_patch_or_none(state)
                for form in self.patch_forms]


class DeteriorationStateForm(Form):
    def __init__(self, target: Target, email: str = None,
                 default_state: DeteriorationState = None):
        state_info_form = StateForm(target.made_on,
                                    default_state=default_state)
        st.divider()
        state = state_info_form.to_deterioration_state(target, email)
        target.states = [state]

        patch_list_form = PatchListForm(state_info_form.target_img,
                                        default_state=default_state)
        all_patches = patch_list_form.to_patches(state)
        filled_patches = [p for p in all_patches if p is not None]
        state.patches = filled_patches

        with st.container(horizontal=True, vertical_alignment='top'):
            patch_fig = state.to_figure()
            st.plotly_chart(patch_fig)

        is_correct_fld = IsCorrectFigureField(form_default=False)

        st.divider()
        self.target = target
        self.target_img = state_info_form.target_img
        self.all_patches = all_patches
        self.filled_patches = filled_patches
        self.state = state

        super().__init__(
            fields=[is_correct_fld],
            sub_forms = [state_info_form, patch_list_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        missing_patch_count = len(self.all_patches) - len(self.filled_patches)
        if missing_patch_count > 0:
            return False, (f"Please enter data for all patches. "
                           f"{missing_patch_count} are missing")
        return True, ''


class RootForm(Form):
    def __init__(self):
        basic_info_form = BasicInfoForm()
        target = basic_info_form.to_target(is_archived=False)

        state_form = DeteriorationStateForm(target)

        self.target = target
        self.target_img = state_form.target_img

        super().__init__(
            fields=[],
            sub_forms=[basic_info_form, state_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''
