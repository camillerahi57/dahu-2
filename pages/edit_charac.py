"""Page for editing a characterization (e.g. an EDX) made on a film.

The characterization is chosen by the `charac_id` query parameter (a
`name=value` pair after the `?` of the URL, see `IdType.CHARAC`). The
form is `edit_charac.sub_forms.RootForm`. The film and the type cannot
be changed; the date, author, last film modification, comment and the
label of the data file can, and the data file can be replaced (or added,
if it is missing from the server).

On submit, the characterization row is updated in place, keeping its id,
so the references other libraries hold to it stay valid. If the data
file is replaced, the new file is first written to `user_data/` (it can
be several GB, so this can take a while), then, in one transaction (a
group of DB writes that either all succeed or are all cancelled), the
new file's row is saved, the old subtype rows (e.g. the EDX results per
element) are replaced by the ones read from the new file, and the old
file's row is deleted. The old file is deleted from `user_data/` only
once the transaction succeeded; if it fails, the new file is deleted
instead. The user is then sent to the film's library page.
"""
import streamlit as st

from components.forms.base_classes import PausePageRun
from components.forms.edit_charac.sub_forms import RootForm
from components.general import init_page, \
    switch_to_submit_successful, current_params
from logic.constants import IdType
from logic.lab_modelization.base_classes import db
from logic.lab_modelization.db_models import Charac
from logic.page_list import pages

init_page(pages.edit_charac)

st.set_page_config(layout="centered")

charac_id = current_params()[IdType.CHARAC]
old_charac: Charac = Charac.get_by_id(charac_id)

try:
    root_form = RootForm(old_charac)

    lib_ref_text = ''
    for lib in old_charac.referencing_libs():
        lib_ref_text += f'- {lib.label}\n'
    st.warning(f"Other libraries refer to this characterization:\n"
               f"{lib_ref_text}")

    if st.button("Submit", disabled=not root_form.is_valid, type="primary"):
        new_charac = root_form.charac
        old_file = old_charac.file
        new_file = root_form.new_file
        with st.spinner('Saving, please wait...'):
            if new_file is not None:
                new_file.save_stream(root_form.file_stream)
            try:
                with db.atomic():
                    if new_file is not None:
                        # The file row first: the charac needs its id.
                        new_file.save()
                        old_charac.delete_subtype_rows()
                    elif root_form.file_label != old_file.label:
                        old_file.label = root_form.file_label
                        old_file.save()
                    new_charac.save()  # Has an id: updates the row.
                    for row in root_form.new_subtype_rows:
                        row.save_with_dependent()
                    if new_file is not None:
                        # Only possible once no charac points to it.
                        old_file.delete_instance()
            except BaseException:
                # No row points to the new file: don't leave it on the
                # disk.
                if new_file is not None:
                    new_file.get_path().unlink(missing_ok=True)
                raise
            if new_file is not None:
                # After the transaction: a failed one must not lose the
                # old file.
                old_file.delete_related_files()

        switch_to_submit_successful(
            redirect_to=pages.inspect_lib,
            id_type=IdType.LIB,
            object_id=old_charac.film.library.id,
        )

except PausePageRun:
    pass
