from flask import Flask , render_template ,request,url_for ,flash,redirect,session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests 
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True , autoincrement=True)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150),nullable=False)
    movies = db.relationship('Movie', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'
    def is_authenticated(self):
        return True 
    def is_active(self):
        return True 
    def is_anonymous(self):
        return False 
    def get_id(self):
        return str(self.id)
    
class Movie(db.Model):
    __tablename = 'movie'
    id = db.Column(db.Integer, primary_key = True , autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))





@app.route("/")
@login_required
def home():
    # return render_template("home.html")
    return redirect("/movies")

@app.route("/login" , methods=["GET", "POST"])
def login():
    error = None 
    if request.method =="POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password :
            error = "Invalid username or password"
        else:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password,password):

                print("Just a minute....")
                login_user(user)
                return redirect(url_for('home'))
            else:
                error = "Invalid username or password"

            
    return render_template("login.html",error=error)

@app.route("/register" , methods=["GET","POST"])
def register():
    error = None 

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password :
            error = "Invalid username or password"
            return render_template("register.html",error=error)
            
        elif len(password) <8:
            error = "Password length should be atleast 8 characters.."
            return render_template("register.html",error=error)
        
        
        else:
            checkuser = User.query.filter_by(username=username).first()
            if checkuser:
                error = "User already exists"
                return render_template("register.html",error=error)
            else:

                hashed_password = generate_password_hash(password=password , method='pbkdf2')
                new_user =User(username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()


            print("Registration successful")
            return redirect(url_for("login"))
    return render_template("register.html",error=error)        
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/search" , methods=["GET","POST"])
@login_required
def search():
    movies = None 
    error = None 
    friend = None 
    if request.method == "POST":
        friend_name = request.form.get("search")
        print("You searched for : ",friend_name)
        friend = User.query.filter_by(username=friend_name).first()
        print(friend)
        if friend :
            print("Friend found")
            movies = friend.movies 

        else :
            error = "No person with given name was found"
            print("No friend with given name was found")

       
            


    return render_template("search.html",friend=friend, movies=movies,error=error)

@app.route("/profile" ,methods=['GET'])
@login_required
def profile():
    user = current_user

    return render_template("profile.html", user=user)

@app.route("/profile/change-password", methods=["GET","POST"])
@login_required
def change_password():
    user = current_user
    error = None 
    if request.method == "POST":
        oldpassword = request.form.get("oldpassword")
        oldhashpassword = user.password 

        newpassword = request.form.get("newpassword")
        if not oldpassword or not newpassword:
            error = "Old password or new password is invalid"
        else:
            newpasswordhash = generate_password_hash(newpassword ,method='pbkdf2')
            user.password = newpasswordhash
            db.session.commit()
            print("Password changed successfully")
            return redirect(url_for("home"))




    return render_template("changepassword.html", error=error)

@app.route("/movies" , methods=["GET", "POST"])
@login_required
def movies():
    movies = None 
    error = None 
    if request.method == "POST":
        movie_name = request.form.get("moviename")
        if not movie_name :
            print("No movie name entered")
            error = "Invalid movie name"
        else:
            res = search_movies(movie_name=movie_name)
            if res :
                # print(res)
                print("--------------------------------------")
                print(res.json())
                re = res.json()

                print(re['Title'])
                movies =re 
            else:
                error = "Something went wrong"
            
    return render_template("movies.html", movies=movies, error=error)

@app.route("/mymovies", methods=["GET"])
@login_required
def mymovies():
    # user_id = session.get('user_id')

    # print(user_id)
    user = current_user
    print("----------------------------------------------------------")
    
    print(user)
    print("----------------------------------------------------------------")
    movies = Movie.query.filter_by(user_id=current_user.id).all()
    print(movies)
    return render_template("mymovies.html", movies=movies)


api = 'https://www.omdbapi.com/?t=interstellar&apikey=8174a6ce'
def search_movies(movie_name):
    if not movie_name:
        print("Please enter valid movie name")
    else :
        query = f'https://www.omdbapi.com/?t={movie_name}&apikey=8174a6ce'
        result = requests.get(query)


        if result :
            print("Result")
            # print(result.json())
            # return result 
            return result 
        else:
            print("No movie found with this name")

@app.route('/add-movie' , methods=["POST"])
@login_required
def add_movie():
    title = request.form.get("title")
    # genre = request.form.get("genre")
    # director = request.form.get("director")p
    print("----------------------------------")
    year = request.form.get("year")
    print(f"Title : {title}, year: {year}")
    print("--------------------------------------")
    movie = Movie(title=title, year=year, user_id =current_user.id)
    db.session.add(movie)
    db.session.commit()


    return redirect(url_for("mymovies"))

@app.route("/delete-movie/<int:movie_id>", methods=["POST"])
@login_required
def delete_movie(movie_id):
    movie = Movie.query.filter_by(id=movie_id, user_id =current_user.id).first()
    print(movie)
    if movie is None :
        print("Something went wrong ")
    
    db.session.delete(movie)
    db.session.commit()
    print('Movie deleted successfully')
    return redirect(url_for("mymovies"))
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True,port=5002)