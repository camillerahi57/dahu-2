"""Forms of the "new library" page, ending with `RootForm`.

Nesting on the "new library" page::

    RootForm
    ├── BaseInfoForm      library label and comment
    ├── FilmInfoForm      film label, date, author, substrate
    ├── TargetListForm    targets used for the film
    └── LayerListForm     layer count, then one LayerForm per layer
        └── LayerForm
            ├── LayerIntroForm   general layer data and its targets
            └── MagnetronForm or TriodeForm

`RootForm` turns the validated input into an unsaved `Library` with its
`Film`, `FilmLayer`s and their parts, which the page saves with
`save_with_dependent()`. Parts are the child rows a row owns; a form
attaches them by assigning lists to the parent's backref attributes (a
backref is the attribute on the parent that lists the rows whose
foreign key, i.e. reference column, points to it).

Some of these forms are reused on edit pages, with the existing object
as default so that their fields are prefilled from the DB:
`BaseInfoForm` (edit library), `FilmInfoForm` (edit film), and
`TargetListForm` with `LayerListForm` (edit film layers).

Many builder methods raise `PausePageRun` while the form is invalid.
Every widget has already been drawn by then, so this only hides what
the page would draw next, such as the "Submit" button.
"""

from datetime import datetime
from typing import cast, Any

import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_library.fields import (
    LibLabelField, CommentField, FilmLabelField, MadeOnField,
    MadeByField, SubstrateField, DepositTempField, NominalThicknessField,
    ShadowMaskField, NominalStoichioField, FilmLayerFunctionField,
    SputteringSystemField, DepositDistanceField, DepositAngleField,
    DepositPowerField, DepositDurationField, MagnetronModelField,
    MagnetronGeneratorField, HasActiveCoolingField, RotationSpeedField,
    FilamentCurrentStartField, FilamentCurrentEndField, AnodeCurrentField,
    AnodeVoltageField, CathodeCurrentField, CathodeVoltageField,
    DepositRateField, ArgonFlowField, NitrogenFlowField, PressureField,
    PresputteringThicknessField, LayerCountField, TargetCountField, TargetField,
    TargetChoiceField, ConfirmOrderField, IsCoSputteringField,
)
from logic.constants import SessionKeys as Sk, CookieKeys as Ck
from logic.cookie_init import cookies
from logic.global_variables import sess
from logic.lab_modelization.db_enums import SputteringSystem
from logic.lab_modelization.db_models import Library, Film, FilmLayer, \
    MagnetronSputtering, TriodeSputtering, Substrate, Target, TargetUse, \
    StoichioElement


class BaseInfoForm(Form):
    """Library label and comment, under the page title.

    Used by the "new library" page (through `RootForm`) and by the
    "edit library" page.

    Attributes:
        label: The library label, or None if invalid.
        comment: The comment, or None if empty.
    """

    def __init__(self, default_lib: Library | None):
        """Draw the title "New Library" and the fields.

        The title is drawn on the edit page too.

        Args:
            default_lib: Library whose values prefill the fields (edit
                page), or None.
        """
        st.title('New Library')  # TODO It should be "Edit..." on edit page.
        st.divider()
        lib_label_fld = LibLabelField(
            form_default='',
            db_default=default_lib.label if default_lib else None
        )
        comment_fld = CommentField(
            form_default='',
            db_default=default_lib.comment if default_lib else None
        )

        self.label = lib_label_fld.value
        self.comment = comment_fld.value

        super().__init__(fields=[lib_label_fld, comment_fld], sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''

    def to_library(self, is_archived: bool, id_: int|None = None) -> Library:
        """Build an unsaved `Library` from the input.

        `last_inspected_at` is set to now, also when editing.

        Args:
            is_archived: Value of `Library.is_archived`; the edit page
                passes the old library's value, a new library is not
                archived.
            id_: Id of the library being edited, so that `save()`
                updates that row instead of inserting a new one. None
                for a new library.

        Returns:
            The library, without its film.

        Raises:
            PausePageRun: If the form is invalid.
        """
        if not self.is_valid:
            raise PausePageRun

        lib = Library(
            label=self.label,
            last_inspected_at=datetime.now(),
            comment=self.comment,
            # TODO Passes `hdf5_file_name=None`, which is not a column of
            #   `Library`. Peewee just sets it as a plain attribute that is never
            #   saved. Leftover from an older schema?
            hdf5_file_name=None,
            is_archived=is_archived,
        )
        if id_ is not None:
            lib.id = id_
        return lib


class FilmInfoForm(Form):
    """Film label, deposition date, author email and substrate, side by
    side.

    Used by the "new library" page (through `RootForm`) and by the
    "edit film" page.

    Attributes:
        label: The film label, or None if invalid.
        made_on: The deposition date, or None.
        email: The author's email address, or None if invalid.
        substrate_name: The substrate label, or None.
    """

    def __init__(self, default_film: Film | None):
        """Draw the fields.

        On a new film, the email is prefilled with the last address
        used in this browser (`LAST_EMAIL_USED` cookie; a cookie is a
        small value the browser stores for the site).

        Args:
            default_film: Film whose values prefill the fields (edit
                page), or None.
        """
        with st.container(horizontal=True, vertical_alignment='center'):
            label_fld = FilmLabelField(
                form_default='',
                db_default=default_film.label
                    if default_film else None,
            )
            made_on_fld = MadeOnField(
                form_default=None,
                db_default=default_film.made_on
                    if default_film else None,
            )
            email_fld = MadeByField(
                form_default=cookies.get(Ck.LAST_EMAIL_USED),
                db_default=default_film.made_by_email
                    if default_film else None,
            )
            substrate_fld = SubstrateField(
                form_default=None,
                db_default=default_film.substrate.label
                    if default_film else None,
            )

        self.label = label_fld.value
        self.made_on = made_on_fld.value
        self.email = email_fld.value
        self.substrate_name = substrate_fld.value

        super().__init__(
            fields=[label_fld, made_on_fld, email_fld, substrate_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''

    def add_to_library(self, library: Library):
        """Build the film and attach it as the library's only film.

        Args:
            library: The unsaved library; its `films` backref is set to
                a list of one film.

        Raises:
            PausePageRun: If the form is invalid.
        """
        film = self.to_film(library)
        library.films = [film]

    def to_film(self, library: Library, id_: int|None = None) -> Film:
        """Build an unsaved `Film` (without layers) from the input.

        Loads the chosen substrate from the DB.

        Args:
            library: Library the film belongs to.
            id_: Id of the film being edited, so that `save()` updates
                that row instead of inserting a new one. None for a new
                film.

        Returns:
            The film.

        Raises:
            PausePageRun: If the form is invalid.
        """
        if not self.is_valid:
            raise PausePageRun
        film = Film(
            label=self.label,
            made_on=self.made_on,
            made_by_email=self.email,
            substrate=Substrate.from_label(self.substrate_name),
            library=library,
        )
        if id_ is not None:
            film.id = id_

        return film


class LayerIntroForm(Form):
    """General data of one layer, its target(s) and sputtering system.

    The fields that depend on the sputtering system are in
    `MagnetronForm` or `TriodeForm`, drawn after this one by
    `LayerForm`.

    Attributes:
        deposit_temp: Deposition temperature in K, or None.
        nominal_thickness: Intended thickness in m, or None.
        shadow_mask_descr: Shadow mask description, or None.
        nominal_stoichio: Intended chemical formula, or None.
        layer_function: A `FilmLayerFunction` value, or None.
        sputtering_system: A `SputteringSystem` value, or None.
        target_label: Label of the (first) target, or None.
        target_2_label: Label of the co-sputtering target, or None
            without co-sputtering.
    """

    def __init__(self, default_layer: FilmLayer | None, key: str):
        """Draw the fields side by side.

        A second target field appears when the co-sputtering box is
        ticked. Its options, like the first one's, are the targets
        chosen in `TargetListForm`.

        Args:
            default_layer: Layer whose values prefill the fields (edit
                film layers page), or None.
            key: The layer's index, as a string. It makes the widget
                keys (names Streamlit uses to recognize a widget from
                one rerun to the next) unique across layers.

        Raises:
            NotImplementedError: If `default_layer` has more than two
                targets, which the DB allows but this form can't show.
        """
        no_db_default = default_layer is None
        if default_layer:
            db_default_target_labels = [use.target.label
                                        for use in default_layer.target_uses]
            if len(db_default_target_labels) > 2:
                raise NotImplementedError(
                    "It is possible to have more than two targets in "
                    "co-sputtering in the database, but it's not implemented "
                    "in the user interface.")
        else:
            db_default_target_labels = []
        with st.container(horizontal=True):
            deposit_temp_fld = DepositTempField(
                key=f'deposit_temp_{key}',
                form_default=None,
                db_default=default_layer.deposit_temp if default_layer
                else None
            )
            nominal_thickness_fld = NominalThicknessField(
                key=f'thickness_{key}',
                form_default=None,
                db_default=default_layer.nominal_thickness if default_layer
                else None
            )
            shadow_mask_fld = ShadowMaskField(
                key=f'shadow_mask_{key}',
                form_default='',
                db_default=default_layer.shadow_mask_description
                if default_layer
                else None
            )
            nominal_stoichio_fld = NominalStoichioField(
                key=f'stoichio_{key}',
                form_default='',
                db_default=default_layer.nominal_stoichio_str if default_layer
                else None
            )
            layer_function_fld = FilmLayerFunctionField(
                key=f'function_{key}',
                form_default=None,
                db_default=default_layer.function if default_layer else None
            )
            is_cosputter_fld = IsCoSputteringField(
                key=key,
                form_default=False,
                db_default=len(db_default_target_labels) == 2
            )
            # TODO If an existing
            #   layer has no `TargetUse`, `db_default_target_labels[0]` raises
            #   `IndexError`.
            target_label_fld = TargetChoiceField(
                key=key,
                form_default=None,
                db_default=db_default_target_labels[0] if default_layer
                else None
            )
            if is_cosputter_fld.value:
                if no_db_default or len(db_default_target_labels) < 2:
                    db_co_sputter_target = None
                else:
                    db_co_sputter_target = db_default_target_labels[1]
                # Its own key, distinct from the first target field's.
                target_2_label_fld = TargetChoiceField(
                    key=f'co_sputter_target_{key}',
                    form_default=None,
                    db_default=db_co_sputter_target
                )
                target_2_label = target_2_label_fld.value
            else:
                target_2_label_fld = None
                target_2_label = None
            sputtering_system_fld = SputteringSystemField(
                key=key,
                form_default=None,
                db_default=default_layer.sputtering_system if default_layer
                else None
            )

        self.deposit_temp = deposit_temp_fld.in_db_unit
        self.nominal_thickness = nominal_thickness_fld.in_db_unit
        self.shadow_mask_descr = shadow_mask_fld.value
        self.nominal_stoichio = nominal_stoichio_fld.value
        self.layer_function = layer_function_fld.value
        self.sputtering_system = sputtering_system_fld.value
        self.target_label = target_label_fld.value
        self.target_2_label = target_2_label

        # `nominal_stoichio_fld` is listed twice, while
        # `nominal_thickness_fld` and `target_label_fld` are missing, so
        # these two don't affect `is_valid`.
        super().__init__(
            fields=[deposit_temp_fld, nominal_stoichio_fld, shadow_mask_fld,
                    nominal_stoichio_fld, layer_function_fld, is_cosputter_fld,
                    sputtering_system_fld, target_2_label_fld],
            # TODO nominal_stoichio_fld is passed twice and
            #  nominal_thickness_fld and target_label_fld are left out.
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''


class MagnetronForm(Form):
    """Magnetron sputtering parameters of one layer.

    Attributes:
        deposit_distance: Target-to-substrate distance in m, or None.
        deposit_angle: Deposition angle in rad, or None.
        deposit_power: Generator power in W, or None.
        deposit_duration: Deposition duration in s, or None.
        generator: A `MagnetronSputteringGenerator` value, or None.
        machine_model: A `MagnetronMachineModel` value, or None.
    """

    def __init__(self, default_layer: MagnetronSputtering | None, key: str):
        """Draw the fields side by side.

        On a new layer, the distance is prefilled with 100 mm and the
        angle with 0°.

        Args:
            default_layer: Magnetron row whose values prefill the
                fields (edit film layers page), or None.
            key: The layer's index, as a string. Every field gets the
                same key; that is fine because the widget key also
                contains the field's class name.
        """
        with st.container(horizontal=True):
            deposit_distance_fld = DepositDistanceField(
                key=key,
                form_default=100.,
                db_default=default_layer.deposit_distance if default_layer
                else None
            )
            deposit_angle_fld = DepositAngleField(
                key=key,
                form_default=0.,
                db_default=default_layer.deposit_angle if default_layer
                else None
            )
            deposit_power_fld = DepositPowerField(
                key=key,
                form_default=None,
                db_default=default_layer.deposit_power if default_layer
                else None
            )
            deposit_duration_fld = DepositDurationField(
                key=key,
                form_default=None,
                db_default=default_layer.deposit_duration if default_layer
                else None
            )
            machine_model_fld = MagnetronModelField(
                key=key,
                form_default='',
                db_default=default_layer.machine_model if default_layer
                else None
            )
            generator_fld = MagnetronGeneratorField(
                key=key,
                form_default='',
                db_default=default_layer.generator if default_layer
                else None
            )

        self.deposit_distance = deposit_distance_fld.in_db_unit
        self.deposit_angle = deposit_angle_fld.in_db_unit
        self.deposit_power = deposit_power_fld.in_db_unit
        self.deposit_duration = deposit_duration_fld.in_db_unit
        self.generator = generator_fld.value
        self.machine_model = machine_model_fld.value

        super().__init__(
            fields=[deposit_distance_fld, deposit_angle_fld, deposit_power_fld,
                    deposit_duration_fld, machine_model_fld, generator_fld],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''

    def add_to_layer(self, layer: FilmLayer):
        """Build the magnetron row and attach it to the layer.

        Args:
            layer: The unsaved layer; its `magnetron_sputterings`
                backref is set to a list of one row.

        Raises:
            PausePageRun: If the form is invalid.
        """
        if not self.is_valid:
            raise PausePageRun
        magnetron = MagnetronSputtering(
            deposit_distance=self.deposit_distance,
            deposit_angle=self.deposit_angle,
            deposit_power=self.deposit_power,
            deposit_duration=self.deposit_duration,
            generator=self.generator,
            machine_model=self.machine_model,
            film_layer=layer,
        )
        layer.magnetron_sputterings = [magnetron]


class TriodeForm(Form):
    """Triode sputtering parameters of one layer.

    Attributes:
        active_cooling: Whether the substrate was actively cooled.
        rotation_speed: Substrate rotation speed in rad/s, or None.
        filament_current_start: Filament current at the start in A, or
            None.
        filament_current_end: Filament current at the end in A, or
            None.
        anode_current: Anode current in A, or None.
        anode_voltage: Anode voltage in V, or None.
        cathode_current: Cathode current in A, or None.
        cathode_voltage: Cathode voltage in V, or None.
        deposit_rate: Deposition rate in m/s, or None.
        argon_flow: Argon flow in m³/s, or None.
        nitrogen_flow: Nitrogen flow, or None. Stored as typed (see
            `NitrogenFlowField`).
        pressure: Pressure in Pa, or None.
        deposit_duration: Deposition duration in s, or None.
        presputter_thickness: Presputtering thickness in m, or None.
    """

    def __init__(self, default_layer: TriodeSputtering | None, key: str):
        """Draw the fields side by side.

        On a new layer, active cooling is ticked and the rotation
        speed, anode voltage and cathode voltage are prefilled with
        0 rpm, 80 V and 900 V.

        Args:
            default_layer: Triode row whose values prefill the fields
                (edit film layers page), or None.
            key: The layer's index, as a string. Every field gets the
                same key; that is fine because the widget key also
                contains the field's class name.
        """
        with st.container(horizontal=True, vertical_alignment='center'):
            active_cooling_fld = HasActiveCoolingField(
                key=key,
                form_default=True,
                db_default=default_layer.has_active_cooling if default_layer
                else None
            )
            rot_speed_fld = RotationSpeedField(
                key=key,
                form_default=0.,
                db_default=default_layer.rotation_speed if default_layer
                else None
            )
            filament_current_start_fld = FilamentCurrentStartField(
                key=key,
                form_default=None,
                db_default=default_layer.filament_current_start if default_layer
                else None
            )
            filament_current_end_fld = FilamentCurrentEndField(
                key=key,
                form_default=None,
                db_default=default_layer.filament_current_end if default_layer
                else None

            )
            anode_current_fld = AnodeCurrentField(
                key=key,
                form_default=None,
                db_default=default_layer.anode_current if default_layer
                else None
            )
            anode_voltage_fld = AnodeVoltageField(
                key=key,
                form_default=80.,
                db_default=default_layer.anode_voltage if default_layer
                else None
            )
            cathode_current_fld = CathodeCurrentField(
                key=key,
                form_default=None,
                db_default=default_layer.cathode_current if default_layer
                else None
            )
            cathode_voltage_fld = CathodeVoltageField(
                key=key,
                form_default=900.,
                db_default=default_layer.cathode_voltage if default_layer
                else None
            )
            deposit_rate_fld = DepositRateField(
                key=key,
                form_default=None,
                db_default=default_layer.deposit_rate if default_layer
                else None
            )
            argon_flow_fld = ArgonFlowField(
                key=key,
                form_default=None,
                db_default=default_layer.argon_flow if default_layer
                else None
            )
            nitrogen_flow_fld = NitrogenFlowField(
                key=key,
                form_default=None,
                db_default=default_layer.nitrogen_flow if default_layer
                else None
            )
            pressure_fld = PressureField(
                key=key,
                form_default=None,
                db_default=default_layer.pressure if default_layer
                else None
            )
            deposit_duration_fld = DepositDurationField(
                key=key,
                form_default=None,
                db_default=default_layer.deposit_duration if default_layer
                else None
            )
            presputtering_thickness_fld = PresputteringThicknessField(
                key=key,
                form_default=None,
                db_default=default_layer.presputtering_thickness
                if default_layer else None
            )

        self.active_cooling = active_cooling_fld.value
        self.rotation_speed = rot_speed_fld.in_db_unit
        self.filament_current_start = filament_current_start_fld.in_db_unit
        self.filament_current_end = filament_current_end_fld.in_db_unit
        self.anode_current = anode_current_fld.in_db_unit
        self.anode_voltage = anode_voltage_fld.in_db_unit
        self.cathode_current = cathode_current_fld.in_db_unit
        self.cathode_voltage = cathode_voltage_fld.in_db_unit
        self.deposit_rate = deposit_rate_fld.in_db_unit
        self.argon_flow = argon_flow_fld.in_db_unit
        self.nitrogen_flow = nitrogen_flow_fld.in_db_unit
        self.pressure = pressure_fld.in_db_unit
        self.deposit_duration = deposit_duration_fld.in_db_unit
        self.presputter_thickness = presputtering_thickness_fld.in_db_unit

        super().__init__(
            fields=[
                active_cooling_fld, rot_speed_fld, filament_current_start_fld,
                filament_current_end_fld, anode_current_fld, anode_voltage_fld,
                cathode_current_fld, cathode_voltage_fld, deposit_rate_fld,
                argon_flow_fld, nitrogen_flow_fld, pressure_fld,
                deposit_duration_fld, presputtering_thickness_fld,
            ],
            sub_forms=[],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''

    def add_to_layer(self, layer: FilmLayer):
        """Build the triode row and attach it to the layer.

        Args:
            layer: The unsaved layer; its `triode_sputterings` backref
                is set to a list of one row.

        Raises:
            PausePageRun: If the form is invalid.
        """
        if not self.is_valid:
            raise PausePageRun
        triode = TriodeSputtering(
            has_active_cooling=self.active_cooling,
            rotation_speed=self.rotation_speed,
            filament_current_start=self.filament_current_start,
            filament_current_end=self.filament_current_end,
            anode_current=self.anode_current,
            anode_voltage=self.anode_voltage,
            cathode_current=self.cathode_current,
            cathode_voltage=self.cathode_voltage,
            deposit_rate=self.deposit_rate,
            argon_flow=self.argon_flow,
            nitrogen_flow=self.nitrogen_flow,
            pressure=self.pressure,
            deposit_duration=self.deposit_duration,
            presputtering_thickness=self.presputter_thickness,
            film_layer=layer,
        )
        layer.triode_sputterings = [triode]


class LayerForm(Form):
    """One layer, in a bordered box: `LayerIntroForm`, then the form of
    the chosen sputtering system.

    Attributes:
        sputter_system: The chosen `SputteringSystem` value, or None.
        intro_form: The `LayerIntroForm`.
        sputter_form: The `MagnetronForm` or `TriodeForm`, or None
            while no system is chosen.
    """

    def __init__(self, default_layer: FilmLayer | None, key: str):
        """Draw the layer box.

        The sputtering form appears only once a system is chosen, and
        changes when the user picks the other system.

        Args:
            default_layer: Layer whose values prefill the fields (edit
                film layers page), or None.
            key: The layer's index from 0, as a string. Used for the
                widget keys and, plus one, for the heading.
        """
        with st.container(border=True):
            st.header(f"• Layer  {int(key) + 1}")
            layer_intro_form = LayerIntroForm(default_layer, key)
            sputter_system = layer_intro_form.sputtering_system
            # TODO On the
            #   "edit film layers" page, if the user switches an existing layer from
            #   magnetron to triode (or the reverse), `default_layer.triode_sputterings[0]`
            #   (or `magnetron_sputterings[0]`) is an empty list, so `[0]` raises
            #   `IndexError`.
            if sputter_system == SputteringSystem.TRIODE:
                if default_layer:
                    triode_sput = default_layer.triode_sputterings[0]
                else:
                    triode_sput = None
                sputter_form = TriodeForm(triode_sput, key=key)

            elif sputter_system == SputteringSystem.MAGNETRON:
                if default_layer:
                    magnetron_sput = (default_layer.magnetron_sputterings[0])
                else:
                    magnetron_sput = None
                sputter_form = MagnetronForm(magnetron_sput, key=key)

            else:
                sputter_form = None

        self.sputter_system = layer_intro_form.sputtering_system
        self.intro_form = layer_intro_form
        self.sputter_form = sputter_form

        super().__init__(
            fields=[], sub_forms=[layer_intro_form, sputter_form]
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''

    def to_layer(self, film: Film, position_from_buffer: int):
        """Build an unsaved `FilmLayer` with all its parts.

        The parts are the nominal composition (`StoichioElement`s), the
        sputtering subtype row and one `TargetUse` per target. Loads
        the targets from the DB.

        Args:
            film: Film the layer belongs to.
            position_from_buffer: Index of the layer in the film, from
                0 at the bottom.

        Returns:
            The layer.

        Raises:
            PausePageRun: If the form is invalid or no sputtering
                system is chosen.
        """
        if not self.is_valid:
            raise PausePageRun
        base_info = self.intro_form
        layer = FilmLayer(
            position_from_buffer=position_from_buffer,
            deposit_temp=base_info.deposit_temp,
            nominal_thickness=base_info.nominal_thickness,
            shadow_mask_description=base_info.shadow_mask_descr,
            function=base_info.layer_function,
            sputtering_system=self.sputter_system,
            film=film,
        )
        # `cast` only silences the type checker: `from_str` expects the
        # foreign key column object, which Peewee returns when the
        # attribute is read on the class rather than on a row.
        fk_field = cast(Any, StoichioElement.film_layer)
        stoichio = StoichioElement.from_str(
            base_info.nominal_stoichio,
            fk_field=fk_field,
            parent=layer,
        )
        layer.nominal_stoichio = stoichio
        if self.sputter_form is None:
            raise PausePageRun
        self.sputter_form.add_to_layer(layer)

        first_target = Target.from_label(base_info.target_label)
        targets = [first_target]
        target_2_label = base_info.target_2_label
        if target_2_label is not None:
            co_sputter_target = Target.from_label(str(target_2_label))
            targets.append(co_sputter_target)
        target_uses = [TargetUse(target=target, film_layer=layer)
                       for target in targets]
        layer.target_uses = target_uses
        return layer


class LayerListForm(Form):
    """The film's layers: a layer count, then one `LayerForm` each.

    Used by the "new library" page (through `RootForm`) and by the
    "edit film layers" page.

    Attributes:
        layer_forms: One `LayerForm` per layer, bottom first.
    """

    def __init__(self, default_film: Film | None):
        """Draw the layer count, then the layer boxes.

        Args:
            default_film: Film whose layers prefill the forms (edit
                film layers page), or None. If the user raises the
                count, the extra layers start empty.

        Raises:
            PausePageRun: If the layer count is invalid (e.g. 0), so
                nothing below it is drawn.
        """
        layer_count_fld = LayerCountField(
            form_default=0,
            db_default=len(default_film.layers) if default_film else None
        )
        if not layer_count_fld.is_valid:
            raise PausePageRun

        layer_forms: list[LayerForm] = []
        for i in range(layer_count_fld.value):
            if default_film is None:
                default_layer = None
            else:
                try:
                    # TODO   `default_film.layers[i]` uses the backref query's order, not
                    #   `Film.ordered_layers` (sorted by `position_from_buffer`). With no
                    #   `ORDER BY`, SQLite doesn't guarantee the order, so the edit page could
                    #   prefill layers in the wrong order.
                    # `layers` is a backref query; indexing runs it.
                    default_layer = default_film.layers[i]
                except IndexError, AttributeError:  # TODO Remove AttributeError?
                    default_layer = None
            form = LayerForm(default_layer=default_layer, key=f'{i}')
            layer_forms.append(form)

        self.layer_forms = layer_forms

        super().__init__(fields=[layer_count_fld], sub_forms=layer_forms)

    def _is_coherent(self) -> tuple[bool, str]:
        """Refuse a missing layer form. See `Form._is_coherent`."""
        # TODO `Form.__init__` already removed the Nones from `sub_forms`,
        #  so this test never fails.
        if None in self.sub_forms:
            return False, "Please fill all layers."
        return True, ''

    def to_layers(self, film: Film):
        """Build the unsaved layers, with their parts.

        Args:
            film: Film the layers belong to.

        Returns:
            The `FilmLayer`s, bottom first, numbered from 0 in
            `position_from_buffer`.

        Raises:
            PausePageRun: If the form is invalid.
        """
        if not self.is_valid:
            raise PausePageRun
        layers = [f.to_layer(film, idx)
                  for idx, f in enumerate(self.layer_forms)]
        return layers


class TargetListForm(Form):
    """The targets used for the film: a count, then one `TargetField`
    each, in a bordered box.

    The chosen targets are not saved as such: they only fill the target
    choices of each layer (`TargetChoiceField`). What is saved is the
    target(s) of each layer, as `TargetUse` rows. On an edit page, the
    list is prefilled from the targets of the existing layers.

    Side effect: writes the chosen labels to the session state (a
    dictionary Streamlit keeps for each browser tab across reruns)
    under `SessionKeys.SELECTED_TARGETS`, with None for an unchosen
    target. It must therefore be drawn before `LayerListForm`.

    Attributes:
        target_flds: One `TargetField` per target.
    """

    def __init__(self, default_film: Film | None):
        """Draw the target count and the target fields.

        Args:
            default_film: Film whose targets prefill the fields (edit
                film layers page), or None.

        Raises:
            PausePageRun: If the target count is invalid (e.g. 0), so
                nothing below it is drawn.
        """
        if default_film is None:
            db_default_target_labels = []
        else:
            db_default_target_labels = default_film.target_labels
        with st.container(border=True):
            st.subheader("Targets")
            with st.container(horizontal=True):
                target_count_fld = TargetCountField(
                    form_default=0,
                    db_default=len(db_default_target_labels) if default_film
                    else None
                )
                if not target_count_fld.is_valid:
                    raise PausePageRun

                target_flds: list[TargetField] = []

                for i in range(target_count_fld.value):
                    try:
                        default_name = db_default_target_labels[i]
                    except IndexError:
                        default_name = None
                    field = TargetField(form_default=default_name, key=i)
                    target_flds.append(field)

        self.target_flds = target_flds

        sess[Sk.SELECTED_TARGETS] = [f.value for f in self.target_flds]

        super().__init__(fields=[target_count_fld] + target_flds,
                         sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''


class RootForm(Form):
    """The whole "new library" form.

    Draws, in order: `BaseInfoForm`, `FilmInfoForm`, `TargetListForm`,
    `LayerListForm` and `ConfirmOrderField`, then builds the library.

    Attributes:
        library: The unsaved `Library`, with its film, the film's
            layers and their parts. The page saves it with
            `save_with_dependent()`.
    """

    def __init__(self, default_lib: Library | None = None):
        """Draw the sub-forms and build the library.

        Args:
            default_lib: Library whose values prefill the forms, or
                None. The "new library" page always passes None.

        Raises:
            PausePageRun: If any part is invalid, from the `to_...`
                methods. Everything is already drawn by then, so only
                the page's "Submit" button is missing.
        """
        default_film = default_lib.films[0] if default_lib else None

        base_info_form = BaseInfoForm(default_lib)
        film_info_form = FilmInfoForm(default_film)
        target_list_form = TargetListForm(default_film)
        st.divider()
        layer_list_form = LayerListForm(default_film)
        confirm_order_fld = ConfirmOrderField(form_default=False)

        library = base_info_form.to_library(
            is_archived=default_lib.is_archived if default_lib else False,
        )
        film_info_form.add_to_library(library)

        layers = layer_list_form.to_layers(library.films[0])
        library.films[0].layers = layers

        self.library = library

        super().__init__(
            fields=[confirm_order_fld],
            sub_forms=[base_info_form, film_info_form, layer_list_form,
                       target_list_form],
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """Nothing to cross-check. See `Form._is_coherent`."""
        return True, ''
