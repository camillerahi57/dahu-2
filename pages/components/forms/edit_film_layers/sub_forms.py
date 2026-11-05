"""Root form of the "edit film layers" page (`pages/edit_film_layers.py`).

Reuses the target and layer forms of the "new library" page, prefilled
from the existing film. The page then replaces all the film's layers:
it deletes the old ones with their parts and saves the new ones.
"""

import streamlit as st

from components.forms.base_classes import Form
from components.forms.new_library.fields import ConfirmOrderField
from components.forms.new_library.sub_forms import TargetListForm, \
    LayerListForm
from logic.lab_modelization.db_models import Film


class RootForm(Form):
    """The targets used, the layers, and the "layer order is right"
    checkbox.

    Attributes:
        layers: The new, unsaved `FilmLayer`s of the film, bottom
            first, with their parts.
    """

    def __init__(self, updated_film: Film):
        """Draw the target list, the layer list and the checkbox.

        Args:
            updated_film: The film whose layers are edited. It prefills
                the forms and becomes the film of the new layers.

        Raises:
            PausePageRun: From the sub-forms while a count is invalid,
                and from `LayerListForm.to_layers` while the layers are
                not valid.
        """
        # `TargetListForm` must come first: it writes the chosen
        # targets to the session state (a dictionary Streamlit keeps for
        # each browser tab across reruns), which `LayerListForm` reads.
        target_list_form = TargetListForm(updated_film)
        st.divider()
        layer_list_form = LayerListForm(updated_film)
        confirm_order_fld = ConfirmOrderField(form_default=False)

        self.layers = layer_list_form.to_layers(updated_film)

        super().__init__(fields=[confirm_order_fld],
                         sub_forms=[target_list_form, layer_list_form])

    def _is_coherent(self) -> tuple[bool, str]:
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''
