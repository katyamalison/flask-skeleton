# project/server/main/views.py


from flask import render_template, Blueprint, url_for, redirect


main_blueprint = Blueprint('main', __name__,)


@main_blueprint.route('/')
def home():
    return redirect(url_for('lyric.input_artist'))


@main_blueprint.route("/about/")
def about():
    return render_template("main/about.html")
