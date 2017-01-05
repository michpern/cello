"""
Routes and views for the flask application.
"""

from datetime import datetime
import json
from flask import render_template, request
from playhouse.shortcuts import *
from cello import app, model
import cello.model
from builtins import print


class uiStream:
    def __init__(self, id, name, allow_direct_add, items):
        self.id = id
        self.name = name
        self.allow_direct_add = allow_direct_add
        self.items = items

class uiItem:
    def __init__(self, id, type, featureId, name, lastupdated, lastupdatedby, checklistitemcount, checklistitemcompleted, checklisttext, description, comments):
        self.id = id
        self.type = type
        self.featureId = featureId
        self.name = name
        self.lastupdated = lastupdated
        self.lastupdatedby = lastupdatedby
        self.checklistitemcount = checklistitemcount
        self.checklistitemcompleted = checklistitemcompleted
        self.checklisttext = checklisttext
        if description is None:
            self.description = ""
        else:
            self.description = description

        if comments is None:
            self.comments = ""
        else:
            self.comments = comments

class uiComment:
    def __init__(self, id, comment, lastupdated, lastupdatedby):
        self.id = id
        self.comment = comment
        self.lastupdated = lastupdated
        self.lastupdatedby = lastupdatedby

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

class uiChecklistItem:
    def __init__(self, id, itemtext, lastupdated, lastupdatedby, completed):
        self.id = id
        self.itemtext = itemtext
        self.lastupdated = lastupdated
        self.lastupdatedby = lastupdatedby
        self.completed = completed

def jdefault(o):
    return o.__dict__

def format_date_time(t):
    # yyyymmddhhmmss
    if t is None:
        return ""

    y = t // 10000000000
    mon = (t // 100000000) % 100
    d = (t // 1000000) % 100
    h = (t // 10000) % 100
    m = (t // 100) % 100
    s = t % 100
    r = '{:02d}/{:02d}/{:04d}-{:02d}:{:02d}'.format(d, mon, y, h, m)
    return r

def get_date_time(dt):
    y = dt.year
    mon = dt.month
    d = dt.day
    h = dt.hour
    m = dt.minute
    s = dt.second

    res = y * 10000000000 + mon * 100000000 + d * 1000000 + h * 10000 + m * 100 + s
    return res

def get_user_name(u):
    if u is None:
        return ""

    user = model.User.get(model.User.id == u)
    return user.name

def get_comment_info(item_id):
    dbcomments = model.Comment.select().where(model.Comment.parentitem == item_id).order_by(model.Comment.lastupdated.desc())
    comments = ""
    count = 0
    for i in dbcomments:
        lu = format_date_time(i.lastupdated)
        lub = get_user_name(i.lastupdatedby)

        comments = comments +  i.comment + "<br/>"
        count = count + 1
        if (count > 2):
            break
    return comments

def get_checklist_info(item_id):
    total = 0
    completed = 0
    text = ""
    dbchecklist = model.ChecklistItem.select().where(model.ChecklistItem.parentitem == item_id)
    total = dbchecklist.count()
    for i in dbchecklist:
        if i.completed == 1:
            completed = completed + 1
            text = text + "<s>" + i.checklisttext + "</s><br/>"
        else:
            text = text + i.checklisttext + "<br/>"

    return total,completed, text

def get_UI_stream(stream_id):
    stream = model.Stream.get(model.Stream.id == stream_id)
    stream_items = model.Item.select().where(model.Item.parentstream == stream_id).order_by(model.Item.orderInStream)
    si = []
    for i in stream_items:
        checklisttotal, checklistitemcompleted, checklisttext = get_checklist_info(i.id)
        comments = get_comment_info(i.id)
        uii = uiItem(i.id, i.itemtype, i.featureId, i.name, i.lastupdated, i.lastupdatedby, checklisttotal, checklistitemcompleted, checklisttext, i.description, comments)
        si.append(uii)

    print ("Stream: " + stream.name ) 

    print (si)   
    uistr = uiStream(stream.id, stream.name, stream.allow_direct_add, si)
    return uistr

def update_checklist_items(item_id, form_data):
    dbchecklist = model.ChecklistItem.select().where(model.ChecklistItem.parentitem == item_id).order_by(model.ChecklistItem.lastupdated.desc())
    if dbchecklist.count() == 0:
        return

    all_items = {k:v for k,v in form_data.items() if k.startswith('clih')}
    checked_items = {k:v for k,v in form_data.items() if k.startswith('clic')}
    for i in dbchecklist: 
        key = "clic-" + str(item_id) + "-" + str(i.id)

        if key in checked_items:
            if i.completed is None or i.completed == 0:
                query = model.ChecklistItem.update(completed=1, lastupdated=get_date_time(datetime.utcnow()), lastupdatedby=get_current_user()).where(model.ChecklistItem.id == i.id)
                query.execute()
        else:
            if i.completed == 1:
                query = model.ChecklistItem.update(completed=0, lastupdated=get_date_time(datetime.utcnow()), lastupdatedby=get_current_user()).where(model.ChecklistItem.id == i.id)
                query.execute()


app.jinja_env.filters['formatdatetime'] = format_date_time
app.jinja_env.filters['getusername'] = get_user_name
    
@app.before_request
def before_request():
    model.database.connect()

@app.after_request
def after_request(response):
    model.database.close()
    return response

@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )


@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/boards')
def boards():
    boards = model.Board.select().order_by(model.Board.name)
    return render_template(
        'boards.html',
        title='Boards',
        boards = boards)

@app.route('/')
def slash():
    return board(1)

@app.route('/board/<board_id>')
def board(board_id):
    """Renders the board page."""
    streams = model.Stream.select().where(model.Stream.parentboard==board_id).order_by(model.Stream.order_in_board)
    sdict = {}
    uiStreams = []
    for stream in streams:
        uistr = get_UI_stream(stream.id)
        uiStreams.append(uistr)

    return render_template(
        'board.html',
        title='Project',
        year=datetime.now().year,
        message='This is a project.',
        streams=streams,
        sdict = sdict,
        uis = uiStreams

    )

@app.route('/new_board')
def new_board():
    return render_template('new_board.html')

@app.route('/add_board')
def add_board():
    return boards()

def get_current_user():
    return 2

def get_next_feature_id(parentStreamId):
    stream = model.Stream.get(model.Stream.id == parentStreamId)
    project = model.Project.get(model.Project.id == stream.parentboard)
    stem = project.gitstem
    featureId = project.lastId
    featureId = featureId + 1
    query = model.Project.update(lastId = featureId).where(model.Project.id == project.id)
    query.execute()
    return stem + "-" + str(featureId).zfill(3)

def set_item_from_data(item, data):
    item.name = data['name']
    item.title = data['name']
    item.description = data['description']
    item.lastupdated = get_date_time(datetime.utcnow())
    item.lastupdatedby = get_current_user()
    item.parentstream = data['parentStream']
    item.itemtype = int(data['itemtype'])
    

@app.route('/save_item', methods=['POST'])
def save_item():
    data = request.form
    item_id = data['itemid']
    
    if (item_id == '-1'):
        new_item = model.Item()
        new_item.created = get_date_time(datetime.utcnow())
        new_item.reportedby = get_current_user()
        new_item.featureId = get_next_feature_id(data['parentStream'])
    else:
        new_item = model.Item.get(model.Item.id == item_id)

    set_item_from_data(new_item, data)
    new_item.save()

    if (data['newcomment'] != ''):
        new_comment = model.Comment()
        new_comment.comment = data['newcomment']
        new_comment.lastupdated = get_date_time(datetime.utcnow())
        new_comment.lastupdatedby = get_current_user()
        new_comment.parentitem = new_item.id
        new_comment.save()

    if (data['newchecklistitem']):
        new_checklistitem = model.ChecklistItem()
        new_checklistitem.checklisttext = data['newchecklistitem']
        new_checklistitem.lastupdated = get_date_time(datetime.utcnow())
        new_checklistitem.lastupdatedby = get_current_user()
        new_checklistitem.parentitem = new_item.id
        new_checklistitem.completed = 0
        new_checklistitem.save()

    update_checklist_items(item_id, data)

    stream_id = data['parentStream']
    uistr = get_UI_stream(stream_id)

    return render_template(
        'partial/stream.html',
        stream=uistr
    )
@app.route('/move_item')
def move_item():
    # item-<parent-id>-<item-id>
    old_pos = request.args.get("old_pos")
    # 4
    new_pos = request.args.get("new_pos")
    # stream-4
    parent = request.args.get("new_parent")

    old_parts = old_pos.split("-")
    item_id = old_parts[2]
    parent_id = parent.split("-")[1]

    uncompleted_checklist_count = dbchecklist = model.ChecklistItem.select().where(model.ChecklistItem.parentitem == item_id and model.ChecklistItem.completed == 0).count()

    query = model.Item.update(orderInStream=model.Item.orderInStream+1).where(model.Item.parentstream == parent_id and model.Item.orderInStream >= new_pos )
    query.execute()

    lud = get_date_time(datetime.utcnow())
    ludb = get_current_user()
    query = model.Item.update(parentstream=parent_id, orderInStream=new_pos, lastupdated=lud, lastupdatedby=ludb).where(model.Item.id == item_id)
    query.execute()

    uistr = get_UI_stream(parent_id)
    return render_template(
        'partial/stream.html',
        stream=uistr
    )


@app.route('/get_item')
def get_item():   
    item_id = request.args.get("id")
    item = model.Item.get(model.Item.id == item_id)
    dbcomments = model.Comment.select().where(model.Comment.parentitem == item_id).order_by(model.Comment.lastupdated.desc())
    dbchecklist = model.ChecklistItem.select().where(model.ChecklistItem.parentitem == item_id).order_by(model.ChecklistItem.lastupdated.desc())
    comments = []
    for i in dbcomments:
        lu = format_date_time(i.lastupdated)
        lub = get_user_name(i.lastupdatedby)

        comments.append(uiComment(i.id, i.comment, lu, lub))

    checklist = []
    for i in dbchecklist:
        lu = format_date_time(i.lastupdated)
        lub = get_user_name(i.lastupdatedby)
        checklist.append(uiChecklistItem(i.id, i.checklisttext, lu, lub, i.completed))

    d = model_to_dict(item)
    d['lastupdated'] = format_date_time(d['lastupdated']) + " " + get_user_name(d['lastupdatedby'])
    d['comments'] = comments
    d['checklist'] = checklist
    retval = json.dumps(d, default=jdefault)
   
    return retval
