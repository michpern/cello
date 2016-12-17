from peewee import *

database = SqliteDatabase('c:/dev/tracker.db', **{})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Board(BaseModel):
    name = TextField(null=True)
    parentproject = IntegerField(db_column='parentProject')

    class Meta:
        db_table = 'Board'

class Item(BaseModel):
    assignedto = IntegerField(db_column='assignedTo', null=True)
    backgroundcolour = IntegerField(db_column='backgroundColour', null=True)
    created = IntegerField(null=True)
    description = TextField(null=True)
    duedate = IntegerField(db_column='dueDate', null=True)
    label = TextField(null=True)
    lastupdated = IntegerField(db_column='lastUpdated', null=True)
    lastupdatedby = IntegerField(db_column='lastUpdatedBy', null=True)
    name = TextField(null=True)
    parentstream = IntegerField(db_column='parentStream')
    reportedby = IntegerField(db_column='reportedBy', null=True)
    title = TextField()
    orderInStream = IntegerField(db_column='orderInStream', null=True)
    class Meta:
        db_table = 'Item'

class Project(BaseModel):
    gitstem = TextField(null=True)
    name = TextField()

    class Meta:
        db_table = 'Project'

class Stream(BaseModel):
    name = TextField(null=True)
    parentboard = IntegerField(db_column='parentBoard')
    order_in_board = IntegerField(db_column='orderInBoard')

    class Meta:
        db_table = 'Stream'

class User(BaseModel):
    defaultboard = IntegerField(db_column='defaultBoard', null=True)
    name = TextField(null=True)
    username = TextField(null=True)

    class Meta:
        db_table = 'User'

class SqliteSequence(BaseModel):
    name = UnknownField(null=True)  #
    seq = UnknownField(null=True)  #

    class Meta:
        db_table = 'sqlite_sequence'
