# Dependencies
import os
import sqlalchemy
from flask import Flask, render_template, jsonify, request, make_response, session, abort, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
import pymysql
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextField, PasswordField, SelectField, DateField, DecimalField, SubmitField
from wtforms.validators import InputRequired, Length, NumberRange, EqualTo
from passlib.hash import sha256_crypt

import enum



#################################################
# Flask Setup
#################################################

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = '1a2b3c4d5e'

# Enter your database connection details below
# app.config['MYSQL_HOST'] = '127.0.0.1'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'password'
# app.config['MYSQL_DB'] = 'usda'

# Intialize MySQL
# mysql = MySQL(app)

#################################################
# Set up the database
#################################################
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD = "uv9y9g5t"
DIALECT = "mysql"
DRIVER = "pymysql"
DATABASE = "usda"

# Connect to DB in DB Server
db_connection_string = (
    f"{DIALECT}+{DRIVER}://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
)

#FOLLOWING CODE IS FOR HEROKU######
# #################################################
# # Database Setup
# #################################################

# # The database URI
###################################################

app.config['SQLALCHEMY_DATABASE_URI'] = (
     os.environ.get("JAWSDB_URL","") or db_connection_string
 )
db = SQLAlchemy(app)

class IntEnum(db.TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.
    The default would have stored the enum's *name* (ie the string).
    """
    impl = db.Integer

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)


class Meal_record(db.Model):
    __tablename__ = "meal_record"

    meal_item_code = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    type = db.Column(db.String(50))
    meal_date = db.Column(db.Date)
    meal_desc = db.Column(db.String(256))    
    amount = db.Column(db.Float)

    def __repr__(self):
        return "<Meal_record %r>" % (self.name)

class ActivityTypes(enum.IntEnum):
    sedentary = 1
    lightly_active = 2
    moderately_active = 3
    very_active = 4
    extra_active = 5


class User_account(db.Model):
    __tablename__ = "user_account"

    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50))
    confirm_password = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    physical_activity_level = db.Column(IntEnum(ActivityTypes), default=ActivityTypes.sedentary)
    


    def __repr__(self):
        return "<User_account %r>" % (self.name)


@app.before_first_request
def setup():
    db.create_all()

#ABOVE CODE IS FOR HEROKU######
###################################################

#commented as using a different method for Heroku
# engine = create_engine(db_connection_string)
# inspector = inspect(engine)
# table_names = inspector.get_table_names()
# # print("Table names are: ", table_names)

#commented as using a different method for Heroku
# Base = automap_base()
# Base.prepare(db.engine, reflect=True)
# # print(Base.classes.values)

# # create classes by mapping with names which match the table names
# User_account = Base.classes.user_account
# Meal_record = Base.classes.meal_record
# Nutrition = Base.classes.nutrition

#commented as using a different method for Heroku
# session_db = Session(bind=engine)
# print("session_db is: ", session_db)






#############################################################################################
# Route #1("/")
# Home Page
#############################################################################################
@app.route("/index.html")
@app.route("/")
def main():
    session['page']=' '
    if(checkLoggedIn() == True):
        session['page']='dashboard'
        return redirect('/dashboard')

    session['page']=' '
    return render_template("index.html")
#############################################################################################
# Route #2(/login)
# Design a query for the existing user to login
#############################################################################################
    
@app.route('/login', methods=['GET', 'POST'])
def login():
# Output message if something goes wrong...
    msg = ''
    print("Start of stuff")
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST': #and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        request_username = request.form['username']
        request_password = request.form['password']
        # Check if account exists using MySQL
        # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # cursor.execute('SELECT * FROM user_accounts WHERE username = %s AND password = %s', (username, password))
        if request_username and request_password:   
        # Fetch one record and return result
            print("request_username: "+request_username+" | request_password: "+request_password)
            account = loginsys(request_username, request_password)
                # If account exists in accounts table in out database
            if account:
            # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['username'] = account[3]
            # Redirect to home page
                session['page']='dashboard'
                return redirect('/dashboard')
            else:
            # Account doesnt exist or username/password incorrect
                msg = 'Incorrect username/password!'
    session['page']=' '
    return render_template('index.html', msg=msg)
    
def loginsys(username, password):
    print("Username: "+username+" Password: "+password)
    user_ls = db.session.query(User_account.first_name, User_account.last_name, User_account.gender, User_account.username)\
                        .filter(User_account.username == username)\
                        .filter(User_account.password == password)\
                        .first()           
    print("user_ls: " + str(user_ls))                 
    return user_ls


##############################################################################################
# Route #3(/register)
# Design a query for the register a new user
#############################################################################################

class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('password', validators=[InputRequired()])
    confirm_password = PasswordField('confirm_password', validators=[InputRequired(), EqualTo('password')])
    first_name = StringField('first_name', validators=[InputRequired(),Length(min=2, max=50)])
    last_name = StringField('last_name', validators=[InputRequired(),Length(min=2, max=50)])
    gender = SelectField(u'gender', choices=[('male', 'Male'), ('female', 'Female')])
    date_of_birth = DateField('date_of_birth', format='%Y-%m-%d')
    height = DecimalField('height', places=2, rounding=None, validators=[InputRequired(), NumberRange(min=0, max=500, message='Blah')])
    weight = DecimalField('weight', places=2, rounding=None, validators=[InputRequired(), NumberRange(min=0, max=2000, message='Blah')])
    physical_activity_level = SelectField(u'physical_activity_level', choices=[('sedentary', 'Sedentary'), ('lightly active', 'Lightly Active'), ('moderately active', 'Moderately Active'), ('very active', 'Very Active'), ('extra active', 'Extra Active')])  
    submit = SubmitField('Get Started')

@app.route("/register", methods=["GET", "POST"])
def register():

        form = RegistrationForm(request.form)
        if form.validate_on_submit():
            flash(f'Account created for {form.username.data}!', 'success')

            new_user = User_account(username = form.username.data,\
                                    password = form.password.data,\
                                    confirm_password = form.confirm_password.data,\
                                    first_name = form.first_name.data,\
                                    last_name = form.last_name.data,\
                                    gender =  form.gender.data,\
                                    date_of_birth = form.date_of_birth.data,\
                                    height = form.height.data,\
                                    weight = form.weight.data,\
                                    physical_activity_level = form.physical_activity_level.data
                                    )
            db.session.add(new_user)
            db.session.commit()

            return redirect('/dashboard')
        return render_template("New_user.html", form=form)


##############################################################################################
# Route #4(/home)
# This will be the home page, only accessible for loggedin users
#############################################################################################

class AddMeal(FlaskForm):
    inputdate = DateField('inputdate', format='%Y-%m-%d')
    meal_category = StringField(u'meal_category', validators=[InputRequired()]) 
    food_desc = StringField('food_desc', validators=[InputRequired()])
    servings_count = DecimalField('servings_count', places=2, rounding=None, validators=[InputRequired(), NumberRange(min=0, max=20)])
    foodNameId = DecimalField('foodNameId')
    submit = SubmitField('Add')


@app.route('/dashboard',methods=["GET", "POST"])
def dashboard():
    if(checkLoggedIn() == False):
        return redirect('/login')

    session['page']='dashboard'

    form = AddMeal(request.form)
    if form.validate_on_submit():
        # flash(f'Meal Added for {form.meal_category.data}!', 'successfully')

        new_meal = Meal_record(meal_date = form.inputdate.data,\
                                    type = form.meal_category.data,\
                                    meal_desc = form.food_desc.data,\
                                    amount = form.servings_count.data,\
                                    meal_item_code = form.foodNameId.data
                                    )
        db.session.add(new_meal)
        db.session.commit()
        print("Adding meal")

    return render_template("dashboard.html", form=form)

@app.route("/user_metrics/<new_food>")
def user_meal(new_food):
    print(new_food)
    search = "{}%".format(new_food) 
    list_food =db.session.query(Nutrition.Shrt_Desc,Nutrition.Weight_desc )\
                    .filter(Nutrition.Shrt_Desc.like(search)).all()
    print(list_food)                
    show_breakfast = {}   
    for food in list_food:
        show_breakfast[food[0]] = food[1]
       
    print(show_breakfast)      
    return jsonify(show_breakfast)
 

@app.route('/analysis')
def analysis():
    if(checkLoggedIn() == False):
        return redirect('/login')
    session['page']='analysis'
    return render_template("Daily_vizualization.html")

def checkLoggedIn():
    if 'loggedin' in session:
        if session['loggedin'] == True:
            return True
    return False 

@app.route('/nutrition')
def nutrition():
    if(checkLoggedIn() == False):
        return redirect('/login')
    session['page']='nutrition'
    return render_template("nutrition.html")

# @app.route('/register')
# def register():
#     session['page']='register'
#     return render_template("New_user.html")

@app.route('/intake')
def intake():
    if(checkLoggedIn() == False):
        return redirect('/login')
    session['page']='intake'
    return render_template("intake.html")

@app.route('/logout')
def logout():
    if(checkLoggedIn() == False):
        session['page']=' '
        return render_template('login.html', msg="Already logged out!")
    else:
        session['loggedin'] = False
        messages = "loggedout"
        session['messages'] = messages
        session['page']=' '
        return redirect("/")  


@app.route('/nutriquicksearch', methods=['GET'])
def nutriquicksearch():
    searchkey=request.args.get('term')
    if not searchkey:
        return '{  "data": [] } '
    resultSet = db.session.query(Nutrition.NDB_No, Nutrition.Shrt_Desc, Nutrition.Energy)\
        .filter(Nutrition.Shrt_Desc.ilike('%'+searchkey+'%')).all()
    return jsonify(data=resultSet)



if __name__ == "__main__":
    app.run(debug=True)
    #app.run() 
