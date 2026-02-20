# Apply alternating row colors
def highlight_rows(row) -> list[str]:
    if row.name % 2 == 0:
        return ['background-color: white'] * len(row)
    else:
        return ['background-color: #f0f0f0'] * len(row)


# def add_fake_library()

# def assert_local_schema_and_db_matching()
"""Checks if the described schema in Python project and the PostgreSQL database schema are matching."""