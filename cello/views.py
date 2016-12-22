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
    def __init__(self, id, name, items):
        self.id = id
        self.name = name
        self.items = items

class uiComment:
    def __init__(self, id, comment, lastupdated, lastupdatedby):
        self.id = id
        self.comment = comment
        self.lastupdated = lastupdated
        self.lastupdatedby = lastupdatedby

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

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

@app.route('/')
@app.route('/project')
def project():
    """Renders the project page."""
    streams = model.Stream.select().order_by(model.Stream.order_in_board)
    sdict = {}
    uiStreams = []
    for stream in streams:
        stream_items = model.Item.select().where(model.Item.parentstream == stream.id).order_by(model.Item.orderInStream)
        si = []
        for i in stream_items:
            si.append(i)

        print ("Stream: " + stream.name ) 

        print (si)
        sdict[stream.name] = stream_items
        uistr = uiStream(stream.id, stream.name, si)

        uiStreams.append(uistr)

    return render_template(
        'project.html',
        title='Project',
        year=datetime.now().year,
        message='This is a project.',
        streams=streams,
        sdict = sdict,
        uis = uiStreams

    )

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

    stream_id = data['parentStream']

    stream = model.Stream.get(model.Stream.id == stream_id)
    stream_items = model.Item.select().where(model.Item.parentstream == stream_id).order_by(model.Item.orderInStream)
    si = []
    for i in stream_items:
        si.append(i)

    print ("Stream: " + stream.name ) 

    print (si)   
    uistr = uiStream(stream.id, stream.name, si)

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

    query = model.Item.update(orderInStream=model.Item.orderInStream+1).where(model.Item.parentstream == parent_id and model.Item.orderInStream >= new_pos )
    query.execute()
    query = model.Item.update(parentstream=parent_id, orderInStream=new_pos).where(model.Item.id == item_id)
    query.execute()

    return ""

@app.route('/get_item')
def get_item():   
    item_id = request.args.get("id")
    item = model.Item.get(model.Item.id == item_id)
    dbcomments = model.Comment.select().where(model.Comment.parentitem == item_id).order_by(model.Comment.lastupdated.desc())
    comments = []
    for i in dbcomments:
        lu = format_date_time(i.lastupdated)
        lub = get_user_name(i.lastupdatedby)

        comments.append(uiComment(i.id, i.comment, lu, lub))

    d = model_to_dict(item)
    d['lastupdated'] = format_date_time(d['lastupdated']) + " " + get_user_name(d['lastupdatedby'])
    d['comments'] = comments
    retval = json.dumps(d, default=jdefault)
   
    return retval
    