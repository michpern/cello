from peewee import *
from cello import db
# database = SqliteDatabase('c:/dev/tracker.db', **{})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(db.Model):
    """class Meta:
        database = database
"""

class Board(BaseModel):
    name = TextField(null=True)
    parentproject = IntegerField(db_column='parentProject')
    gitstem = TextField(null=True)    
    lastId = IntegerField(db_column='lastId', null=True)
    createdby = IntegerField(db_column='createdBy', null=True)
    isprivate = IntegerField(db_column='isprivate', null=True)
    team = IntegerField(db_column='team', null=True)
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
    itemtype = IntegerField(db_column='itemtype', null=True)
    featureId =  TextField(null=True)
    parentId = IntegerField(db_column='parentId', null=True)
    priority = IntegerField(db_column='priority', null=True)
    class Meta:
        db_table = 'Item'

""" - Not used
class Project(BaseModel):
    gitstem = TextField(null=True)
    name = TextField()
    lastId = IntegerField(db_column='lastId', null=True)

    class Meta:
        db_table = 'Project'
"""

class Stream(BaseModel):
    name = TextField(null=True)
    parentboard = IntegerField(db_column='parentBoard')
    order_in_board = IntegerField(db_column='orderInBoard')
    allow_direct_add = IntegerField(db_column='allowDirectAdd')
    stream_type = IntegerField(db_column='streamType')
    class Meta:
        db_table = 'Stream'

class UserPrefs(BaseModel):
    defaultboard = IntegerField(db_column='defaultBoard', null=True)
    name = TextField(null=True)
    username = TextField(null=True)

    class Meta:
        db_table = 'UserPrefs'

class Comment(BaseModel):
    parentitem = IntegerField(db_column='parentItem')
    comment = TextField(null=True)
    lastupdated = IntegerField(db_column='lastUpdated', null=True)
    lastupdatedby = IntegerField(db_column='lastUpdatedBy', null=True)

    class Meta:
        db_table = 'Comment'

class ChecklistItem(BaseModel):
    parentitem = IntegerField(db_column='parentItem')
    checklisttext =  TextField(null=True)
    lastupdated = IntegerField(db_column='lastUpdated', null=True)
    lastupdatedby = IntegerField(db_column='lastUpdatedBy', null=True)
    completed = IntegerField(db_column='completed')

    class Meta:
        db_table = 'ChecklistItem'

class Team(BaseModel):
    name = TextField(null=True)

class TeamMembers(BaseModel):
    teamId = IntegerField(db_column='teamId')
    userId = IntegerField(db_column='userId')

class SqliteSequence(BaseModel):
    name = UnknownField(null=True)  #
    seq = UnknownField(null=True)  #

    class Meta:
        db_table = 'sqlite_sequence'
