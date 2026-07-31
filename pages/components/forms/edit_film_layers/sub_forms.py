import streamlit as st

from components.forms.new_library.fields import ConfirmOrderField
from components.forms.new_library.sub_forms import TargetListForm, \
    LayerListForm
from components.forms.base_classes import Form
from logic.lab_modelization.db_models import Film


class RootForm(Form):
    def __init__(self, updated_film: Film):
        target_list_form = TargetListForm(updated_film)
        st.divider()
        layer_list_form = LayerListForm(updated_film)
        confirm_order_fld = ConfirmOrderField(form_default=False)

        self.layers = layer_list_form.to_layers(updated_film)

        super().__init__(fields=[confirm_order_fld],
                         sub_forms=[target_list_form, layer_list_form])

    def _is_coherent(self) -> tuple[bool, str]:
        return True, ''