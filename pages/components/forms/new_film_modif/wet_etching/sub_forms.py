"""Wet (chemical) etching part of the film modification form.

`WetEtchingForm` is used by `RootForm` in `new_film_modif/sub_forms.py`.
Its `default_wet_etch` argument prefills the form from an existing
etching; no page passes one yet, since there is no page to edit a film
modification.
"""

import streamlit as st

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import HardBakeTempField, \
    AcidEtchingDurationField, UsedUltrasoundField, \
    UltrasoundConfigField, EtchingDepthSpeedField, EtchingLateralSpeedField, \
    BaseField, AcidField, SolventField, SolventCountField, \
    DevelopmentDurationField
from components.forms.new_film_modif.shared import \
    EtchingForm
from logic.lab_modelization.db_models import WetEtching, \
    Etching, FilmModification, EtchingSolvent


class WetEtchingForm(Form):
    """Development, hard bake, acid, solvents, ultrasound, etching
    speeds, then recipe/pattern of a wet etching.

    The physical values are stored in SI base units; the UI unit of
    each one is that of its field class (see `WetEtching`).

    Attributes:
        hard_bake_temp: Hard bake temperature, in K (typed in °C), or
            None.
        etching_duration: Time in the acid, in s (typed in min), or
            None.
        development_duration: Development time, in s (typed in min),
            or None.
        used_ultrasound: True if the user answered "Yes"; False for
            "No" or no answer.
        ultrasound_config: Free description of the ultrasound
            settings, or None if empty.
        depth_speed: Acid etching speed into the depth, in m/s (typed
            in µm/s), or None.
        lateral_speed: Lateral acid etching speed, in m/s (typed in
            µm/s), or None.
        base: Name of the base, or None.
        acid: Name of the acid, or None.
        solvent_form: The `SolventListForm`.
        base_info_form: The `EtchingForm` (recipe and pattern).
    """

    def __init__(self, default_wet_etch: WetEtching|None = None):
        """Draw the fields in groups separated by dividers.

        Args:
            default_wet_etch: Existing etching to prefill from, or
                None. Its `used_ultrasound` is a bool, while the field
                expects "Yes" or "No" (see DOC_NOTES.md).

        Raises:
            PausePageRun: See `EtchingForm.__init__`.
        """
        base_fld = BaseField(
            form_default=None,
            db_default=default_wet_etch.base
            if default_wet_etch else None,
        )
        development_duration_fld = DevelopmentDurationField(
            form_default=None,
            db_default=default_wet_etch.development_duration
            if default_wet_etch else None,
        )

        st.divider()

        bake_temp_fld = HardBakeTempField(
            form_default=None,
            db_default=default_wet_etch.hard_bake_temperature
            if default_wet_etch else None,
        )

        st.divider()

        acid_fld = AcidField(
            form_default=None,
            db_default=default_wet_etch.acid
            if default_wet_etch else None,
        )
        etching_duration_fld = AcidEtchingDurationField(
            form_default=None,
            db_default=default_wet_etch.etching_duration
            if default_wet_etch else None,
        )

        st.divider()

        solvent_form = SolventListForm(
            default_wet_etch.solvents if default_wet_etch else None,
        )

        st.divider()

        with st.container(horizontal=True):
            used_ultrasound_fld = UsedUltrasoundField(
                form_default=None,
                db_default=default_wet_etch.used_ultrasound  # TODO expects `'Yes'`/`'No'`
                if default_wet_etch else None,
            )
            ultrasound_config_fld = UltrasoundConfigField(
                form_default='',
                db_default=default_wet_etch.ultrasound_config
                if default_wet_etch else None,
            )
        st.divider()
        with st.container(horizontal=True):
            depth_speed_fld = EtchingDepthSpeedField(
                form_default=None,
                db_default=default_wet_etch.acid_etching_depth_speed
                if default_wet_etch else None,
            )
            lateral_speed_fld = EtchingLateralSpeedField(
                form_default=None,
                db_default=default_wet_etch.acid_etching_lateral_speed
                if default_wet_etch else None,
            )
        st.divider()

        default_etch = default_wet_etch.etching if default_wet_etch else None
        base_info_form = EtchingForm(default_etch)

        st.divider()

        self.hard_bake_temp = bake_temp_fld.in_db_unit
        self.etching_duration = etching_duration_fld.in_db_unit
        self.development_duration = development_duration_fld.in_db_unit
        self.used_ultrasound = (used_ultrasound_fld.value
                                == UsedUltrasoundField.Option.YES)
        self.ultrasound_config = ultrasound_config_fld.value
        self.depth_speed = depth_speed_fld.in_db_unit
        self.lateral_speed = lateral_speed_fld.in_db_unit
        self.base = base_fld.value
        self.acid = acid_fld.value
        self.solvent_form = solvent_form

        self.base_info_form = base_info_form
        super().__init__(
            fields=[bake_temp_fld, etching_duration_fld, used_ultrasound_fld,
                    ultrasound_config_fld, depth_speed_fld, lateral_speed_fld,
                    base_fld, acid_fld, development_duration_fld],
            sub_forms=[base_info_form, solvent_form]
        )

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        # User can indicate that there is a pattern without providing it.
        return True, ''

    def to_wet_etching(self, film_modif: FilmModification) -> Etching:
        """Build the unsaved `Etching` row with its wet etching subtype.

        No image bytes are involved: the pattern is picked among
        existing `Pattern` files.

        Args:
            film_modif: The (unsaved) modification it belongs to.

        Returns:
            The `Etching`, with `wet_etchings` set to a list holding the
            `WetEtching`, itself with its `solvents`.

        Raises:
            PausePageRun: If the form is not valid.
        """
        # The docstring used to promise "pattern image bytes", from
        # when patterns were uploaded here; fixed.
        if not self.is_valid:
            raise PausePageRun

        etching = self.base_info_form.to_etching(film_modif)

        wet_etching = WetEtching(
            hard_bake_temperature=self.hard_bake_temp,
            etching_duration=self.etching_duration,
            development_duration=self.development_duration,
            used_ultrasound=self.used_ultrasound,
            ultrasound_config=self.ultrasound_config,
            base=self.base,
            acid=self.acid,
            acid_etching_depth_speed=self.depth_speed,
            acid_etching_lateral_speed=self.lateral_speed,
            etching=etching,
        )
        solvents = self.solvent_form.to_solvents(wet_etching)
        wet_etching.solvents = solvents
        etching.wet_etchings = [wet_etching]
        return etching


class SolventListForm(Form):
    """The solvents of a wet etching, in order: a count, then one
    `SolventField` each, side by side.

    Attributes:
        solvents: Solvent names in order of use; an item is None where
            the field is empty. Empty list if no count is given.
    """

    def __init__(self, solvents: list[EtchingSolvent]|None):
        """Draw the subheader, the count and the solvent fields.

        Args:
            solvents: Existing solvents to prefill from, or None. They
                are passed to the fields as `EtchingSolvent` rows,
                while the fields expect names (see DOC_NOTES.md).
        """
        st.subheader('Solvents')
        count_fld = SolventCountField(
            form_default=None,
            db_default=len(solvents) if solvents else None,
        )
        with st.container(horizontal=True):
            solvent_fld_list = []
            if count_fld.value:
                for i in range(count_fld.value):
                    with st.container():
                        # TODO `SolventListForm` passes `EtchingSolvent` rows as `db_default` to
                        #   `SolventField`, whose `options.index(prefill)` expects a name: it
                        #   would raise `ValueError`. Probably `solvents[i].label`. Also,
                        #   `default_wet_etch.solvents` is not sorted by `step_idx`.
                        st.write(f'Solvent {i+1}')
                        # The index in the key keeps widget keys
                        # distinct between solvents.
                        fld = SolventField(
                            key=f'solvent_{i}',
                            form_default=None,
                            db_default=solvents[i]
                            if solvents and len(solvents) > i else None,
                        )
                    solvent_fld_list.append(fld)
        self.solvents = [fld.value for fld in solvent_fld_list]
        super().__init__(fields=[count_fld]+solvent_fld_list,
                         sub_forms=[])

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''

    def to_solvents(self, wet_etch: WetEtching) -> list[EtchingSolvent]:
        """Build the unsaved `EtchingSolvent` rows.

        Doesn't check validity itself; `WetEtchingForm.to_wet_etching`
        has already done it.

        Args:
            wet_etch: The (unsaved) wet etching they belong to.

        Returns:
            One row per solvent, with `step_idx` = its position from 0.
        """
        return [
            EtchingSolvent(etching=wet_etch, label=label, step_idx=idx)
            for idx, label in enumerate(self.solvents)
        ]
