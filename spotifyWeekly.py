import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth

from flask import Flask, request, url_for, session, redirect, render_template

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'your_secret_key'
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    if code:
        token_info = create_spotify_oauth().get_access_token(code)
        session[TOKEN_INFO] = token_info
        return redirect(url_for('display_playlists'))
    else:
        return "Authorization failed. Please try again."

@app.route('/displayPlaylists')
def display_playlists():
    try:
        token_info = get_token()
    except Exception as e:
        print("Error:", e)
        return redirect('/')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    try:
        user_playlists = sp.current_user_playlists()['items']
    except Exception as e:
        print("Error fetching playlists:", e)
        user_playlists = []

    playlists_data = []
    for playlist in user_playlists:
        playlist_info = {
            'name': playlist['name'],
            'images': playlist['images'] if 'images' in playlist else [],
            'id': playlist['id']
        }
        playlists_data.append(playlist_info)
    
    return render_template('playlists.html', playlists=playlists_data)
    
@app.route('/playlist/<playlist_id>/statistics')
def playlist_statistics(playlist_id):
    try:
        token_info = get_token()
    except Exception as e:
        print("Error:", e)
        return redirect('/')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    try:
        playlist = sp.playlist(playlist_id)
        playlist_name = playlist['name']
        playlist_tracks = sp.playlist_tracks(playlist_id)
        song_genres = []

        for item in playlist_tracks['items']:
            track = item['track']
            artists = track['artists']
            for artist in artists:
                artist_id = artist['id']
                artist_info = sp.artist(artist_id)
                genres = artist_info['genres']
                song_genres.extend(genres)
        
        # Calculate genre counts
        genre_counts = {}
        for genre in song_genres:
            if genre in genre_counts:
                genre_counts[genre] += 1
            else:
                genre_counts[genre] = 1

    except Exception as e:
        print("Error fetching playlist statistics:", e)
        playlist_name = "Unknown"
        song_genres = []
        genre_counts = {}

    return render_template('playlist_statistics.html', playlist_name=playlist_name, song_genres=song_genres, genre_counts=genre_counts)

def get_token():
    token_info = session.get(TOKEN_INFO)
    if not token_info:
        raise Exception("User not logged in")

    now = int(time.time())
    if token_info.get('expires_at', 0) - now < 60:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info

    return token_info
    
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = "b93be33552e744fbab000f43e40805eb", 
        client_secret = "986e249b8e414f14bd20ae9b670610c9",
        redirect_uri = url_for('redirect_page', _external=True),
        scope = 'user-library-read playlist-modify-public playlist-modify-private'
    )

if __name__ == '__main__':
    app.run(debug=True)