import requests
from bs4 import BeautifulSoup
import pdb
from pprint import pprint
import http.client, urllib.parse, json
from project.server import bcrypt, db
from project.server.models import Artist, Song, Genre
import billboard
import sys

# billboard stuff
chart_url = 'billboard-200'
genres = ['pop', 'indie', 'rock', 'alternative rock', 'rap', 'soul', 'hardcore', 'jazz', 'funk', 'blues', 'electronic', 'folk', 'country', 'emo', 'rnb', 'hip-hop', 'pop-punk']

# genius api stuff
genius_base_url = "http://api.genius.com"
headers = {'Authorization':
           'Bearer LAlB9OoHM4T5oDheDvIluyjcj5tGROWZjlsyX93V8BKT-IhswXMHw1XAqmxKtEcE'}
search_url = genius_base_url + "/search"

# bing image api stuff
bing_base_url = "api.cognitive.microsoft.com"
subscriptionKey = "d8524841495c4cc98575f5e8e6c9efa5"
image_path = "/bing/v7.0/images/search"

# lastfm api
lastfm_api_key = '6963278a164aa2b0876e19f2989f967b'
lastfm_base_url = "ws.audioscrobbler.com"


### TO DO: make it so that 'the' doesnt need to be included

######################
# GET TRAINNING DATA #
#####################

def insert_genres():
    for name in genres:
        gen = Genre(name)
        try:
            db.session.add(gen)
            db.session.commit()
        except:
            db.session.rollback()
            break
        
def create_training_data():
    top_artists = get_top_artists()
    #i = 0
    for artist, year in top_artists.items():
        #if i == 30: break
        #i += 1
        if not Artist.query.filter_by(name=artist.title()).first():
            if get_artist_info(artist.title(), year):
                print('stored %s in database' % artist.title())
            else:
                print('could not find ' + artist)
        
def get_top_artists():
    artists = {}
    for year in range (1970, 2017):
        date = "05-12-" + str(year)
        chart = billboard.ChartData(chart_url, str(year) + "-05-12")
        print("getting year %s" % date)
        i = 0
        for entry in chart:
            i += 1
            if i > 30:
                break
            if entry.artist in artists:
                pass
            else:
                artists[entry.artist] = year
    print(artists)
        
    return artists

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
    conn.request("GET", image_path + "?q=" + query + '&count=30', headers=headers)
    response = conn.getresponse()
    headers = [k + ": " + v for (k, v) in response.getheaders()
                   if k.startswith("BingAPIs-") or k.startswith("X-MSEdge-")]
    return headers, response.read().decode("utf8")

def find_artist_image(artist):
    if len(subscriptionKey) == 32:
        print('Searching the Web for: ', artist)
        
        headers, result = BingWebSearch(artist)
        results = json.loads(result)

        image_url = ''
        for hit in results['value']:
            # hacky way of getting the best-fitting image IF POSSIBLE
            if 0.53 < hit['height'] / hit['width'] < 0.67:
                if not image_url:
                    image_url = hit['contentUrl']
            if 0.56 < hit['height'] / hit ['width'] < 0.63:
                image_url = hit['contentUrl']
                break

        return image_url
        
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
        params = {'per_page' : 25, 'page' : i, 'sort' : 'popularity'}
        response = requests.get(artist_url, params=params, headers=headers)
        json = response.json()
        if json['response']['next_page'] == None:
            print('no next page')
            break
        for song in json['response']['songs']:
            if song['title'] not in song_api_paths:
                song_api_paths[song['title']] = song['api_path']
    print('number of songs:', len(song_api_paths))
    for title, path in song_api_paths.items():
        print('getting song')
        lyrics = get_song_lyrics(path)
        song = Song(
            title=title,
            lyrics=lyrics,
        )
        try:
            db.session.add(song)
            artist.songs.append(song)
        except:
            db.session.rollback()
            print("Unexpected error:", sys.exc_info()[0])
            
def get_artist_genre(artist):
    # this one has to be first
    params = urllib.parse.urlencode(
        {'method' : 'artist.getInfo'}
    )
    params = params + '&' +  urllib.parse.urlencode(
        {'artist' : artist.name,
         'api_key' : lastfm_api_key}
    )

    print(params)

    lastfm = http.client.HTTPConnection(lastfm_base_url)
    lastfm.request("POST", "/2.0/?", params + '&format=json')

    response = lastfm.getresponse().read().decode('utf-8') 
    response = json.loads(response)
    #pprint(response)
    try:
        for genre in response['artist']['tags']['tag']:
            print(genre['name'])
            gen = Genre.query.filter_by(name=genre['name'].lower()).first()
            if gen:
                gen.artists.append(artist)
                break
    except KeyError:
        pass

def get_artist_info(artist, year):
    found_artist = False
    params = {'q' : artist}
    response = requests.get(search_url, params=params, headers=headers)
    json = response.json()
    for hit in json['response']['hits']:
        if equal(hit["result"]["primary_artist"]["name"], artist):
            found_artist = True
            api_path = hit["result"]["primary_artist"]["api_path"]
            artist = Artist(
                name=hit["result"]["primary_artist"]["name"],
                api_path=api_path,
                image_url=find_artist_image(artist),
                year=year
            )

            try:
                db.session.add(artist)
                db.session.commit()
                get_artist_genre(artist)
                get_all_lyrics(artist)
                print('stored artist and songs in db')
            except:
                print('artist not stored-- rollback')
                db.session.rollback()
                print("Unexpected error:", sys.exc_info()[0])
            break
    
    return found_artist

