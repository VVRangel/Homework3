from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config["SECRET_KEY"] = "forumsecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///forum.db"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    author = db.Column(db.String(50))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    post_id = db.Column(db.Integer)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


BASE_STYLE = """
<style>
body{
background:#0f172a;
font-family:Arial,sans-serif;
margin:0;
color:white;
}
nav{
background:#1e293b;
padding:15px;
display:flex;
gap:15px;
}
nav a{
color:white;
text-decoration:none;
font-weight:bold;
}
.container{
width:80%;
margin:auto;
padding:20px;
}
.card{
background:#1e293b;
padding:20px;
border-radius:12px;
margin-bottom:15px;
box-shadow:0 0 10px rgba(0,0,0,.3);
}
input,textarea{
width:100%;
padding:12px;
margin-top:8px;
margin-bottom:12px;
background:#334155;
border:none;
color:white;
border-radius:8px;
}
button{
background:#3b82f6;
color:white;
border:none;
padding:10px 20px;
border-radius:8px;
cursor:pointer;
}
h1,h2{
color:#60a5fa;
}
.small{
color:#94a3b8;
}
</style>
"""


@app.route("/")
def home():
    posts = Post.query.order_by(Post.id.desc()).all()

    html = BASE_STYLE + """
    <nav>
        <a href="/">Forum</a>
        {% if current_user.is_authenticated %}
            <a href="/create">Create Post</a>
            <a href="/logout">Logout</a>
        {% else %}
            <a href="/login">Login</a>
            <a href="/register">Register</a>
        {% endif %}
    </nav>

    <div class="container">
        <h1>Forum</h1>

        {% for post in posts %}
        <div class="card">
            <h2>{{post.title}}</h2>
            <p>{{post.content[:150]}}...</p>
            <p class="small">By {{post.author}}</p>
            <a href="/post/{{post.id}}">
                <button>Open</button>
            </a>
        </div>
        {% endfor %}
    </div>
    """
    return render_template_string(html, posts=posts)


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

    html = BASE_STYLE + """
    <div class="container">
        <div class="card">
            <h1>Register</h1>

            <form method="POST">
                <input name="username" placeholder="Username">
                <input type="password" name="password" placeholder="Password">
                <button>Create Account</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(html)


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

    html = BASE_STYLE + """
    <div class="container">
        <div class="card">
            <h1>Login</h1>

            <form method="POST">
                <input name="username" placeholder="Username">
                <input type="password" name="password" placeholder="Password">
                <button>Login</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(html)


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

    html = BASE_STYLE + """
    <div class="container">
        <div class="card">
            <h1>Create Post</h1>

            <form method="POST">
                <input name="title" placeholder="Title">
                <textarea name="content" rows="8"></textarea>
                <button>Create</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(html)


@app.route("/post/<int:id>", methods=["GET","POST"])
def post(id):

    post = Post.query.get_or_404(id)

    if request.method == "POST":
        comment = Comment(
            text=request.form["comment"],
            post_id=id
        )

        db.session.add(comment)
        db.session.commit()

    comments = Comment.query.filter_by(post_id=id).all()

    html = BASE_STYLE + """
    <div class="container">

        <div class="card">
            <h1>{{post.title}}</h1>
            <p>{{post.content}}</p>
            <p class="small">By {{post.author}}</p>
        </div>

        <div class="card">
            <h2>Comments</h2>

            {% for c in comments %}
                <div class="card">
                    {{c.text}}
                </div>
            {% endfor %}

            <form method="POST">
                <textarea name="comment"></textarea>
                <button>Add Comment</button>
            </form>
        </div>

    </div>
    """

    return render_template_string(
        html,
        post=post,
        comments=comments
    )


if __name__ == "__main__":
    app.run(debug=True)