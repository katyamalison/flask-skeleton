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
    magic.create_training_data()
    form = InputArtistForm(request.form)
    if form.validate_on_submit():
        # title() to avoid duplicate entries in db depending on case
        a1 = form.artist1.data.title()
        a2 = form.artist2.data.title()
        if not Artist.query.filter_by(name=a1).first():
            artist1 = magic.store_artist_info(a1, 2010)
            if artist1:
                process.artist_all(artist1)
            else:
                print("could not find artist " + a1)
                return redirect(url_for('lyric.artist_not_found', a=a1))
        if not Artist.query.filter_by(name=a2).first():
            artist2 = magic.store_artist_info(a2, 2010)
            if  artist2:
                process.artist_all(artist2)
            else:
                print("could not find artist " + a2)
                return redirect(url_for('lyric.artist_not_found', a=a2))
        return redirect(url_for('lyric.results', a1=a1, a2=a2))
    return render_template('lyrics/input_artist.html', form=form)

@lyric_blueprint.route('/results')
def results():
    artist1 = Artist.query.filter_by(name=request.args.get('a1')).first()
    artist2 = Artist.query.filter_by(name=request.args.get('a2')).first()

    a1 = { 'image' : artist1.image_url,
           'unique' : process.get_artist_unique_scale(artist1),
           'allit' : process.get_artist_allit_scale(artist1),
           'pov' : process.get_artist_pov_scale(artist1)
    }
    a2 = { 'image' : artist2.image_url,
           'unique' : process.get_artist_unique_scale(artist2),
           'allit' : process.get_artist_allit_scale(artist2),
           'pov' : process.get_artist_pov_scale(artist2)
    }
    
    return render_template('lyrics/results.html', artists=[a1, a2])

@lyric_blueprint.route('/artist_not_found')
def artist_not_found():
    return render_template('lyrics/artist_not_found.html',
                           artist=request.args.get('a'))

@lyric_blueprint.route('/test')
def test():
    process.allit_scale()
    process.pov_scale()
    process.unique_scale()
    process.get_artist_allit_scale(Artist.query.filter_by(name='Lil Wayne').first())
    return (render_template('main/about.html'))
