from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Articles = Articles()

# Index
@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# All articles
@app.route('/articles')
def articles():
    # Create a cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute('SELECT * from articles')

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg)

    # Close connection
    cur.close()

# Single article
@app.route('/article/<string:id>/')
def article(id):
    # Create a cursor
    cur = mysql.connect.cursor()

    # Get articles
    result = cur.execute('SELECT * from articles WHERE id=%s', id)

    article = cur.fetchone()

    return render_template('article.html', article=article)

# Register Form class


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.EqualTo('confirm', message='Password do not match'),
        validators.Length(min=6, max=50)
    ])
    confirm = PasswordField('Confirm Password')

# User register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create the cursor
        cur = mysql.connection.cursor()

        cur.execute('INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)',
                    (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create a cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute(
            "SELECT * from users where username=%s", [username])

        if result > 0:
            # Get stored data
            data = cur.fetchone()
            password = data['password']

            # compare password
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                errors = 'Invalid login'
                return render_template('login.html', errors=errors)
            # Close the connection
            cur.close()
        else:
            errors = 'Username not found'
            return render_template('login.html', errors=errors)
    return render_template('login.html')

# Check if user logged in


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Create a cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute('SELECT * from articles')

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)

    # Close connection
    cur.close()

# Article Form class


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add new article
@app.route('/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create a cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s, %s, %s)",
                    (title, body, session['username']))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('addarticle.html', form=form)

# edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    # Create cursor
    cur = mysql.connect.cursor()

    # Get the article by id
    result = cur.execute("SELECT * from articles where id=%s", [id])
    article = cur.fetchone()

    # Get the form
    form = ArticleForm(request.form)

    # Populate form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create a cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute(
            "UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('editarticle.html', form=form)

# Delete article


@app.route('/delete_article/<string:id>', methods=['POST'])
@login_required
def delete_article(id):
    # Create the cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE from articles where id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Article deleted', 'success')

    return redirect(url_for('dashboard'))


# Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = 'secret_key_1234'
    app.run(debug=True)
