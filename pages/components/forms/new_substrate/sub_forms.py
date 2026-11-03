"""Forms of the new and edit substrate pages.

Nesting: `RootForm` → `LayerListForm` → one `LayerForm` per layer →
`CrystalOrientationForm`. `RootForm.to_substrate` turns the validated
input into an unsaved `Substrate` with its `SubstrateLayer`s, which
the page saves with `save_with_dependent()`.

On the edit page, each form gets the existing substrate or layer as
its default, so its fields are prefilled from the DB.
"""

import streamlit as st

from components.forms.base_classes import Form
from components.forms.new_substrate.fields import (
    HasCrystalOrientationField, HField, KField, LField, StoichiometryField,
    ThicknessField, LayerCountField, SubstrateLabelField, CommentField
)
from logic.lab_modelization.db_models import Substrate, SubstrateLayer, \
    StoichioElement


class CrystalOrientationForm(Form):
    """Crystal orientation of one layer, as Miller indices (h, k, l).

    Asks whether the layer has an orientation; if so, shows the h, k
    and l fields.

    Attributes:
        has_orientation: True, False, or None if not answered yet.
        h: h index, or None without orientation.
        k: k index, or None without orientation.
        l: l index, or None without orientation.
    """

    def __init__(self, key: str, default_layer: SubstrateLayer|None):
        """Draw the fields.

        Args:
            key: Distinguishes the widgets of the different layers.
            default_layer: Existing layer to prefill from, or None.
                A layer whose `h` is NULL counts as having no
                orientation.
        """
        fields = []
        st.write(f"**Crystal Orientation**")
        with st.container(horizontal=True, vertical_alignment='top'):
            has_orientation_fld = HasCrystalOrientationField(
                key,
                form_default=None,
                db_default=default_layer.h is not None
                    if default_layer else None,
            )
            fields.append(has_orientation_fld)
            if has_orientation_fld.value is True:
                # The first column stays empty, as an indent.
                col1_, col2_, col3_, col4_ = st.columns(4)
                with col2_:
                    h_fld = HField(
                        key=f'h_{key}',
                        form_default=0,
                        db_default=default_layer.h if default_layer else None,
                    )
                with col3_:
                    k_fld = KField(
                        key=f'k_{key}',
                        form_default=0,
                        db_default=default_layer.k if default_layer else None,
                    )
                with col4_:
                    l_fld = LField(
                        key=f'l_{key}',
                        form_default=0,
                        db_default=default_layer.l if default_layer else None,
                    )
                h, k, l = h_fld.value, k_fld.value, l_fld.value
                fields.extend([h_fld, k_fld, l_fld])
            else:
                h, k, l = None, None, None

        self.has_orientation = has_orientation_fld.value
        self.h, self.k, self.l = h, k, l

        super().__init__(fields, [])

    def _is_coherent(self):
        """Refuse the orientation (0, 0, 0). See `Form._is_coherent`."""
        if self.has_orientation:
            if (self.h, self.k, self.l) != (0, 0, 0):
                return True, ''
            else:
                return False, 'Invalid crystal orientation.'
        else:
            return True, ''


class LayerForm(Form):
    """One substrate layer: composition, thickness and orientation.

    Attributes:
        stoichio: Chemical formula string, or None if invalid.
        thickness: Thickness in m (typed in µm), or None if invalid.
        cryst_orient_form: The layer's `CrystalOrientationForm`.
    """

    def __init__(self, key: str, default_layer: SubstrateLayer|None):
        """Draw the layer's fields and sub-form.

        Args:
            key: Distinguishes the widgets of the different layers
                (the layer index).
            default_layer: Existing layer to prefill from, or None.
        """
        with st.container(horizontal=True, vertical_alignment='center'):
            stoichio_fld = StoichiometryField(
                key,
                form_default=None,
                db_default=StoichioElement.to_str(default_layer.stoichio)
                    if default_layer else None,
            )
            thickness_fld = ThicknessField(
                key,
                form_default=0.,
                db_default=default_layer.thickness if default_layer else 0.,
            )
        cryst_orient_form = CrystalOrientationForm(key, default_layer)

        self.stoichio = stoichio_fld.value
        self.thickness = thickness_fld.in_db_unit
        self.cryst_orient_form = cryst_orient_form

        super().__init__(
            [stoichio_fld, thickness_fld],
            [cryst_orient_form]
        )

    def _is_coherent(self):
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''


class LayerListForm(Form):
    """The stack of layers: a layer count, then one `LayerForm` each.

    Layers are listed from the bottom (index 0) to the top.

    Attributes:
        layer_forms: One `LayerForm` per layer, bottom first; empty
            while the layer count is invalid.
    """

    def __init__(self, default_sub: Substrate|None):
        """Draw the layer count and the layer forms.

        Args:
            default_sub: Existing substrate whose layers prefill the
                forms, or None. Layer i is prefilled from
                `default_sub.layers[i]`.
        """
        st.subheader("Layers:")

        layer_count_fld = LayerCountField(
            form_default=0,
            db_default=len(default_sub.layers) if default_sub else None,
        )
        st.divider()
        layer_count = layer_count_fld.value

        layer_forms = []
        if layer_count_fld.is_valid:
            for i in range(layer_count):
                if i == 0:
                    layer_label = 'Bottom layer'
                elif i == layer_count - 1:
                    layer_label = 'Top layer'
                else:
                    layer_label = f"Layer {i+1}"
                with st.container(border=True):
                    st.subheader(layer_label)
                    # No default when the user adds more layers than
                    # the substrate had (IndexError) or on the "new"
                    # page, where `default_sub` is None
                    # (AttributeError).
                    # TODO layer i is
                    #   prefilled from `default_sub.layers[i]`, but the `layers` backref has
                    #   no `order_by(position_from_back)`; the order relies on SQLite
                    #   returning rows in insertion order.
                    try:
                        default_layer = default_sub.layers[i]
                    except IndexError, AttributeError:
                        default_layer = None
                    layer_form = LayerForm(
                        key=str(i),
                        default_layer=default_layer,
                    )
                    layer_forms.append(layer_form)

        self.layer_forms = layer_forms
        super().__init__(
            [layer_count_fld],
            layer_forms,
        )

    def _is_coherent(self):
        """Require at least one layer. See `Form._is_coherent`."""
        if len(self.layer_forms) == 0:
            return False, "Please add layer(s)."
        return True, ''


class RootForm(Form):
    """The whole substrate form: name, comment and layers.

    Used by `pages/new_substrate.py` and `pages/edit_substrate.py`.

    Attributes:
        substrate_name: The substrate's label, or None if invalid.
        comment: The comment, or None if empty.
        layer_list_form: The `LayerListForm`.
    """

    def __init__(self, default_sub: Substrate|None):
        """Draw the whole form.

        Args:
            default_sub: Substrate being edited, or None on the "new"
                page.
        """
        sub_label_fld = SubstrateLabelField(
            form_default=None,
            db_default=default_sub.label if default_sub else None,
        )
        comment_fld = CommentField(
            form_default=None,
            db_default=default_sub.comment if default_sub else None,
        )
        layer_list_form = LayerListForm(default_sub)

        self.substrate_name = sub_label_fld.value
        self.comment = comment_fld.value
        self.layer_list_form = layer_list_form

        super().__init__(
            [sub_label_fld, comment_fld],
            [layer_list_form]
        )

    def _is_coherent(self):
        """No cross-field rule. See `Form._is_coherent`."""
        return True, ''

    def show_layers(self):
        """Draw a sketch of the stack, top layer first.

        Shows one line per layer with its formula, only when the form
        is valid.
        """
        st.divider()
        layer_forms = self.layer_list_form.layer_forms
        if self.is_valid:
            layer_strings = []
            for f in reversed(layer_forms):
                layer_strings.append(f'――――――――――― {f.stoichio}')
            with st.container(border=True, width='content'):
                st.write("⬇️ Top layer")
                st.text('\n'.join(layer_strings))
                st.write("⬆️ Bottom layer")

    def to_substrate(self, id_: int|None = None) -> Substrate:
        """Build the unsaved substrate and its layers from the input.

        Call only when the form is valid. Nothing is written to the
        DB; the page saves the result with `save_with_dependent()`.

        Args:
            id_: Id to give the substrate (the old id on the edit
                page), or None to let the DB choose one.

        Returns:
            A `Substrate` whose `layers` list holds one unsaved
            `SubstrateLayer` per layer form, with `position_from_back`
            0 for the bottom layer.
        """
        substrate = Substrate(
            id=id_ if id_ is not None else None,
            label=self.substrate_name,
            comment=self.comment,
        )
        substrate.layers = []

        layer_forms = self.layer_list_form.layer_forms
        for i, form in enumerate(layer_forms):
            cryst_orient = form.cryst_orient_form
            h, k, l = cryst_orient.h, cryst_orient.k, cryst_orient.l
            layer = SubstrateLayer.from_stoichio(
                form.stoichio, form.thickness, h, k, l,
                substrate, position_from_back=i)
            substrate.layers.append(layer)

        return substrate
