import requests
from bs4 import BeautifulSoup
import pdb
from pprint import pprint
import http.client, urllib.parse, json

from flask import render_template, Blueprint, url_for, \
    redirect, flash, request

from project.server import bcrypt, db
from project.server.models import Artist, Song
from project.server.lyrics.forms import InputArtistForm

lyric_blueprint = Blueprint('lyric', __name__,)

# genius API stuff
genius_base_url = "http://api.genius.com"
headers = {'Authorization': 'Bearer LAlB9OoHM4T5oDheDvIluyjcj5tGROWZjlsyX93V8BKT-IhswXMHw1XAqmxKtEcE'}
search_url = genius_base_url + "/search"

# bing image api
bing_base_url = "api.cognitive.microsoft.com"
subscriptionKey = "d8524841495c4cc98575f5e8e6c9efa5"
image_path = "/bing/v7.0/images/search"

#artist_names = ['Pavement', 'Smashing Pumpkins']

def equal(a, b):
    try:
        return a.lower() == b.lower()
    except AttributeError:
        return a == b

def BingWebSearch(search):
    "Performs a Bing Web search and returns the results."

    headers = {'Ocp-Apim-Subscription-Key': subscriptionKey}
    conn = http.client.HTTPSConnection(bing_base_url)
    query = urllib.parse.quote(search)
    conn.request("GET", image_path + "?q=" + query, headers=headers)
    response = conn.getresponse()
    headers = [k + ": " + v for (k, v) in response.getheaders()
                   if k.startswith("BingAPIs-") or k.startswith("X-MSEdge-")]
    return headers, response.read().decode("utf8")

def find_artist_image(artist):
    if len(subscriptionKey) == 32:
        print('Searching the Web for: ', artist)
        
        headers, result = BingWebSearch(artist)
        print("\nRelevant HTTP Headers:\n")
        print("\n".join(headers))
        print("\nJSON Response:\n")
        print(json.dumps(json.loads(result), indent=4))
        
    else:
        print("Invalid Bing Search API subscription key!")
        print("Please paste yours into the source code.")

def get_song_lyrics(song_api_path):
    song_url = genius_base_url + song_api_path
    response = requests.get(song_url, headers=headers)
    json = response.json()
    path = json["response"]["song"]["path"]
    #gotta go regular html scraping... come on Genius
    page_url = "http://genius.com" + path
    page = requests.get(page_url)
    html = BeautifulSoup(page.text, "html.parser")
    #remove script tags that they put in the middle of the lyrics
    [h.extract() for h in html('script')]
    #at least Genius is nice and has a tag called 'lyrics'!
    lyrics = html.find('div', class_='lyrics').get_text() #updated css where the lyrics are based in HTML
    # put lyrics in db
    return lyrics

def get_all_lyrics(artist):
    print('in lyrics foo')
    song_api_paths = {}
    artist_url = genius_base_url + artist.api_path + "/songs"
    for i in range(1, 2):
        params = {'per_page' : 10, 'page' : i}
        response = requests.get(artist_url, params=params, headers=headers)
        json = response.json()
        #if json['response']['next_page'] == None:
            #break
        for song in json['response']['songs']:
            if song['title'] not in song_api_paths:
                song_api_paths[song['title']] = song['api_path']
    for title, path in song_api_paths.items():
        lyrics = get_song_lyrics(path)
        song = Song(
            title=title,
            lyrics=lyrics,
        )
        try:
            db.session.add(song)
            artist.songs.append(song)
        except:
            print("Unexpected error:", sys.exc_info()[0])

def get_artist_info(artist):
    found_artist = False
    params = {'q' : artist}
    response = requests.get(search_url, params=params, headers=headers)
    json = response.json()
    print('here')
    for hit in json['response']['hits']:
        print('here again')
        if equal(hit["result"]["primary_artist"]["name"], artist):
            found_artist = True
            api_path = hit["result"]["primary_artist"]["api_path"]
            artist = Artist(
                name=hit["result"]["primary_artist"]["name"],
                api_path=api_path
            )
            print('hit it bb')
            try:
                db.session.add(artist)
                get_all_lyrics(artist)
                print('stored artist and songs in db')
            except:
                print("Unexpected error:", sys.exc_info()[0])
            break
    db.session.commit()
    return found_artist
    
@lyric_blueprint.route('/input_artist', methods=['GET', 'POST'])
def input_artist():
    form = InputArtistForm(request.form)
    if form.validate_on_submit():
        a1 = form.artist1.data
        a2 = form.artist2.data
        if not Artist.query.filter_by(name=a1).first():
            if not get_artist_info(a1):
                # change to error
                return redirect(url_for('lyric.input_artist'))
        if not Artist.query.filter_by(name=a2).first():
            if not get_artist_info(a2):
                # change to error
                return redirect(url_for('lyric.input_artist'))
        return redirect(url_for('lyric.results', a1=a1, a2=a2))
    return render_template('lyrics/input_artist.html', form=form)

@lyric_blueprint.route('/results')
def results():
    a1 = request.args.get('a1')
    a2 = request.args.get('a2')
    
    find_artist_image(a1)

    print(a1, a2)
    return render_template('lyrics/results.html')
