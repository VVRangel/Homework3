from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "forumsecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///forum.db"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ---------------- MODELS ---------------- #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    author = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    post_id = db.Column(db.Integer)
    author = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 🔥 FORCE CLEAN DB INIT (IMPORTANT FIX)
with app.app_context():
    db.drop_all()
    db.create_all()


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("home.html", posts=posts)


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=request.form["password"]
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            login_user(user)
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/create", methods=["GET","POST"])
@login_required
def create():
    if request.method == "POST":
        post = Post(
            title=request.form["title"],
            content=request.form["content"],
            author=current_user.username
        )
        db.session.add(post)
        db.session.commit()
        return redirect("/")

    return render_template("create.html")


@app.route("/post/<int:id>", methods=["GET","POST"])
def post(id):

    post = Post.query.get_or_404(id)

    if request.method == "POST":
        if not current_user.is_authenticated:
            return redirect("/login")

        comment = Comment(
            text=request.form["comment"],
            post_id=id,
            author=current_user.username
        )

        db.session.add(comment)
        db.session.commit()

    comments = Comment.query.filter_by(post_id=id).all()

    return render_template(
        "post.html",
        post=post,
        comments=comments
    )


@app.route("/profile/<username>")
def profile(username):
    posts = Post.query.filter_by(author=username).all()
    return render_template("profile.html", username=username, posts=posts)


@app.route("/delete_post/<int:id>")
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)

    if post.author == current_user.username:
        Comment.query.filter_by(post_id=id).delete()
        db.session.delete(post)
        db.session.commit()

    return redirect("/")


@app.route("/delete_comment/<int:id>")
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)

    if comment.author == current_user.username:
        db.session.delete(comment)
        db.session.commit()

    return redirect(request.referrer or "/")


if __name__ == "__main__":
    app.run(debug=True)