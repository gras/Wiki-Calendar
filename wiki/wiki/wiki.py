import datetime as dt
import os
import sqlite3
from functools import wraps

from flask import Flask, request, g, redirect, render_template, flash, Response

ROOT_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

config = []
with open("{}/wiki.config".format(ROOT_DIRECTORY), "r") as file:
    for line in file.read().split("\n"):
        info = line.split("=")
        config.append(info[1])

START_DATE = dt.datetime(int(config[2]), int(config[0]), int(config[1]))
END_DATE = dt.datetime(int(config[5]), int(config[3]), int(config[4]))
PASSWORD = config[6]

DAYS = []
DAYS_TEXT = []

TOTAL_DAYS = (END_DATE - START_DATE).days + 1

for day_number in range(TOTAL_DAYS):
    current_date = (START_DATE + dt.timedelta(days=day_number)).date()
    DAYS.append(current_date)
    DAYS_TEXT.append(current_date.strftime("%m-%d-%Y"))

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=('{}/wiki-{}.db'.format(ROOT_DIRECTORY, START_DATE.strftime("%y"))),
    SECRET_KEY=os.urandom(24)  # generate a secret key
))


def check_auth(password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return password == PASSWORD


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('Incorrect login :(', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    # print('Initialized the database.')


def init_db():
    db = sqlite3.connect(app.config['DATABASE'])
    c = db.cursor()
    # start_date = dt.datetime(2017, 5, 27)
    # end_date = dt.datetime(2017, 7, 6)
    # total_days = (end_date - start_date).days + 1

    creation_text = '''CREATE TABLE data (name, role'''

    # for day_number in range(total_days):
    #     current_date = (start_date + dt.timedelta(days=day_number)).date()
    #     creation_text += ''', "''' + current_date.strftime("%m-%d-%Y") + '''"'''

    for day in DAYS_TEXT:
        creation_text += ''', "''' + day + '''"'''

    creation_text += ''')'''
    c.execute(creation_text)

    this_command = '''INSERT INTO data ("name", "role") VALUES ("{}", "{}")'''.format("ANNOUNCEMENTS", "")
    c.execute(this_command)
    db.commit()

    with open("{}/people.config".format(ROOT_DIRECTORY)) as this_file:
        for this_line in this_file.read().split("\n"):
            this_info = this_line.split("\t")
            this_command = '''INSERT INTO data ("name", "role") VALUES ("{}", "{}")'''.format(this_info[0],
                                                                                              this_info[1])
            c.execute(this_command)
            db.commit()


@app.route('/')
@app.route('/home/')
def welcome():
    return render_template("home.html")


@app.route('/set/<int:month>-<int:day>-<int:year>/', methods=['POST', 'GET'])
@requires_auth
def set_data(month, day, year):
    if month == "" and day == "" and year == "":
        return today()
    if request.method == 'POST':
        username = request.form['username']
        date = request.form['date']
        entry = request.form['entry']
        # current = '''SELECT {} FROM data WHERE name="{}"'''.format(date, username)
        db = get_db()
        if date == "*":
            try:
                start_date = dt.datetime(year, month, day)
            except Exception:
                return today()
            end_date = start_date + dt.timedelta(days=6)
            total_days_used = (end_date - start_date).days + 1

            for day_number_now in range(total_days_used):
                current_date_now = (start_date + dt.timedelta(days=day_number_now)).date()
                current_date_now = str(current_date_now.strftime("%m-%d-%Y"))
                command = '''UPDATE data SET "{}"="{}" WHERE name="{}"'''.format(current_date_now, entry, username)
                try:
                    db.execute(command)
                    db.commit()
                except sqlite3.OperationalError:
                    log("error")
                    return today()

        elif username == "*":
            all_users = db.execute('''SELECT "name" FROM data''').fetchall()
            for u in all_users:
                for uu in u:
                    command = '''UPDATE data SET "{}"="{}" WHERE name="{}"'''.format(date, entry, uu)
                    try:
                        db.execute(command)
                        db.commit()
                    except sqlite3.OperationalError:
                        log("error")
                        return today()
        else:
            command = '''UPDATE data SET "{}"="{}" WHERE name="{}"'''.format(date, entry, username)
            # print(command)
            try:
                db.execute(command)
                db.commit()
                flash('Update successful!')
            except sqlite3.OperationalError:
                log("error")
                return today()
            except Exception:
                log("error")
                return today()
        log("Changed {}@{} to '{}'".format(username, date, entry))
    return redirect("/week/{}-{}-{}/".format(month, day, year))


@app.route('/now/')
@app.route('/today/')
def today():
    month = dt.date.today().strftime("%m")
    day = dt.date.today().strftime("%d")
    year = dt.date.today().strftime("%Y")
    return redirect("/week/{}-{}-{}/".format(month, day, year))


@app.route('/weeks/')
@app.route('/week/')
@app.route('/day/')
@app.route('/days/')
@app.route('/date/')
@app.route('/dates/')
def display_weeks():
    return render_template("weeks.html", days=DAYS_TEXT, today=dt.date.today().strftime("%m-%d-%Y"))


@app.route('/date/<int:month>-<int:day>-<int:year>/')
@app.route('/day/<int:month>-<int:day>-<int:year>/')
@app.route('/days/<int:month>-<int:day>-<int:year>/')
@app.route('/weeks/<int:month>-<int:day>-<int:year>/')
@app.route('/week/<int:month>-<int:day>-<int:year>/')
def display_days(month, day, year):
    try:
        start_date = dt.datetime(year, month, day)
    except Exception:
        return today()

    end_date = start_date + dt.timedelta(days=6)
    total_days = (end_date - start_date).days + 1

    day_code = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
    days = ["NAME", "ROLE"]
    weekday = ["", ""]
    blank = ["", "", "", "", "", "", "", "", ""]

    query = '''SELECT name, role'''

    for day_number in range(total_days):
        current_date = (start_date + dt.timedelta(days=day_number)).date()
        weekday.append(day_code[current_date.weekday()])
        current_day = str(current_date.strftime("%m-%d-%Y"))
        days.append(current_day)
        query += ''', "''' + current_day + '''"'''

    query += ''' from data'''

    # print(query)

    table_data = [days, weekday, blank]

    orig_text = [days, weekday, blank]

    for entry in get_db().execute(query).fetchall():
        entry_filtered = []
        orig_filtered = []
        for index in range(0, len(days)):
            if days[index] == entry[index]:
                entry_filtered.append(["color:red; font-weight: bold;", "CLOSED"])
                orig_filtered.append("")
            else:
                if entry[index] is not None:
                    orig_filtered.append(entry[index])
                    submission = entry[index]
                    if "|" not in submission:
                        submission = "|" + submission
                    entry_split = submission.split("|")
                    entry_filtered.append(entry_split)
                else:
                    orig_filtered.append("")
                    entry_filtered.append(entry[index])
        table_data.append(entry_filtered)
        orig_text.append(orig_filtered)

    next_week = (start_date + dt.timedelta(days=7)).strftime("%m-%d-%Y")
    prev_week = (start_date - dt.timedelta(days=7)).strftime("%m-%d-%Y")
    current_date_now = start_date.strftime("%m-%d-%Y")
    today_date = dt.date.today().strftime("%m-%d-%Y")
    current_day = start_date.strftime("%d")
    current_month = start_date.strftime("%m")
    current_year = start_date.strftime("%Y")

    return render_template('table.html', table_data=table_data, current_date=current_date_now, next=next_week,
                           previous=prev_week, today=today_date, orig_text=orig_text, current_day=current_day,
                           current_month=current_month, current_year=current_year)


@app.route("/users/")
def users():
    u_list = []

    db = get_db()
    all_users = db.execute('''SELECT "name" FROM data''').fetchall()
    for u in all_users:
        for uu in u:
            if uu != "ANNOUNCEMENTS":
                u_list.append(uu)

    return render_template('users.html', people=u_list)


@app.route("/users/<user>")
@app.route("/user/<user>")
def report(user):
    db = get_db()
    all_users = db.execute('''SELECT "name" FROM data''').fetchall()

    found = False

    for u in all_users:
        for uu in u:
            if uu == user:
                found = True

    if not found:
        return today()

    data = db.execute('''SELECT * FROM data WHERE "name" = "{}"'''.format(user)).fetchall()
    today_date = dt.date.today().strftime("%m-%d-%Y")

    submit = []
    for item in data[0]:
        edited = item
        if item is None:
            edited = ""
        if "|" not in edited:
            edited = "|" + edited
        submit.append(edited.split("|"))

    not_empty = 0.0
    total_length = 0.0
    sub_total_length = 0.0
    sub_not_empty = 0.0
    strikes = 0
    attended = 0
    hours = 0

    for x in range(2, len(submit)):
        # print("{} {}".format(submit[x][1], DAYS_TEXT[x - 3]))

        if submit[x][1] is not None and "closed" not in submit[x][1].lower() and "x" not in submit[x][
            1].lower() and "gcer" not in submit[x][1].lower():
            total_length += 1
            if submit[x][1].strip() != "":
                not_empty += 1
                if "line-through" in submit[x][0].lower():
                    strikes += 1
                elif "-" in submit[x][1]:
                    attended += 1

                    try:
                        split = submit[x][1].strip().split("-")
                        if ":" in split[0]:
                            temp = split[0].replace(";", ":").split(":")
                            start_time = float(temp[0]) + (float(temp[1]) / 60.0)
                        else:
                            start_time = int(split[0])
                        if ":" in split[1]:
                            temp = split[1].replace(";", ":").split(":")
                            end_time = float(temp[0]) + (float(temp[1]) / 60.0)
                        else:
                            end_time = int(split[1])
                        hours += end_time - start_time
                    except ValueError:
                        pass
                elif "y" in submit[x][1].lower():
                    attended += 1
                    weekday = DAYS[x - 2].weekday()
                    if weekday == 5 or weekday == 6:
                        hours += 4
                    else:
                        hours += 2.5
        if DAYS_TEXT[x - 2] == today_date:
            sub_total_length = total_length
            sub_not_empty = not_empty
            real_attended = attended
            real_hours = hours

    percent = "{:.2f}%".format((not_empty / total_length) * 100)

    sub_percent = "{:.2f}%".format((sub_not_empty / sub_total_length) * 100)

    at_percent = "{:.2f}%".format((real_attended / sub_total_length) * 100)

    show_hours = "{:.2f}".format(real_hours)
    show_days = "{:.2f}".format(real_hours / 24)

    # print("not empty {} total length {} sub total length {} sub not empty {}".format(not_empty, total_length,
    #                                                                                  sub_total_length, sub_not_empty))

    return render_template('user.html', user=user, table_data=submit, days=DAYS_TEXT, percent=percent, today=today_date,
                           sub_percent=sub_percent, not_empty=int(not_empty), total_length=int(total_length),
                           sub_total_length=int(sub_total_length), sub_not_empty=int(sub_not_empty), strikes=strikes,
                           at=real_attended, at_per=at_percent, show_hours=show_hours, show_days=show_days)


@app.route("/log/")
@app.route("/logs/")
@app.route("/history/")
@app.route("/changes/")
def get_log():
    try:
        with open("{}/history.log".format(ROOT_DIRECTORY), "r") as file:
            data = []
            text = file.read().split("\n")
            for x in range(len(text) - 1, -1, -1):
                data.append(text[x])
    except FileNotFoundError:
        data = ["No data"]
    return render_template('log.html', log=data)


def log(message):
    time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = "{}/history.log".format(ROOT_DIRECTORY)
    with open(filename, "a") as history:
        history.write("{}: {}\n".format(time, message))


# If a database does not exist, create one
if not os.path.isfile(app.config["DATABASE"]):
    init_db()
