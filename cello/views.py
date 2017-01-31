"""
Routes and views for the flask application.
"""
import os
from datetime import datetime
import json
from flask import render_template, request, jsonify
from flask_peewee.auth import Auth
from playhouse.shortcuts import *
from cello import app, model, auth
import cello.model
from builtins import print


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class uiIdValue:
    def __init__(self, id, value):
        self.id = id
        self.value = value

class uiStream:
    def __init__(self, id, name, allow_direct_add, can_edit, is_completed_stream, items):
        self.id = id
        self.name = name
        self.allow_direct_add = (allow_direct_add and can_edit)
        self.can_edit = can_edit
        self.is_completed_stream = is_completed_stream
        self.items = items

class uiItem:
    def __init__(self, id, type, featureId, name, lastupdated, lastupdatedby, assignedto, checklistitemcount, checklistitemcompleted, checklisttext, description, comments, parentitemtext, childitemtext, priority, age):
        self.id = id
        self.type = type
        self.featureId = featureId
        self.name = name
        self.lastupdated = lastupdated
        self.lastupdatedby = lastupdatedby
        if assignedto is None:
            self.assignedto = -1
        else:
            self.assignedto = assignedto

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
        self.parentitemtext = parentitemtext
        self.childitemtext = childitemtext
        self.priority = priority
        self.age = age

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

def get_days_difference(t):
    if t is None:
        return 999

    y = t // 10000000000
    mon = (t // 100000000) % 100
    d = (t // 1000000) % 100
    h = (t // 10000) % 100
    m = (t // 100) % 100
    s = t % 100

    then = datetime(y, mon, d, h, m, s)
    diff = datetime.utcnow() - then
    days = diff.days
    return days
    
def get_user_name(u):
    if u is None or u == -1:
        return ""

    user = model.UserPrefs.get(model.UserPrefs.id == u)
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

def get_UI_stream(stream_id, canEdit, filter_tag, sort_order, search_term):
    stream = model.Stream.get(model.Stream.id == stream_id)
    is_completed_stream = False
    if stream.stream_type == 4: #  TODO Fix hard coded 
        orderby = model.Item.lastupdated.desc()
        is_completed_stream = True
    else:
        if sort_order == '1':
            orderby = SQL('priority, lastupdated desc')
        elif sort_order == '2':
            orderby = SQL('priority, assignedto desc')
        elif sort_order == '3':
            orderby = SQL('assignedto desc, priority')

    if filter_tag == 'all':
        stream_items = model.Item.select().where(model.Item.parentstream == stream_id).order_by(orderby)
    elif filter_tag == 'mine':
        cu = get_current_user()
        stream_items = model.Item.select().where((model.Item.parentstream == stream_id) & (model.Item.assignedto == cu)).order_by(orderby)
    else:        
        stream_items = model.Item.select().where((model.Item.parentstream == stream_id) & (model.Item.assignedto == filter_tag)).order_by(orderby)

    si = []
    for i in stream_items:
        item_wanted = False
        if (search_term is None or search_term == ''):
            item_wanted = True
        else:
            if search_term in i.name:
                item_wanted = True
            elif search_term in i.description:
                item_wanted = True

        checklisttotal, checklistitemcompleted, checklisttext = get_checklist_info(i.id)
        if not item_wanted:
            if search_term in checklisttext:
                item_wanted = True

        comments = get_comment_info(i.id)
        if not item_wanted:
            if search_term in comments:
                item_wanted = True

        if not item_wanted:
            continue

        if i.parentId is None or i.parentId == -1:
            parentItem = ""
        else:
            parent = model.Item.get(model.Item.id == i.parentId)
            parentItem = parent.featureId + "/" + parent.name

        childitemtext = ""
        children = model.Item.select().where(model.Item.parentId == i.id)
        for c in children:
            child = c.featureId + "/" + c.name
            childitemtext = childitemtext + child + "<br/>"

        age = get_days_difference(i.lastupdated)
        uii = uiItem(i.id, i.itemtype, i.featureId, i.name, i.lastupdated, i.lastupdatedby, i.assignedto, checklisttotal, checklistitemcompleted, checklisttext, i.description, comments, parentItem, childitemtext, i.priority, age)
        si.append(uii)

    print ("Stream: " + stream.name ) 

    print (si)   
    uistr = uiStream(stream.id, stream.name, stream.allow_direct_add, canEdit, is_completed_stream, si)
    return uistr

def get_UI_teams(current_user):
    teamIds = get_users_teams(current_user) 
    teams = model.Team.select().where(model.Team.id  << teamIds).order_by(model.Team.name)

    uiTeams = []
    private = uiIdValue(-1, "Private Board")
    uiTeams.append(private)
    for team in teams:
        id = team.id
        value = team.name
        t = uiIdValue(id, value)
        uiTeams.append(t)

    return uiTeams

def get_ui_team_members(team_id):
    team_user_ids = model.TeamMembers.select().where(model.TeamMembers.teamId == team_id)
    uiTeamUsers = []
    for tid in team_user_ids:
        user = model.UserPrefs.get(model.UserPrefs.id == tid.userId)
        uname = uiIdValue(user.id, user.name)
        uiTeamUsers.append(uname)

    return uiTeamUsers

def can_user_edit_board(board, current_user, uiTeams):
    canEdit = False
    if board.createdby == current_user:
        canEdit = True
    else:
        for team in uiTeams:
            if team.id == board.team:
                canEdit = True
                break

    return canEdit

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

def create_standard_streams(board_id):
    proposed = model.Stream()
    proposed.parentboard = board_id
    proposed.name="Proposed"
    proposed.order_in_board = 1
    proposed.allow_direct_add = 1
    proposed.stream_type = 1
    proposed.save()

    backlog = model.Stream()
    backlog.parentboard = board_id
    backlog.name="Backlog"
    backlog.order_in_board = 2
    backlog.allow_direct_add = 1
    backlog.stream_type = 2
    backlog.save()

    inprogress = model.Stream()
    inprogress.parentboard = board_id
    inprogress.name="In Progress"
    inprogress.order_in_board = 3
    inprogress.allow_direct_add = 1
    inprogress.stream_type = 3
    inprogress.save()

    completed = model.Stream()
    completed.parentboard = board_id
    completed.name="Completed"
    completed.order_in_board = 4
    completed.allow_direct_add = 0
    completed.stream_type = 4
    completed.save()

    notdone = model.Stream()
    notdone.parentboard = board_id
    notdone.name="Will Not Be Done"
    notdone.order_in_board = 5
    notdone.allow_direct_add = 0
    notdone.stream_type = 5
    notdone.save()


app.jinja_env.filters['formatdatetime'] = format_date_time
app.jinja_env.filters['getusername'] = get_user_name

"""    
@app.before_request
def before_request():
    model.database.connect()

@app.after_request
def after_request(response):
    model.database.close()
    return response
"""
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
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

@auth.login_required
@app.route('/boards')
def boards():
    currentuser = get_current_user()
    privateboards = model.Board.select().where( (model.Board.createdby == currentuser) & (model.Board.isprivate==1)).order_by(model.Board.name)
    myteams = get_users_teams(currentuser)
    teamboards = model.Board.select().where(model.Board.team << myteams).order_by(model.Board.name)
    otherboards = model.Board.select().where((~(model.Board.team << myteams)) & (model.Board.isprivate == 0) & (model.Board.createdby != currentuser)).order_by(model.Board.name)
    return render_template(
        'boards.html',
        title='Boards',
        currentuser = currentuser,
        privateboards = privateboards,
        teamboards = teamboards,
        otherboards = otherboards)


@app.route('/')
@auth.login_required
def slash():
    userId = get_current_user()
    user = model.UserPrefs.get(model.UserPrefs.id == userId)
    boardId = user.defaultboard
    return board(boardId)

@app.route('/board/<board_id>', strict_slashes=False)
@app.route('/board/<board_id>/<filter_tag>', strict_slashes=False)
@app.route('/board/<board_id>/<filter_tag>/<sortorder>', strict_slashes=False)
@app.route('/board/<board_id>/<filter_tag>/<sortorder>/<searchterm>', strict_slashes=False)
def board(board_id, filter_tag='all', sortorder='1', searchterm=''):
    """Renders the board page."""
    streams = model.Stream.select().where(model.Stream.parentboard==board_id).order_by(model.Stream.order_in_board)
    board = model.Board.get(model.Board.id==board_id)

    current_user = get_current_user()
    uiTeams = get_UI_teams(current_user)
    canEdit = can_user_edit_board(board, current_user, uiTeams)
    ui_team_users = get_ui_team_members(board.team)

    sdict = {}
    uiStreams = []
    for stream in streams:
        uistr = get_UI_stream(stream.id, canEdit, filter_tag, sortorder, searchterm)
        uiStreams.append(uistr)

    
    return render_template(
        'board.html',
        board_name=board.name,
        board_id = board_id,
        title='Board',
        year=datetime.now().year,
        message='This is a board.',
        can_edit = canEdit,
        filter_tag = filter_tag,
        sort_order = sortorder,
        search_term = searchterm,
        streams=streams,
        team_users = ui_team_users,
        sdict = sdict,
        uis = uiStreams

    )

@app.route('/new_board')
def new_board():
    current_user = get_current_user()
    uiTeams = get_UI_teams(current_user)

    return render_template(
        'edit_board.html',
        name = '',
        currentteam = -1,
        id = -1,
        default_board=False,
        teams = uiTeams,
        is_private = False)

@app.route('/edit_board/<board_id>')
def edit_board(board_id):
    board = model.Board.get(model.Board.id == board_id)
    current_user = get_current_user()
    uiTeams = get_UI_teams(current_user)
    canEdit = can_user_edit_board(board, current_user, uiTeams)
    if canEdit == False:
        raise InvalidUsage('You cannot edit this board', status_code=403)

    return render_template(
        'edit_board.html',
        name = board.name,
        currentteam = board.team,
        id = board_id,
        default_board=False,
        teams = uiTeams,
        is_private = (board.isprivate == 1))

@app.route('/save_board', methods=['POST'])
def save_board():
    data = request.form
    id = data['board_id']
    name = data['boardname']
    teamid = data['team']
    if teamid == -1:
        teamid = None

    if (id == '-1'):
        parent = 1
        new_board = model.Board()
        new_board.name = name
        new_board.parentproject = parent
        new_board.gitstem = data['gitstem']
        new_board.lastId = 1
        new_board.team = teamid
        if ('is_private' in data):
            new_board.isprivate = 1
        else:
            new_board.isprivate = 0
        new_board.createdby = get_current_user()
        new_board.save()

        create_standard_streams(new_board.id)
    else:
        board = model.Board.get(model.Board.id == id)
        current_user = get_current_user()
        uiTeams = get_UI_teams(current_user)
        canEdit = can_user_edit_board(board, current_user, uiTeams)
        if canEdit == False:
            raise InvalidUsage('You cannot edit this board', status_code=403)

        board.name = name
        board.team = teamid
        board.save()

    return boards()

def get_current_user():
    user = auth.get_logged_in_user()
    return user.id
    
def get_users_teams(userId):
    teams = model.TeamMembers.select(fn.Distinct(model.TeamMembers.teamId)).where(model.TeamMembers.userId == userId)    
    return teams

def get_next_feature_id(parentStreamId):
    stream = model.Stream.get(model.Stream.id == parentStreamId)
    board = model.Board.get(model.Board.id == stream.parentboard)
    stem = board.gitstem
    featureId = board.lastId
    featureId = featureId + 1
    query = model.Board.update(lastId = featureId).where(model.Board.id == board.id)
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
    item.parentId = int(data['parent-item'])
    item.assignedto = int(data['assigned-to'])
    item.priority = int(data['priority'])
    

@app.route('/save_item', methods=['POST'])
def save_item():
    data = request.form
    item_id = data['itemid']
    
    if (item_id == '-1'):
        new_item = model.Item()
        new_item.created = get_date_time(datetime.utcnow())
        new_item.reportedby = get_current_user()
        item_type = int(data['itemtype'])
        if item_type == 1 or item_type == 2:
            new_item.featureId = get_next_feature_id(data['parentStream'])
        else:
            new_item.featureId = ""
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
    item_filter = data['item_filter']
    sort_order = data['sort_order']
    search_term = data['search_term']
    uistr = get_UI_stream(stream_id, True, item_filter, sort_order, search_term)

    return render_template(
        'partial/stream.html',
         can_edit = True,
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
    filter_tag = request.args.get("item_filter")
    sort_order = request.args.get("sort_order")
    search_term = request.args.get("search_term")
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

    item = model.Item.get(model.Item.id == item_id)
    parent = model.Stream.get(model.Stream.id == parent_id)

    if (item.assignedto is None or item.assignedto == -1) and parent.stream_type == 3:      # TODO fix 3 == inprogress
        query = model.Item.update(assignedto=ludb).where(model.Item.id == item_id)
        query.execute()

    uistr = get_UI_stream(parent_id, True, filter_tag, sort_order, search_term)
    return render_template(
        'partial/stream.html',
        can_edit = True,
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
    if item.parentId is None:
        d['parentId'] = -1

    d['lastupdated'] = format_date_time(d['lastupdated']) + " " + get_user_name(d['lastupdatedby'])
    if item.assignedto is None:
        d['assignedto'] = -1;

    d['comments'] = comments
    d['checklist'] = checklist
    retval = json.dumps(d, default=jdefault)
   
    return retval

@app.route('/get_potential_parents')
def get_potential_parents():   
    item_id = request.args.get("id")
    stream_id = request.args.get("sid")
    stream = model.Stream.get(model.Stream.id == stream_id)
    board = model.Board.get(model.Board.id == stream.parentboard)
    board_stream_ids = model.Stream.select(fn.Distinct(model.Stream.id)).where(model.Stream.parentboard==board.id)
    
    parr =  []
    potentials = model.Item.select().where((model.Item.parentstream << board_stream_ids) & (model.Item.id != item_id)).order_by(model.Item.name)
    for p in potentials:
        id = p.id
        name = p.featureId + "/" +  p.name
        up = uiIdValue(id, name)
        parr.append(up)

    retval = json.dumps(parr, default=jdefault)
    return retval

@app.route('/get_team_members_from_stream')
def get_team_from_stream():
    stream_id = request.args.get("sid")
    stream = model.Stream.get(model.Stream.id == stream_id)
    team = get_ui_team_members(stream.parentboard)
    retval = json.dumps(team, default=jdefault)
    return retval

ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            now = datetime.now()
            filename = os.path.join(app.config['UPLOAD_FOLDER'], "%s.%s" % (now.strftime("%Y-%m-%d-%H-%M-%S-%f"), file.filename.rsplit('.', 1)[1]))
            file.save(filename)
            return jsonify({"success":True})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS