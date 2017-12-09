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

def verbose(song):
    words = word_tokenize(song.lyrics)
    print(words)

def artist_verbose(artist):
    songs = get_artist_songs(artist)
    for song in songs:
        verbose(song)

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

def artist_pov(artist):
    songs = get_artist_songs(artist)
    for song in songs:
        pov(song)

def all_songs_pov():
    songs = Song.query.all()
    for song in songs:
        pov(song)
        
def get_all_song_words():
    songs = Song.query.all()
    frequencies = Counter([])
    for song in songs:
        lyrics = sanitize_lyrics(song.lyrics)
        words = set(word_tokenize(lyrics.lower()))
        frequencies += Counter(words)

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
    

def unique_topics():
    frequencies = get_all_song_words()
    songs = Song.query.all()

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

def artist_unique(artist):
    songs = get_artist_songs(artist.name)
    #unique_topics()
    print("unique: ", artist.name)
    
    if songs:
        print("SONGS", songs)
        unique_words = 0
        for song in songs:
            song_unique_words(song)
            unique_words += song.unique_words
            artist.unique_words = unique_words / len(songs)
            db.session.commit()

def song_unique_words(song):
    frequencies = get_all_song_words()
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
                
