from flask import url_for, request, render_template, redirect, send_from_directory, g, session, abort, flash, jsonify
from functools import wraps
from lib import *
from coco_scheduling import *
import re
from flask.globals import session, request
from flask_mail import Mail, Message
from db_helper import DBAssistant

# from celery import Celery


app.config.from_object(__name__)

mail_ext = Mail(app)
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)

PERIOD = {}
COLORPREFS = {0: "tomato", 1: "", 2: "yellow", 3: "lightgreen", 5: "lightgrey"}
courseComplete = {}  # for the current lecturer: dictionary for courses and resp. preferences for each of them
hrs = {}  # hours per week for every course of current lecturer (who is logged in now)
markedTimes = {}
allSolutions = []
incr = 0
newPrefs = 0

app.config.from_envvar('COCO_SETTINGS', silent=True)
db_assist = DBAssistant()


# request login
def login_required(f):
    """
    A decorator to disallow accessing restricted pages without being authenticated.
    :param f: a function to be decorated
    :return: a wrapper
    """

    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first')
            return redirect(url_for('log'))

    return wrap


# Redirect to index page
@app.route("/")
def home():
    """
    Route function for the home page.
    :return: redirects to the function that renders the index.
    """
    return redirect(url_for("index"))


@app.route("/index")
def index():
    """
    Route function for the index, it renders the index view and check if you are logged in already
    redirects to the respective users view.
    :return:
    """

    if 'logged_in' in session:
        passwd1 = db_assist.get_single('select password from users where id = 1')[0]
        passwd2 = db_assist.get_single('select password from users where id = 2')[0]
        if not passwd1[0] == '$':
            passwd1 = bcrypt.generate_password_hash(str(passwd1))
            db_assist.update('update users set password = ? where id = 1', [passwd1])

        if not passwd2[0] == '$':
            passwd2 = bcrypt.generate_password_hash(str(passwd2))
            db_assist.update('update users set password = ? where id = 2', [passwd2])
        if session['type'] == 0:
            return redirect(url_for('coordinators'))
        elif session['type'] == 1:
            return redirect(url_for('lecturers'))
    return render_template("index.html")


# Process values from Register page
@app.route("/register", methods=['POST'])
def register():
    """
    The registeration function, takes in fields(e.g name, username, password etc)
    from the registration view and commits to the database if user does not exist,
    else it flashes and error message.
    :var: name: name read from the html name field string
    :var: username: username read from the html name field string
    :var: password: user password from form string
    :var: email: user email from form string
    :var: types: user type 1 or 0, coordinator-0 lecturer-1
    :var: title: user title string
    :return:
    """
    name = request.form['name'].strip()
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    email = request.form['email'].strip()
    types = request.form.get('type')

    title = request.form.get('title')
    len_email = len(email)
    if not name or not email or not username or not password or not types or not title:
        flash('Please fill all the fields')
        return redirect(url_for('reg'))
    if (len_email < 7) or re.match("^.+@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) is None:
        flash('Wrong Email')
        return redirect(url_for('reg'))
    if not title:
        title = None
    passwd = request.form['password']
    # TODO: EMA: Password hashing # aleady done by good samaritan

    # passphrase is a column inside passphrase table in db
    # passphrase is also a text that a new coordinator needs to register into the system.
    passp = db_assist.get_single('select passphrase from passphrase')
    passphrase = passp if not passp else passp[0]
    v = db_assist.get_single('select * from users where username = ?', [request.form['username']])
    val = v if not v else v[0]

    if val is not None:
        flash('User/Username already exists')
        return redirect(url_for('reg'))
    if request.form["confirmpass"] != "" and request.form['password'] != "":
        if passwd != request.form['confirmpass']:
            flash('Password mismatch')
            return redirect(url_for('reg'))
    # coordinator registration
    if request.form['type'] == '0':
        try:
            if bcrypt.check_password_hash(passphrase, request.form['passphrase']):
                db_assist.update(
                    'insert into users (title, name, username, password, email, type) values (?, ?, ?, ?, ?, ?)',
                    [title, request.form['name'], request.form['username'],
                     bcrypt.generate_password_hash(request.form['password']),
                     request.form['email'], request.form['type']])

                flash('Registration successful')
                return redirect(url_for('log'))
            else:
                flash("Wrong passphrase!")
                return redirect(url_for('reg'))
        except:
            flash("Wrong passphrase!")
            return redirect(url_for('reg'))
    # lecturer registration
    if request.form['type'] == '1':
        db_assist.update('insert into users (title, name, username, password, email, type) values (?, ?, ?, ?, ?, ?)',
                         [title, name, username, bcrypt.generate_password_hash(password), email, types])
        flash('Registration successful')
        return redirect(url_for('log'))
    flash('Fields are empty')
    return redirect(url_for('reg'))


@app.route("/reg")
def reg():
    """
    Renders the registration view when user click on register
    :return: render_template()
    """
    return render_template("register.html")


@app.route("/log")
def log():
    """
    Renders the login view when user click on view
    :return: render_template()
    """
    return render_template("login.html")


@app.route("/login", methods=['GET', 'POST'])
def login():  # On login function
    u = db_assist.get_single('select username from users where username = ?', [request.form['username']])
    user_name = u if not u else u[0]
    times = db_assist.get_all(
            'select timeslot_id, time from timeslots order by timeslot_id asc')  # here we initialize the PERIOD dictionary
    for time in times:
        PERIOD[time[0]] = time[1]

    if user_name is not None:
        m = db_assist.get_single('select password from users where username = ?', [request.form['username']])
        passwd = m if not m else m[0]  # deal with none or value in a tuple
        r = db_assist.get_single('select type, id from users where username = ?', [request.form['username']])
        g.user_type = r[0]  # get user type
        session['user_id'] = r[1]  # get user ID !! DO NOT REMOVE
        username = request.form['username']
        error = None
        if request.method == 'POST':
            try:
                test_passwd = bcrypt.check_password_hash(passwd, request.form['password'])
            except:
                test_passwd = False
            if not test_passwd:
                error = 'Invalid Password'
            else:
                session['logged_in'] = True
                session['type'] = g.user_type
                session['user'] = username
                flash('You are logged in')
                if g.user_type == 1:
                    return redirect(url_for('lecturers'))
                if g.user_type == 0:
                    return redirect(url_for('coordinators'))
    else:
        error = "Wrong User Name!"
    return render_template("login.html", error=error)


@app.route("/changepassword")
def changepassword():
    return render_template("change_password.html")


@app.route("/passwordchanged", methods=['POST', 'GET'])
def change_password():
    oldpassword = request.form['Old password']
    newpassword = request.form['New password']
    confirmpassword = request.form['Confirm password']
    cur = db_assist.get_single('select password from users where username = ?', [session['user']])
    if 'user' in session:
        if len(newpassword) > 5:
            if len(cur) > 0 and bcrypt.check_password_hash(cur['password'], oldpassword):
                if newpassword == confirmpassword:
                    db_assist.update('Update users set password=? where username=?',
                                     [bcrypt.generate_password_hash(request.form['New password'].strip()),
                                      session['user']])
                    flash("Your password successfully changed!")
                    return redirect(url_for('log'))

                else:
                    flash("new password and confirm password mismatch")
                    return render_template("change_password.html")

            else:
                flash("old password mismatch")
                return render_template("change_password.html")
        else:
            flash("please enter password with at least six characters")
            return render_template("change_password.html")
    else:
        flash("please first login")
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You are logged out')
    return redirect(url_for('index'))


@app.context_processor
def utility_processor():
    def rowspan(prefs):
        """
        This function returns number of keys in dictionary and dynamically passes in to the web page
        
        :param: prefs:dicitonary - dictionary, in which we count keys
        :return: :int - amount of keys in the input dictionary
        """
        return len(prefs) + 1

    return dict(rowspan=rowspan)


@app.route("/pref")
@login_required
def pref():
    """
    This function collects the preferences of the lecturers, structure and sends to the coordinator
    view responsible for presenting in a given manner.
    :param null
    :var client - the user type accessing this function.
    :var prefs - the prefereces gotten from the database
    :var list_pref - the data from preferences we actually need in a list of a tuple structure
    :var p - the dictionary of a dictionary of a list of a tuple, containing our data to present.
    :return: p

    """
    client = "Coordinator"

    set_current_semester()
    prefs = db_assist.get_all("select p.timeslot_id, courses.course, p.weekday_id, p.preference_id \
     from courses, preferences p where courses.id = p.course_id \
     and p.semester_id = " + session['current_semester'])
    p = Library.form_marks(prefs, COLORPREFS, True, True, False)

    return render_template("preferences.html", prefs=p, times=list(PERIOD.values()), client=client)


@app.route("/get-prefs", methods=['POST', 'GET'])
@login_required
def get_prefs():
    """
    Gets the preferences and inputs to database.
    :param null
    :var course - selected course id
    :var hrs - selected hours per week
    :var courseComplete - dictionary for preferences loaded from DB for current user and current semester
    :var preferences - the prefereces from the user input
    :var pref_2 - temporary array for updating data in database
    :var upd - array with preferences to be updated with the new value
    :var rmv - array with preferences to be deleted
    :return void

    """
    try:
        course = request.form["courses"]
        hrs_ = request.form["hours"]
        if course is None or hrs is None:
            raise Exception("Required fields are empty")
    except:
        return ('', 204)
    else:
        global newPrefs
        g.user_id = str(session['user_id'])
        cur_semester = str(session['current_semester'])
        preferences = Library.read_timeslot_marks(request, '1', False)
        pref_2 = []

        if preferences:
            # exclude preferences, that already exist in DB
            upd = []
            rmv = []
            pref = []
            if courseComplete:
                if int(course) in courseComplete:
                    c = courseComplete[int(course)]
                    pref = Library.handle_duplicates(preferences, c)
                    preferences = pref[0]
                    upd = pref[1]
                    rmv = pref[2]

            if preferences:
                list(map(lambda c:
                         pref_2.append((g.user_id, c[0], c[1], c[2], course, hrs_, cur_semester)), preferences))
                if pref_2:
                    db_assist.change_data("insert into preferences (user_id, weekday_id, timeslot_id, preference_id, course_id, hours, semester_id) \
                           values (?, ?, ?, ?, ?, ?, ?)", pref_2)
                    pref_2 = []
            if upd:
                list(map(lambda c:
                         pref_2.append((c[2], hrs_, course, c[0], c[1], cur_semester)),
                         upd))  # pref_id, course, weekday, timeslot
                if pref_2:
                    db_assist.change_data("update preferences set preference_id = ?, hours = ? \
                        where course_id = ? and weekday_id = ? and timeslot_id = ? and semester_id = ?", pref_2)
                    pref_2 = []

            if hrs:
                if int(course) in hrs:
                    if hrs[int(course)] != hrs_:
                        pref_2.append((hrs_, course, cur_semester))
                        db_assist.change_data("update preferences set hours = ? where \
                        course_id = ? and semester_id = ?", pref_2)
                        pref_2 = []
            if rmv:
                list(map(lambda c:
                         pref_2.append((course, c[0], c[1], cur_semester)),
                         rmv))  # course, weekday, timeslot
                if pref_2:
                    db_assist.change_data("delete from preferences \
                        where course_id = ? and weekday_id = ? and timeslot_id = ? and semester_id = ?", pref_2)
            flash("Preferences saved", category='success')
            newPrefs = 1
            return redirect(url_for('lecturers'))
        else:
            # if int(course) not in courseComplete:  # if the preferences were not saved yet
            return ('', 204)


@app.route("/add-pref", defaults={'courses': None}, methods=['POST', 'GET'])
@app.route("/add-pref/<courses>", methods=['POST', 'GET'])
@login_required
def add_pref(courses):
    # TODO: refactor!
    """

    Shows interface for lecturer. If current user already saved preferences in current semester, load them.
    Otherwise open intermediate window to set preferences.
    :param courses - list of courses, for which preferences are set by current user for current semester
    :var client - the user type accessing this function.
    :var courses_list - list of courses, for which preferences are not set or set by current user
    :var semester_set - indicates if the current semester is set
    :var times - list of timeslots, available to set the preferences
    :var hrs - hours per week for the first course with saved preferences
    :var current - the first course (name) with saved preferences
    :var prefs - preferences (dictionary for: day of week -> timeslot -> value) for the first course with saved preferences
    :return client, times, courses_list, current, prefs, hrs, semester_set

    """
    add = True
    courses_list = db_assist.get_all("select id, course from courses where id not in (select course_id from preferences \
                    where user_id <> " + str(session['user_id']) + " and semester_id = " + str(
            session['current_semester']) + ") order by id desc")
    busy_ = db_assist.get_all("select b.weekday_id, b.timeslot_id, 1, r.comment from busy_timeslots b, reasons r\
                    where b.semester_id = " + str(session['current_semester']) + " and b.reason_id = r.reason_id")
    # if there are several reasons for one timeslot, concatenate reasons
    busy_times = Library.form_marks(busy_, None, True, False, False)  # add here the reason text, call with parameter

    client = "Lecturer"
    # add = True
    temp = -1
    temp2 = []
    temp_hrs = ''
    if courses:  # show preferences from DB
        p = {}
        for crs in courses:
            prefs = db_assist.get_all("select weekday_id, timeslot_id, preference_id, hours from preferences \
                        where course_id = " + str(crs[0]) + " and semester_id = " + str(session['current_semester']) +
                                      " and user_id =" + str(session['user_id']))
            p = Library.form_marks(prefs, COLORPREFS, False, False, False)

            hrs[crs[0]] = prefs[0][3]
            courseComplete[crs[0]] = p

    try:
        selectedCourse = request.get_json()
    except:
        selectedCourse = None
    else:
        if selectedCourse is not None:
            temp = int(selectedCourse)
            if temp in courseComplete:
                temp2 = courseComplete[temp]
            else:
                temp2 = []
            if temp in hrs:
                temp_hrs = hrs[temp]
        else:
            if courses:
                temp = courses[0][0]  # first course
                temp2 = courseComplete[temp]  # [0][0][0] = value [0][0][1] = color
                temp_hrs = hrs[temp]
                flash("Your current preferences are shown below")
    return render_template("lecturers.html", client=client, add=add, times=list(PERIOD.values()),
                           courses=courses_list, current=temp, prefs=temp2, hrs=temp_hrs,
                           semester_set=True, busy_times=busy_times)


@app.route("/lecturers", methods=['POST', 'GET'])
@login_required
def lecturers():
    """

    Checks if there exist preferences for current user for current semester.
    If preferences exist, load the list of courses. Redirects to page for setting/changing preferences
    :param null
    :var client - the user type accessing this function.
    :var m - current semester id
    :var courses - list of courses, for which current user already set preferences for current semester
    :var semester_set - indicates if the current semester is set
    :return courses, semester_set

    """
    client = 'Lecturer'
    m = db_assist.get_single("select id from sessions where current = 1")
    if m is None:
        flash("The current semester is not set yet. Your preferences cannot be saved")
        return render_template("lecturers.html", client=client, semester_set=False)

    session['current_semester'] = m if not m else m[0]
    courses = db_assist.get_all("select distinct course_id from preferences where user_id=? and semester_id=?",
                                [str(session['user_id']), str(session['current_semester'])])

    if not courses:
        return render_template("lecturers.html", client=client, semester_set=True)
    else:
        return add_pref(courses)


@app.route("/coordinators", methods=['GET', 'POST'])
@login_required
def coordinators():
    """
    This function opens coordinator view to select semester.
    :return redirect to coordinator menu for the chosen semester
    """
    session['home'] = 1
    client = 'Coordinator'
    semesters = db_assist.get_all(
        'select s.id, st.semester, s.years from sessions s, semester_types st where s.semester = st.id order by s.id desc')
    return render_template("coordinator.html", client=client, semesters=semesters)


@app.route("/coordinator_menu", methods=['GET', 'POST'])
@login_required
def coordinator_menu():
    """
    This function routes to the coordinator menu page.

    :param null
    :var session - the session instance
    :var courses - the list of courses gotten from the database
    :var lecturers - the list of lecturers gotten from the database
    :return: redirect to coordinator menu page

    """
    client = 'Coordinator'
    session['home'] = 0
    set_current_semester()
    courses = db_assist.get_all('select course, field, students_number from courses order by id desc')
    lecturers = db_assist.get_all('select name from users where type = 1 order by id desc')
    return render_template('coordinator_menu.html', client=client, courses=courses, lecturers=lecturers)


@app.route("/mark_timeslots", methods=['POST', 'GET'])
@login_required
def mark_timeslots():
    """
    Renders the view for marking timeslots as busy.
    :var: client: client type for the given permission to access this page.
    :return: render_template()
    """
    client = "Coordinator"
    set_current_semester()
    reasons = db_assist.get_all("select reason_id, comment from reasons")
    used_reas = db_assist.get_all(
            "select distinct reason_id from busy_timeslots where semester_id = " + session['current_semester'])
    for r in used_reas:
        marks = db_assist.get_all("select weekday_id, timeslot_id, 5, reasons.comment from busy_timeslots, reasons \
                    where reasons.reason_id = busy_timeslots.reason_id and \
                    semester_id = " + session['current_semester'] + " and busy_timeslots.reason_id = " + str(r[0]))
        m = Library.form_marks(marks, COLORPREFS, True, False, False)

        markedTimes[r[0]] = m
    other_reason = False
    try:
        selectedReason = request.get_json()
    except:
        selectedReason = None
    else:
        if selectedReason is not None:
            other_reason = int(selectedReason) == 0
            temp = int(selectedReason)
            if temp in markedTimes:
                temp2 = markedTimes[temp]
            else:
                temp2 = []
        else:
            if used_reas:
                temp = used_reas[0][0]
                temp2 = markedTimes[temp]
            else:
                temp = ""
                temp2 = []
    return render_template("mark_timeslots.html", times=list(PERIOD.values()), client=client, reasons=reasons,
                           prefs=temp2, current=temp, other_reason=other_reason)


@app.route("/save_marks", methods=['POST', 'GET'])
@login_required
def save_marks():
    """
    This function reads and saves marked timeslots.
    :return on success - redirects to the coordinator menu for the current semester;
            else - keeps the user on th current page
    """
    global allSolutions
    try:
        list_reason = request.form["reasons"]
        new_reason = request.form["other_reason"]
        if list_reason is None or (list_reason == '0' and new_reason == ""):
            raise Exception("Required fields are empty")
    except:
        return ('', 204)  # error message is shown by web page
    else:
        marks = Library.read_timeslot_marks(request, '0', False)

        rid = list_reason
        if list_reason == '0':
            db_assist.insert_single('reasons', 'comment', new_reason)
            rid_ = db_assist.get_single("select reason_id from reasons where comment = \"" + new_reason + "\"")
            rid = rid_[0]

            # Handle duplicates
        markr = []
        new = []
        rmv = []
        if markedTimes:
            if int(rid) in markedTimes:
                marks_new = Library.handle_duplicates(marks, markedTimes[int(rid)])
                markn = marks_new[0]
                markr = marks_new[2]
            else:
                markn = marks
        else:
            markn = marks

        list(map(lambda c:
                 new.append((c[0], c[1], rid, str(session['current_semester']))), markn))
        list(map(lambda c:
                 rmv.append((c[0], c[1], rid, str(session['current_semester']))), markr))
        if new:
            db_assist.change_data("insert into busy_timeslots (weekday_id, timeslot_id, reason_id, semester_id) \
                           values (?, ?, ?, ?)", new)
        if rmv:
            db_assist.change_data("delete from busy_timeslots where weekday_id = ? \
                        and timeslot_id = ? and reason_id = ? and semester_id =?", rmv)
        flash("Marks for timeslots were successfully changed", category='success')
        allSolutions = []
        return redirect(url_for('coordinator_menu', **request.args))


@app.route("/save_changed_schedule", methods=['POST', 'GET'])
@login_required
def save_changed_schedule():
    """
    This function reads and saves changes in the current schedule.
    :return on success - redirects to the coordinator menu for the current semester;
            else - keeps the user on th current page
    """
    try:
        marks = Library.read_timeslot_marks(request, '0', True)
        set_current_semester()
        solution = []
        list(map(lambda c:
                 solution.append((c[0], c[1], c[2], c[3], str(session['current_semester']))), marks))
        db_assist.change_data("delete from schedule where semester_id = ?", list(session['current_semester']))
        db_assist.change_data("insert into schedule values (?,?,?,?,?)", solution)
        flash("The schedule was successfully changed", category='success')
        return redirect(url_for('current_schedule', **request.args))
    except:
        flash("Failed to save the schedule", category='error')
        return redirect(url_for('current_schedule', **request.args))


@app.route("/semester")
@login_required
def semester():
    """
    Renders the semester selection view.
    :var: client: client type for the given permission to access this page.
    :return: render_template()
    """
    client = "Coordinator"
    return render_template("new_semester.html", client=client)


@app.route("/passphrase")
@login_required
def update_passphrase():
    """
    Renders the update pass phrase view if the passp value is set to true.
    :var: client: client type for the given permission to access this page.
    :var: passp: boolean
    :return: render_template()
    """
    client = "Coordinator"
    passp = True
    return render_template("coordinator_menu.html", passp=passp, client=client)


@app.route("/passphrase", methods=['POST'])
@login_required
def passphrase():
    """
    Updates the new pass phrase to register as a coordinator if not None in the database.
    :var: error: error message if pass phrase is empty
    :return: render_template()
    :return: redirect()
    """
    error = ""
    if request.form['passphrase'] is not None:
        db_assist.update('update passphrase set passphrase = ? where id = 1',
                         [bcrypt.generate_password_hash(request.form['passphrase'])])
        flash('Passphrase updated!')
    else:
        error = "Passphrase update failed, no value provided"
        return render_template('coordinator_menu.html', error=error)
    return redirect(url_for('coordinator_menu', **request.args))


@app.route("/add-semester", methods=['POST'])
@login_required
def new_semester():
    """
    This function stores a new semester in the database.

    :param null
    :var val - the possible instance of semester from the database
    :return: redirect to coordinators page
    """
    val = db_assist.get_all(
        "select * from sessions where semester = '" + request.form['semester'] + "' and years = '" + request.form[
            'year'] + "'")
    if val.__len__() == 0:
        if request.form['semester'] and request.form['year']:
            db_assist.change_data(
                'update sessions set current = 0')  # ensure there will be only one current semester, the last added one
            semester_type = db_assist.get_single(
                "select id from semester_types where semester = '" + request.form['semester'] + "'")
            db_assist.change_data('insert into sessions (semester, years, current) values (?, ?, 1)',
                                  [semester_type[0], request.form['year']])
            flash("New semester added")
    else:
        flash("Semester already exists")
    return redirect('coordinators')


@app.route("/add-course")
@login_required
def add_course():
    """
    Renders the add course view, if add is true, disable other views.
    :var: add: boolean
    :return: render_template()
    """
    client = "Coordinator"
    add = True
    courses = db_assist.get_all('select id, course, field, students_number from courses order by id desc')
    return render_template("coordinator_menu.html", add=add, courses=courses, client=client)


@app.route("/course", methods=['POST'])
@login_required
def course():
    """
    This function stores a new course in the database.

    :param null
    :var db - the database instance
    :var val - the list of courses gotten from the database
    :return: redirect to coordinator menu page
    """
    val = db_assist.get_all('select * from courses where course = ? and field = ?',
                            [request.form['course'], request.form['field']])
    if val.__len__() == 0:
        db_assist.update('insert into courses (course, field, students_number) values (?, ?, ?)',
                         [request.form['course'], request.form['field'], request.form['estimate']])
        flash("New Course added")
    else:
        flash("Course already exist")
    return redirect(url_for('coordinator_menu', **request.args))


@app.route("/edit-course", methods=['GET', 'POST'])
@login_required
def edit_course():
    add = True
    course_id = request.form.get('course')
    courses = db_assist.get_all('select id, course, field, students_number from courses order by id desc')
    course_edit = db_assist.get_single('select id, course, field, students_number from courses where id =?',
                                       [course_id])
    return render_template('coordinator_menu.html', add=add, courses=courses, course_edit=course_edit)


@app.route("/update-course", methods=['GET', 'POST'])
@login_required
def update_course():
    global allSolutions
    course = request.form['course']
    field = request.form['field']
    estimate = int(request.form['estimate'])
    course_id = int(request.form['id'])
    error = ""
    try:
        db_assist.update('update courses set course=?, field=?, students_number=? where id=?', [course, field, estimate,
                                                                                                course_id])
        flash("Success updating course")
    except Exception as e:
        error = "Error updating course!"
        return render_template('coordinator_menu.html', error=error)
    allSolutions = []
    return redirect(url_for('coordinator_menu', **request.args))


@app.route("/reset")
@app.route("/reset/<string:link>")
def reset(link=None):
    """
    Renders the reset view, based on reset value disable other views when user click on Forgot password
    :var: reset - boolean
    :return: render_template()
    """
    reset = True
    if not link is None:
        cur = db_assist.get_single("select id from users where reset=link")
        print(cur)
    return render_template("login.html", reset=reset, link=link is None)


@app.route("/reset-password", methods=['POST'])
def reset_password():
    """
    This function manages the password recovery feature of an account holder.

    :param null
    :var user_email - the email addresses gotten from the database
    :var error - non existent user message
    :return: redirect to login page
    """
    email = request.form['email']
    e = db_assist.get_single('select email from users where email = ?', [email])
    user_email = e if not e else e[0]
    if user_email is not None:
        error = ""
        host = request.url_root
        one_time = Library.generate_one_time_password()
        subject = "Password Recovery"
        sender_row = db_assist.get_single("select email from users where id = 1")
        mail = Message(subject=subject, sender=sender_row[0], recipients=[user_email])
        mail.body = "Below is a link to reset your password \n\n " \
                    + host + "reset/" + one_time + " Click or copy and paste this link in your browser" \
                                                   "\n\nThis email has been sent automatically, please don't reply."
        try:
            with app.app_context():
                mail_ext.send(mail)
            flash("An email was sent to your mailbox, visit to reset your password")
        except Exception as e:
            print(e)
            flash("Something went wrong with sending the mail", category='error')
    else:
        error = "User does not exist!"
    return render_template("login.html", error=error)


@app.route("/resetting", methods=['POST'])
def resetting():
    passwd = request.form['password']
    confirm_passwd = request.form['confirm_password']

    return redirect(url_for('log'))


@app.route("/save_schedule", methods=['POST', 'GET'])
@login_required
def save_schedule():
    try:
        solution_num = request.form['solution_number']
        if 'current_semester' not in session:
            session['current_semester'] = request.args.get("semester")
        if 'current_semester' in session:
            if session['current_semester'] != request.args.get("semester") and request.args.get("semester") is not None:
                session['current_semester'] = request.args.get("semester")
    except Exception as e:
        solution_num = 0
    else:
        if len(allSolutions) > int(solution_num) and allSolutions:
            solution = allSolutions[int(solution_num)]
            solution = Library.transform(solution, int(session['current_semester']))
            db_assist.change_data("delete from schedule where semester_id = ?", list(session['current_semester']))
            db_assist.change_data("insert into schedule values (?,?,?,?,?)", solution)
            flash(
                    "The schedule for the current semester has been saved. You can edit it on the page 'Current schedule'")
    return redirect(url_for('coordinator_menu', **request.args))


@app.route("/current_schedule", defaults={'export': False}, methods=['POST', 'GET'])
@app.route("/current_schedule/<export>", methods=['POST', 'GET'])
@login_required
def current_schedule(export):
    client = "Coordinator"
    set_current_semester()
    schedule = db_assist.get_all("select s.weekday_id, s.timeslot_id, 5, c.course, r.name, r.location \
                    from schedule s, courses c, rooms r \
                    where s.course_id = c.id and s.room_id = r.room_id and s.semester_id = " + session[
        'current_semester'])
    p = Library.form_marks(schedule, COLORPREFS, True, False, True)

    return render_template("current_schedule.html", client=client, times=list(PERIOD.values()), prefs=p, export=export)


def set_current_semester():
    if 'current_semester' not in session:
        session['current_semester'] = request.args.get("semester")
    if 'current_semester' in session:
        if session['current_semester'] != request.args.get("semester") and request.args.get("semester") is not None:
            session['current_semester'] = request.args.get("semester")


@app.route('/export_schedule', methods=['POST', 'GET'])
def export_schedule():
    set_current_semester()
    success = Library.create_pdf(current_schedule(True))  # apply_async
    if success:
        flash("The schedule has been successfully exported to PDF file")
        return redirect(url_for('coordinator_menu', **request.args))
    return ('', 204)


@app.route("/send_schedule", methods=['POST', 'GET'])
@login_required
# @celery.task()
def send_schedule():
    m = db_assist.get_single("select st.semester, s.years from sessions s, semester_types st \
                 where s.semester = st.id and s.id = " + session['current_semester'])
    #     cur = m if not m else m[0]
    subject = "The schedule for " + m[0] + " " + m[1]
    emails = db_assist.get_all("select distinct u.email from users u, preferences p \
            where p.semester_id = " + session['current_semester'] + " and u.id = p.user_id")  # "receiver@mail.com"
    receivers = Library.rows_to_array(emails)
    sender_row = db_assist.get_single("select email from users where id = " + str(session['user_id']))
    mail = Message(subject=subject, sender=sender_row[0], recipients=receivers)
    mail.body = "The schedule for the upcoming semester is attached.\
            \n\nThis email has been sent automatically, please don't reply."
    pdf = Library.create_attachment(current_schedule(True))
    mail.attach("schedule.pdf", "application/pdf", pdf.getvalue())
    try:
        with app.app_context():
            mail_ext.send(mail)
        flash("The email with schedule for the upcoming semester has been sent")
    except:
        flash("Something went wrong with sending the mail", category='error')
    return redirect(url_for('coordinator_menu', **request.args))


@app.route("/schedules", methods=['POST', 'GET'])
@login_required
def schedules():
    """
    This function returns the possible schedules suggested to the coordinator based on the preferences
    entered bu the lecturers.

    :param null
    :var prefs - the prefereces gotten from the database
    :var list_pref - the data from preferences we actually need in a list of a tuple structure
    :var p - the dictionary of a dictionary of a list of a tuple, containning our data to present.
    :var: solution - the possible schedules from the constraint solver
    :var: courses - the list of courses whose schedules have been set
    :return: p

    """
    real_solution = []
    final_sol = {}
    display_buttons = False
    global incr
    global allSolutions
    global newPrefs
    client = "Coordinator"

    var = 0
    if request.method == 'POST' and incr > 0:
        try:
            request.form["newsolution"]
            increment = 1
        except:
            increment = -1

        var = len(allSolutions) - (incr - increment)
        incr -= increment

        if var < 0 or var >= len(allSolutions):
            sol = allSolutions[0]
            incr = len(allSolutions)
        else:
            sol = allSolutions[var]
    else:
        import itertools
        set_current_semester()

        prefs = db_assist.get_all('select courses.course, weekdays.name, timeslots.time, preferences.preference_id, \
         courses.students_number from courses, weekdays, timeslots, preferences where preferences.semester_id = ' +
                                  session['current_semester'] + ' and \
        courses.id = preferences.course_id and timeslots.timeslot_id = preferences.timeslot_id and \
         weekdays.weekday_id = preferences.weekday_id')
        # prefs = cur.fetchall()


        list_pref = [(x[0], x[1], x[2], x[3], str(x[4])) for x in prefs]
        p = Library.struct_pref(list_pref, COLORPREFS)

        # Rooms and capacity
        rooms = db_assist.get_all('select name, location, max_capability from rooms')

        pp = Library.struct_constraint(p, rooms)
        courses = pp.keys()
        if len(allSolutions) is 0 or newPrefs != 0:
            # actual variables
            for course in pp:
                problem.addVariable(course, pp[course])

            # constraints
            cur = db_assist.get_single('select active from constr where id = 1')
            active_constr = [i for i in cur][0].split()

            add_func_constraint(problem, not_sametime)
            add_all_constraint(problem)

            combinations = [x for x in itertools.combinations(courses, 2)]
            for i in combinations:
                if i[0][:-1] == i[1][:-1]:
                    add_func_constraint(problem, not_sameday, [i[0], i[1]])
            if "c1" in active_constr:
                for i in combinations:
                    if i[0][:-1] == i[1][:-1]:
                        add_func_constraint(problem, one_day_interval, [i[0], i[1]])

            if "c2" in active_constr:
                add_func_constraint(problem, not_sametime)
                for i in combinations:
                    add_func_constraint(problem, not_sametime, [i[0], i[1]])

            if "c7" in active_constr:
                for i in courses:
                    add_func_constraint(problem, not_redtime, [i])

            if "c4" in active_constr:
                for i in courses:
                    add_func_constraint(problem, not_bias, [i])

            temp = problem.getSolution()
            if temp is not None:
                allSolutions = [temp]  #
            incr = len(allSolutions)
            problem.reset()
            newPrefs = 0

        if incr > 0: sol = allSolutions[0]

    if 'sol' in locals():
        temp_dict = {}
        for course in sol:
            temp_dict[course] = (sol[course][0], Library.time_mapping(sol[course][1]), sol[course][2])
        # temp_dict = OrderedDict(sorted(temp_dict.items(), key=lambda a : rearrange(a[1])))
        real_solution.append(temp_dict)
        final_sol = Library.groupByTime(real_solution)
    else:
        display_buttons = True
        flash("No solutions found!!!")
        flash("Please relax the constraint a bit more or validate preferences")
    return render_template("schedules.html", solution=final_sol, client=client, display=display_buttons,
                           solution_num=var)


@app.route("/modify")
@login_required
def modify_view():
    """
    Renders the view of the modify constraint coordinator function.
    :var:active_constr - string - all constraints that have been set.
    :return:
    """
    client = "Coordinator"
    cur = db_assist.get_single('select active from constr where id = 1')
    active_constr = [i for i in cur][0].split()

    return render_template('modify_constraints.html', client=client, active=active_constr)


@app.route("/modify-constraint", methods=['POST', 'GET'])
@login_required
def modify_constraints():
    """
    Updates the constraints to the currently set constraints and reroutes to view
    :var:active - string - all constraints that have been recently set.
    :return:
    """
    global allSolutions
    checked_boxes = list(request.values)
    active = " ".join(checked_boxes)
    db_assist.update('update constr set active = ? where id = 1', [active])

    allSolutions = []
    flash('Constraint selection saved')
    return redirect(url_for('modify_view', **request.args))


@app.route("/help")
def helper():
    """
    Renders help tips to all clients.
    :return: render_template()
    """
    flash("Welcome to the Help Section for all!")
    pas = True
    return render_template("help.html", passp=pas)


#@app.teardown_appcontext
def close_db():
    db_assist.close_db()


if __name__ == "__main__":
    app.run()
