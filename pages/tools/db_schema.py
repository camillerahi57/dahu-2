from peewee import *

# FIELD TYPES:
# https://docs.peewee-orm.com/en/latest/peewee/models.html#fields

db = PostgresqlDatabase(
    'dahu2', user='postgres', password='postgres', host='localhost', port=5432)


# Be careful, if an attribute is a foreignkey, you have to add '_id' at the end of the name of the column, in the
# DB table. This is because in the table, the key is actually store as an ID.


class BaseDahuModel(Model):
    class Meta:
        database = db
        legacy_table_names = False


class Experimenter(BaseDahuModel):
    full_name = CharField()
    email_address = CharField()


class Library(BaseDahuModel):
    name = CharField()
    comment = CharField()
    made_at = DateTimeField()


class CharacMethod(BaseDahuModel):
    name = CharField()
    experimenter = ForeignKeyField(Experimenter)
    library = ForeignKeyField(Library)