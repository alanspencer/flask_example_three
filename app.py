import os
import uuid
import threading
import shelve


import pyodbc

from contextlib import contextmanager

from flask import Flask, request, session, redirect,\
    url_for, render_template
from flask_wtf import FlaskForm
from flask_login import current_user, LoginManager, UserMixin,\
    login_user, logout_user, login_required
from wtforms import SubmitField

import game


server = os.environ.get('SQLSERVERNAME', default='localhost')
#  
# server = 'tcp:myserver.database.windows.net'  
database =  os.environ.get('SQLDBNAME', default='TestDB')
username = os.environ.get('SQLUSERNAME')  
password = os.environ.get('SQLPASSWORD')
cnxn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}') 
cursor = cnxn.cursor()

# Check the Usera table exists in our database, if not, add it
try:
    cursor.execute("SELECT * FROM Users")
except pyodbc.ProgrammingError:
    cursor.execute("CREATE TABLE Users (name varchar(100), score1 int, score2 int)")
    cursor.commit()


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET',
                                'Please_dont_use_this_default')

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

### The core of the Flask login module is the User class
### This class needs a method is_authenticated() which
### returns True if the user is allowed in

class User(UserMixin):
    def __init__(self, user_id=str(uuid.uuid1())):
        super().__init__()
        self.id = user_id
        self.game = game.PaperScissorsStone()
        cursor = cnxn.cursor()
        res = cursor.execute('SELECT score1, score2 FROM Users WHERE name=(?)',
                            user_id)
        if res.rowcount:
            ## take tuple from result and convert into list
            self.game.score = list(res.fetchone())
        else:
            ## default to 0-0.
            self.game.score = [0, 0]
            cursor.execute("""INSERT INTO Users (name, score1, score2)
            VALUES (?, ?, ?)""",
                          self.id,
                          *self.game.score)
        cursor.commit()

    @property
    def is_authenticated(self):
        return True

    def store(self):
        cursor = cnxn.cursor()
        cursor.execute("""UPDATE Users
                         SET score1=(?), score2=(?)
                         WHERE name=(?)""",
                         self.game.score[0],
                         self.game.score[1],
                         self.id)
        cursor.commit()

def remove_user(user_id):
    cursor = cnxn.cursor()
    cursor.execute("DELETE FROM Users WHERE name=(?)", user_id)
    cursor.commit()

class GameForm(FlaskForm):
    paper = SubmitField('Paper')
    scissors = SubmitField('Scissors')
    stone = SubmitField('Stone')

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
    
@app.route('/login')
def login():
    login_user(User())
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    remove_user(current_user.get_id())
    logout_user()
    return redirect(url_for('index'))

CHOICES = ['paper', 'scissors', 'stone']
MAPPING = {val:key for key, val in enumerate(CHOICES)}

@app.route('/', methods= ['GET', 'POST'])
@login_required
def index():

    info = []
    gform = GameForm()

    print(request)
    
    if request.method == 'POST':
        choice  = (MAPPING.keys() & request.form.keys()).pop()
        info.append(f'You played {choice}.')
        result, my_choice = current_user.game.play_round(MAPPING[choice])
        current_user.store()

        info.extend((f'I played {CHOICES[my_choice]}.',
                     f'{result}'))
    
    return render_template('index.html', info=info, user=current_user,
                           form=gform)
