from flask import Flask, render_template, redirect, request, url_for, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_ckeditor import CKEditor, CKEditorField


class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret'
ckeditor = CKEditor(app)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///my_notes.db"
db=SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)

class Notes(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    notes: Mapped[str] = mapped_column()

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@app.route("/", methods=["POST","GET"])
def home():
    return render_template("home.html")

@app.route("/create_account", methods=["POST","GET"])
def create_account():
    if request.method == "POST":

        Email = request.form.get("email")
        result = db.session.execute(db.select(User).where(User.email == Email)).scalar_one_or_none()
        if result:
            flash("Email Already Exist!")
            return redirect(url_for("create_account"))
        else:
            User_data = User(
                username = request.form.get("user_name"),
                email = request.form.get("email"),
                password = generate_password_hash(request.form.get("password"), method='scrypt', salt_length=16)
            )
            db.session.add(User_data)
            db.session.commit()
        
            return redirect(url_for("login"))

    return render_template("account.html")

@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        result = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
        if not result:
            flash("Enter correct Email!")
            return redirect(url_for('login'))
        elif not check_password_hash(result.password, password):
            flash("Password is Incorrect!")
            return redirect(url_for('login'))
        else:
            login_user(result)
            return redirect(url_for("notes"))

    return render_template("login.html")


@app.route("/notes", methods=["POST","GET"])
@login_required
def notes():
    
    if request.method == "POST":
        my_note = Notes(
            userId = current_user.id ,
            title = request.form.get("title"),
            notes = request.form.get('ckeditor'),
        )
        if my_note.title == "":
            return redirect(url_for("notes"))
        else:
            db.session.add(my_note)
            db.session.commit()
            return redirect(url_for("notes"))

    result = db.session.execute(db.select(Notes).where(Notes.userId == current_user.id)).scalars().all()

    return render_template("notes.html", user=current_user, note=result)

@app.route("/shownote/<int:id>")
def shownote(id):
    result = db.session.execute(db.select(Notes).where(Notes.id==id)).scalar_one_or_none()

    return render_template("shownote.html", data=result)

@app.route("/logout", methods=["POST","GET"])
def logout():
    logout_user()
    return redirect(url_for("home"))

#print(app.url_map)


if __name__ == "__main__":
    app.run(debug=True)