from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session
from amu import forms

views = Blueprint('views', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("logged_in", None) is None:
            return redirect(url_for('.login'))#, next=request.url))
        return f(*args, **kwargs)
    return decorated_function



@views.route("/")
@login_required
def root():
	return render_template('index.html')

@views.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        session['username'] = request.form['username']
        session["logged_in"] = True
        return redirect(url_for('.root'))
    return render_template("login.html", form=form)
