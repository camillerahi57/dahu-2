from types import SimpleNamespace

import streamlit as st

from components.forms.new_target.fields import MadeAtField, \
    ExperimenterEmailField, \
    TargetNameField, PreviousVersionField
from components.forms.shared2 import Form, StopPageLoad
from logic.constants import NEW_TARGET
from logic.lab_modelization.db_models import Target


class BasicInfoForm(Form):
    def __init__(self, updated_target: Target = None):

        class Default(SimpleNamespace):
            made_at = None
            email = None
            name = None
            built_from_name = None

        if updated_target is not None:
            Default.made_at = updated_target.made_on
            Default.email = updated_target.made_by_email
            Default.name = updated_target.physical_name
            built_from: Target|None = updated_target.previous_version
            if built_from is None:
                Default.built_from_name = NEW_TARGET
            else:
                Default.built_from_name = built_from.physical_name

        col1, col2 = st.columns(2)
        with col1:
            made_on_fld = MadeAtField(updated=Default.made_at)
        with col2:
            email_fld = ExperimenterEmailField(updated=Default.email)
        target_name_fld = TargetNameField(updated=Default.name)

        previous_version_fld = PreviousVersionField(
            updated=Default.built_from_name)
        previous_name = previous_version_fld.value
        if previous_name == NEW_TARGET or not previous_version_fld.is_filled:
            built_from = None
        else:
            built_from = Target.from_name(previous_name)

        self.made_on = made_on_fld.value
        self.made_by_email = email_fld.value
        self.physical_name = target_name_fld.value
        self.built_from = built_from
        self.updated_target = updated_target

        super().__init__(
            fields=[made_on_fld, email_fld, target_name_fld,
                    previous_version_fld],
            sub_forms=[]
        )

    def _check_coherence(self) -> tuple[bool, str]:
        updated, built_from = self.updated_target, self.built_from
        if updated is not None and built_from is not None:
            if updated.id == built_from.id:
                return False, ("Target cannot have itself as a built-from "
                               "target.")
        return True, ''

    def to_target(self, updated_target: Target = None) -> Target:
        if not self.is_valid:
            raise StopPageLoad

        target_id = updated_target.id if updated_target else None

        return Target(
            id=target_id,
            made_on=self.made_on,
            made_by_email=self.made_by_email,
            physical_name=self.physical_name,
            previous_version=self.built_from,
        )