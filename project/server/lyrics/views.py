import requests
from bs4 import BeautifulSoup
import pdb
from pprint import pprint
import http.client, urllib.parse, json
from flask import render_template, Blueprint, url_for, \
    redirect, flash, request
from project.server import bcrypt, db
from project.server.models import Artist, Song
from project.server.lyrics.forms import InputArtistForm, TryAgainForm
import project.server.lyrics.addartists as magic
import project.server.lyrics.process as process

lyric_blueprint = Blueprint('lyric', __name__,)

#####################
#      ROUTES       #
#####################

@lyric_blueprint.route('/input_artist', methods=['GET', 'POST'])
def input_artist():
    #magic.insert_genres()
    #magic.create_training_data()
    form = InputArtistForm(request.form)
    if form.validate_on_submit():
        # title() to avoid duplicate entries in db depending on case
        a1 = form.artist1.data.title()
        a2 = form.artist2.data.title()
        if not Artist.query.filter_by(name=a1).first():
            if not magic.get_artist_info(a1, 2010):
                # change to error
                print("could not find artist " + a1)
                return redirect(url_for('lyric.artist_not_found', a=a1))
        if not Artist.query.filter_by(name=a2).first():
            if not magic.get_artist_info(a2, 2010):
                # change to error
                print("could not find artist " + a2)
                return redirect(url_for('lyric.artist_not_found', a=a2))
        return redirect(url_for('lyric.results', a1=a1, a2=a2))
    return render_template('lyrics/input_artist.html', form=form)

@lyric_blueprint.route('/results')
def results():
    a1 = Artist.query.filter_by(name=request.args.get('a1')).first()
    a2 = Artist.query.filter_by(name=request.args.get('a2')).first()
    #magic.get_top_artists()
    process.artist_unique(a1)
    process.artist_unique(a2)
    return render_template('lyrics/results.html', artists=[a1, a2])

@lyric_blueprint.route('/artist_not_found')
def artist_not_found():
    return render_template('lyrics/artist_not_found.html',
                           artist=request.args.get('a'))

@lyric_blueprint.route('/test')
def test():
    #process.all_songs_pov()
    #process.unique_topics()
    #process.artist_unique_topics()
    process.all_songs_alliteration()
    return (render_template('main/about.html'))
