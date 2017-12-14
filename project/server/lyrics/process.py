import pickle
import pdb
from pprint import pprint
from project.server import bcrypt, db
from project.server.models import Artist, Song, Genre
from collections import Counter
import sys
import re
from nltk import word_tokenize

pronouns = {'first' : r'\b(my|I|mine|myself)\b',
            'first_plural' : r'\b(we|our|ours|us)\b',
            'second' : r'\b(you|your|yours|yourself)\b',
            'third' : r'\b(he|his|him|her|hers|she|himself|herself)\b'}

alliterationy = r'\b([a-z])[a-z]+ (\1[a-z]+)'
alot_alliteration = r'\b([a-z])[a-z]+ (\1[a-z]+) (\1[a-z]+)'



FLAGS = re.MULTILINE | re.DOTALL | re.IGNORECASE

test_artist = 'Wilco'

UNIQUE_CUTOFF = 4

def get_artist_songs(artist_name):
    artist = Artist.query.filter_by(name=artist_name).first()
    songs = Song.query.filter_by(artist_id=artist.id).all()

    return songs

############################
#    CLEAN UP DATABASE     #
############################

def delete_artist_no_genre():
    genreless = Artist.query.filter_by(genre_id=None).all()
    #songless = Artist.query.filter_by(songs=None).all()
    
    for artist in genreless:
        print(artist.name)
        db.session.delete(artist)

    try:
        db.session.commit()
    except:
        print('could not delete genreless artists')
        db.session.rollback()

############################
# PROCESSING TRAINING DATA #
############################
def allit_scale():
    all = Artist.query.order_by(Artist.alliteration).all()
    lo = all[0].alliteration
    hi = all[len(all) - 1].alliteration
    pickle.dump(lo, open('pickle/allit_lo.p', 'wb'))
    pickle.dump(hi, open('pickle/allit_hi.p', 'wb'))

def pov_scale():
    first = Artist.query.order_by(Artist.first).all()
    second = Artist.query.order_by(Artist.second).all()
    third = Artist.query.order_by(Artist.third).all()
    
    vals = { 'first_lo' : first[0].first,
             'first_hi' : first[len(first) - 1].first,
             'second_lo' : second[0].second, 
             'second_hi' : second[len(second) - 1].second,
             'third_lo' : third[0].third,
             'third_hi' : third[len(third) - 1].third
    }

    for file, value in vals.items():
        pickle.dump(value, open('pickle/%s.p' % file, 'wb'))

def unique_scale():
    all = Artist.query.order_by(Artist.unique_words).all()
    unique_lo = all[0].unique_words
    unique_hi = all[len(all) - 1].unique_words
    
    pickle.dump(unique_lo, open('pickle/unique_lo.p', 'wb'))
    pickle.dump(unique_hi, open('pickle/unique_hi.p', 'wb'))

def all():
    songs = Song.query.all()
    artists = Artist.query.all()

    all_alliteration(songs, artists)
    all_pov(songs, artists)
    all_unique_words(songs, artists)
    
def all_alliteration(songs, artists):
    for song in songs:
        alliteration(song)

        
    for artist in artists:
        ss = Song.query.filter_by(artist_id=artist.id).all()
        allit = 0
        print('its lit', len(ss))
        for s in ss:
            allit += s.alliteration
        try:
            artist.alliteration = (allit / len(ss))
        except:
            print(artist.name + " has no songs. bye!")
            db.session.delete(artist)
            db.session.commit()

    db.session.commit()


def all_pov(songs, artists):
    for song in songs:
        print('pov')
        pov(song)

    for artist in artists:
        first = 0
        first_plural = 0
        second = 0
        third = 0
        ss = Song.query.filter_by(artist_id=artist.id).all()
        for s in ss:
            first += s.first
            first_plural += s.first_plural
            second += s.second
            third += s.third

        artist.first = first / len(songs)
        artist.first_plural = first_plural / len(songs)
        artist.second = second / len(songs)
        artist.third = third / len(songs)
        db.session.commit()

def all_unique_words(songs, artists):
    frequencies = get_all_song_words()

    for song in songs:
        uncommon_words = 0
        lyrics = sanitize_lyrics(song.lyrics)
        words = word_tokenize(lyrics.lower())
        if words:
            unique_words = set(words)
            for word in unique_words:
                if frequencies[word] < UNIQUE_CUTOFF:
                    uncommon_words += 1
            ratio = uncommon_words / len(words)
            song.unique_words = ratio
            song.word_count = len(words)
            db.session.commit()
            print(song.title, ratio)

    for artist in artists:
        uniques = 0
        ss = Song.query.filter_by(artist_id=artist.id).all()
        for s in ss:
            uniques += song.unique_words
        artist.unique_words = uniques / len(ss)

    db.session.commit()


####################
#     ARTISTS      #
####################
def percentage(part, whole):
  return 100 * float(part)/float(whole)

def get_artist_unique_scale(artist):
    unique_lo = pickle.load(open('pickle/unique_lo.p', 'rb'))
    unique_hi = pickle.load(open('pickle/unique_hi.p', 'rb'))
    range = unique_hi - unique_lo
    artist_score = artist.unique_words - unique_lo

    return (percentage(artist_score, range))


def get_artist_allit_scale(artist):
    allit_lo = pickle.load(open('pickle/allit_lo.p', 'rb'))
    allit_hi = pickle.load(open('pickle/allit_hi.p', 'rb'))
    range = allit_hi - allit_lo
    artist_score = artist.alliteration - allit_lo

    return (percentage(artist_score, range))

def get_artist_pov_scale(artist):
    first_lo = pickle.load(open('pickle/first_lo.p', 'rb'))
    first_hi = pickle.load(open('pickle/first_hi.p', 'rb'))
    second_lo = pickle.load(open('pickle/second_lo.p', 'rb'))
    second_hi = pickle.load(open('pickle/second_hi.p', 'rb'))
    third_lo = pickle.load(open('pickle/second_lo.p', 'rb'))
    third_hi = pickle.load(open('pickle/second_hi.p', 'rb'))

    first_range = first_hi - first_lo
    second_range = second_hi - second_lo
    third_range = third_hi - third_lo
    first_artist_score = artist.first - first_lo
    second_artist_score = artist.second - second_lo
    third_artist_score = artist.third - third_lo

    first_percent = (percentage(first_artist_score, first_range))
    second_percent = (percentage(second_artist_score, second_range))
    third_percent = (percentage(third_artist_score, third_range))

    str = ''
    if first_percent > 50:
        if second_percent > 50:
            if third_percent > 50:
                str = 'Writes from the perspective of many people'
            else:
                str = 'Writes from the perspective of "me" and "you"'
        else:
            str = "Writes about themselves a lot"
    elif third_percent > 50:
        str = 'Writes in the third person. Probably about themselves, though.'
    else:
        str = 'Avoids personal matters in song lyrics'
                
    return str


def artist_all(artist):
    artist_alliteration(artist)
    artist_pov(artist)
    artist_unique(artist)

def artist_alliteration(artist):
    songs = Song.query.filter_by(artist_id=artist.id).all()
    print(songs)

    allit = 0
    for song in songs:
        alliteration(song)
        allit += song.alliteration
    try:
        artist.alliteration = (allit / len(songs))
        db.session.commit()
    except:
        print(artist.name + " has no songs. bye!")

def artist_pov(artist):
    songs = Song.query.filter_by(artist_id=artist.id).all()

    first = 0
    first_plural = 0
    second = 0
    third = 0
    for song in songs:
        print('pov')
        pov(song)
        first += song.first
        print(first)
        first_plural += song.first_plural
        second += song.second
        third += song.third

    artist.first = first / len(songs)
    artist.first_plural = first_plural / len(songs)
    artist.second = second / len(songs)
    artist.third = third / len(songs)

    db.session.commit()

def artist_unique(artist):
    songs = Song.query.filter_by(artist_id=artist.id).all()
    print("unique: ", artist.name)
    
    if songs:
        print("SONGS", songs)
        unique = 0
        for song in songs:
            unique_words(song)
            unique += song.unique_words
        artist.unique_words = unique / len(songs)
        db.session.commit()

####################
#      SONGS       #
####################
def alliteration(song):
    lyrics = sanitize_lyrics(song.lyrics)
    very_alit = len(re.findall(alot_alliteration, lyrics, flags=FLAGS))
    alit = len(re.findall(alliterationy, lyrics, flags=FLAGS))
    
    final_alliteration = (.5 * (alit - very_alit)) + (2 * very_alit)
    song.alliteration = final_alliteration
    print('alliterating')
    try: db.session.commit()
    except:
        print('couldnt alliterate ' + song.title())
        db.session.rollback()
    print(final_alliteration)
    return final_alliteration

def pov(song):
    print(song.lyrics)
    for key, value in pronouns.items():
        pov = re.findall(value, song.lyrics, flags=FLAGS)
        pov_count = len(pov)
        if key == 'first':
            song.first = pov_count
        elif key == 'first_plural':
            song.first_plural = pov_count
        elif key == 'second':
            song.second = pov_count
        elif key == 'third':
            song.third = pov_count
        print(key)
        print(pov_count)
    db.session.commit()

def unique_words(song):
    frequencies = pickle.load(open('pickle/frequencies.p', 'rb'))

    uncommon_words = 0
    lyrics = sanitize_lyrics(song.lyrics)
    words = word_tokenize(lyrics.lower())
    if words:
        unique_words = set(words)
        for word in unique_words:
            if frequencies[word] < UNIQUE_CUTOFF:
                uncommon_words += 1
        ratio = uncommon_words / len(words)
        song.unique_words = ratio
        song.word_count = len(words)
        db.session.commit()
        print(song.title, ratio)


####################
#    OTHER SHIT    #
####################
    
        
def get_all_song_words():
    songs = Song.query.all()
    frequencies = Counter([])
    for song in songs:
        lyrics = sanitize_lyrics(song.lyrics)
        words = set(word_tokenize(lyrics.lower()))
        frequencies += Counter(words)

    pickle.dump(frequencies, open('pickle/frequencies.p', 'wb'))
    return frequencies

def alliteration(song):
    lyrics = sanitize_lyrics(song.lyrics)
    very_alit = len(re.findall(alot_alliteration, lyrics, flags=FLAGS))
    alit = len(re.findall(alliterationy, lyrics, flags=FLAGS))
    
    final_alliteration = (.5 * (alit - very_alit)) + (2 * very_alit)
    song.alliteration = final_alliteration
    print('alliterating')
    try: db.session.commit()
    except: db.session.rollback()


def all_songs_alliteration():
    songs = Song.query.all()

    for song in songs:
        alliteration(song)
    

            
def sanitize_lyrics(lyrics):
    # take out apostrophes in contractions
    lyrics = re.sub(r"(?<=[a-z])'(?=[a-z])", "", lyrics, flags=FLAGS)
    # replace apostrophes at the end of ing words with a "g"
    lyrics = re.sub(r"(?<=in)'", "g", lyrics, flags=FLAGS)
    # replace words like "heeeeeeeey" with "hey"
    lyrics = re.sub(r'(?<=(.))\1{2,}', "", lyrics, flags=FLAGS)
    # remove all punctuation
    lyrics = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()]', "", lyrics, flags=FLAGS)
        
    return lyrics

def artist_unique_topics():
    artists = Artist.query.all()

    for artist in artists:
        artist_unique(artist)

                
