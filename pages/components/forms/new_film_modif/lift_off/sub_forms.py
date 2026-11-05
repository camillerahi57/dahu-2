"""Lift-off part of the film modification form.

`LiftOffForm` is used by `RootForm` in `new_film_modif/sub_forms.py`.
Its `default_lift_off` argument prefills the form from an existing
lift-off; no page passes one yet, since there is no page to edit a film
modification.
"""

from components.forms.base_classes import Form, PausePageRun
from components.forms.new_film_modif.fields import UsedUltrasoundField, \
    UltrasoundConfigField
from components.forms.new_film_modif.shared import EtchingForm
from logic.lab_modelization.db_models import LiftOffEtching, FilmModification, \
    Etching


class LiftOffForm(Form):
    """Ultrasound use and settings, then recipe/pattern of a lift-off.

    Attributes:
        used_ultrasound: True if the user answered "Yes"; False for
            "No" or no answer.
        ultrasound_config: Free description of the ultrasound
            settings, or None if empty.
        base_info_form: The `EtchingForm` (recipe and pattern).
    """

    def __init__(self, default_lift_off: LiftOffEtching|None = None):
        """Draw the ultrasound fields, then the recipe/pattern form.

        Args:
            default_lift_off: Existing lift-off to prefill from, or
                None. Its `used_ultrasound` is a bool, while the field
                expects "Yes" or "No" (see DOC_NOTES.md).

        Raises:
            PausePageRun: See `EtchingForm.__init__`.
        """
        used_ultrasound_fld = UsedUltrasoundField(
            form_default=None,
            db_default=default_lift_off.used_ultrasound  # TODO expects `'Yes'`/`'No'`
            if default_lift_off else None,
        )
        ultrasound_config_fld = UltrasoundConfigField(
            form_default='',
            db_default=default_lift_off.ultrasound_config
            if default_lift_off else None,
        )

        default_etch = default_lift_off.etching if default_lift_off else None
        base_info_form = EtchingForm(default_etch)

        self.used_ultrasound = (used_ultrasound_fld.value
                                == UsedUltrasoundField.Option.YES)
        self.ultrasound_config = ultrasound_config_fld.value
        self.base_info_form = base_info_form

        super().__init__(fields=[used_ultrasound_fld, ultrasound_config_fld],
                         sub_forms=[base_info_form])

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''

    def to_lift_off_etching(self, film_modif: FilmModification) -> Etching:
        """Build the unsaved `Etching` row with its lift-off subtype.

        Args:
            film_modif: The (unsaved) modification it belongs to.

        Returns:
            The `Etching`, with `lift_offs` set to a list holding the
            `LiftOffEtching`.

        Raises:
            PausePageRun: If the form is not valid.
        """
        if not self.is_valid:
            raise PausePageRun

        etching = self.base_info_form.to_etching(film_modif)

        lift_off = LiftOffEtching(
            used_ultrasound=self.used_ultrasound,
            ultrasound_config=self.ultrasound_config,
            etching=etching,
        )

        etching.lift_offs = [lift_off]

        return etching
