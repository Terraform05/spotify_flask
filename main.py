from flask import render_template
from flask import Flask, redirect, request, session, url_for
import spotipy
from spotipy import oauth2
from pprint import pformat


def file_output(anything):
    f = open("output.txt", "w")
    f.write(anything)
    f.close()


app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SESSION_COOKIE_NAME'] = 'spotify-auth-session'

# Spotify API credentials
SPOTIFY_CLIENT_ID = '1d165da0991a40cb9226148f1a03ad89'
SPOTIFY_CLIENT_SECRET = 'b15a39f7ac174cbc84b2bf9bdae02c60'
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'
SPOTIFY_SCOPE = 'user-library-read'

# Authorization URL parameters
oauth = oauth2.SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE
)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    auth_url = oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    token_info = oauth.get_access_token(request.args.get('code'))
    session['token_info'] = token_info
    return redirect(url_for('profile'))


@app.route('/profile')
def profile():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('login'))
    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)

    # user profile
    user_data = sp.current_user()
    display_name = user_data['display_name']
    user_url = user_data['external_urls']['spotify']
    followers = user_data['followers']['total']
    user_id = user_data['id']
    profile_image = user_data['images'][0]['url']
    profile = [display_name, user_url, followers, user_id, profile_image]
    
    # user playlists
    playlists_dict = {}
    playlists = sp.user_playlists(user_id)
    while playlists:
        for pl in playlists['items']:
            # playlists_dict[pl['uri']] = [pl['name'], pl['collaborative'], pl['description'], pl['followers']['total'], pl['images'][0]['url'], pl['owner']['display_name'], pl['public']] #doesn't work
            playlists_dict[pl['uri']] = [
                pl['name'],
                pl['collaborative'],
                pl['description'],
                # .get because for some reason keeps failing. will fix later
                pl.get('followers', {}).get('total', 0),
                pl['images'][0]['url'],
                pl['owner']['display_name'],
                pl['public']
            ]
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

    # return
    return render_template('profile.html', profile=profile, playlists=playlists_dict)


@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    return 'Logged out'


if __name__ == '__main__':
    app.run(debug=True)
