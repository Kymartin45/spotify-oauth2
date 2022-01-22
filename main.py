# venv activation (bash)
# source ./env/Scripts/activate
from flask import Flask, render_template, request, redirect, flash
from dotenv import dotenv_values
import requests 
import base64
import os 
import hashlib
import json

app = Flask(__name__)

config = dotenv_values('.env')
CLIENT_ID = config.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = config.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = config.get('SPOTIFY_REDIRECT_URI')
app.secret_key = config.get('SECRET_KEY')

scopes = [
    'user-read-private',
    'user-read-email',
    'user-top-read',
    'user-read-recently-played'
]

# generate code_challenge, hash code_verifier 
# may change, but idk 
# source: https://docs.cotter.app/sdk-reference/api-for-other-mobile-apps/api-for-mobile-apps#step-1-create-a-code-verifier
verifier_bytes = os.urandom(32)
code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b'=') # creates code_verifier for token req
challenge_bytes = hashlib.sha256(code_verifier).digest()
code_challenge = base64.urlsafe_b64encode(challenge_bytes).rstrip(b'=') # code_challenge for authenticating user

# Authorization: Basic <base64 encoded client_id:client_secret>
rawAuth = f'{CLIENT_ID}:{CLIENT_SECRET}'
auth = base64.b64encode(rawAuth.encode('ascii')).decode('ascii')

class spotifyApiHandle:
    @app.route('/', methods=['GET'])
    def authUser():
        auth = 'https://accounts.spotify.com/authorize'
        payload = {
            'response_type': 'code',
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'state': 'state',
            'scope': ' '.join(scopes),
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge
        }
        r = requests.get(auth, params=payload)
        
        if r.status_code != 200:
            print(f'error: {r.status_code}')
            return r.close()
        return render_template('index.html', authUrl=r.url)        

    @app.route('/callback')
    def getToken():
        code = request.args.get('code')
        req_token_url = 'https://accounts.spotify.com/api/token'
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {auth}'
        }
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'code_verifier': code_verifier
        }
        r = requests.post(req_token_url, params=payload, headers=header)
        if r.status_code != 200: 
            return f'<h1>User not authenticated</h1><p>Error code {r.status_code}</p>'
        
        r.raise_for_status()
        spotifyApiHandle.getToken.access_token = r.json()['access_token']
        return redirect('/user')
        
    @app.route('/user', methods=['GET'])
    def userPage():
        user_url = 'https://api.spotify.com/v1/me'
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {spotifyApiHandle.getToken.access_token}'
        }
        r = requests.get(user_url, headers=header)
        if r.status_code != 200:
            return f'<h1>Error {r.status_code}</h1>'
        
        r.raise_for_status()
        data = json.loads(r.text)
        user_image = data['images'][0]['url']
        user_followers = data['followers']['total']
        user_product_subscription = data['product']
        
        spotifyApiHandle.userPage.display_name = r.json()['display_name']
        spotifyApiHandle.userPage.user_id = r.json()['id']

        return render_template(
            'user.html', 
            user_image = user_image,
            username = spotifyApiHandle.userPage.display_name,
            user_followers = user_followers,
            user_product_subscription = user_product_subscription,
            show_playlists = '/user/playlists'
            ) 

    @app.route('/user/playlists/', methods = ['GET'])
    def getUserPlaylists():
        user_playlist_url = f'https://api.spotify.com/v1/users/{spotifyApiHandle.userPage.user_id}/playlists'
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {spotifyApiHandle.getToken.access_token}'
        }
        payload = {
            'limit': 20, 
            'offset': 0 
        }
        r = requests.get(user_playlist_url, params=payload ,headers=header)
        data = json.loads(r.text)
        playlists = data['items']
        
        playlist_data = []
        for playlist in playlists:
            playlist_data.append({
                'playlist_name': playlist['name'],
                'playlist_url': playlist['external_urls']['spotify'],
                'playlist_image': playlist['images'][0]['url'],
                'playlist_tracks_url': playlist['tracks']['href'],
                'playlist_id': playlist['id']
            })
        
        map_ids = map(lambda ids: ids['id'], playlists)   
        ids = list(map_ids)
        spotifyApiHandle.getUserPlaylists.playlist_id = ids
                                         
        return render_template(
            'userPlaylists.html',
            username = spotifyApiHandle.userPage.display_name,
            playlist_data = playlist_data
            )
        
    @app.route('/user/top_tracks')
    def getTopTracks():
        top_tracks = f'https://api.spotify.com/v1/me/top/tracks'
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {spotifyApiHandle.getToken.access_token}'
        }
        params = {
            'time_range': 'medium_term' 
        }
        r = requests.get(top_tracks, headers=header, params=params)
        data = json.loads(r.text)
        track_data = data['items']
        
        tracks = []
        for track in track_data:
            tracks.append({
                'track_artist': track['artists'][0]['name'],
                'track_name': track['name'],
                'track_url': track['uri']
            })
            
        return render_template(
            'topTracks.html',
            username = spotifyApiHandle.userPage.display_name,
            track_data=tracks
        )
    
    @app.route('/user/', methods=['GET'])
    def searchItem():
        item_types = ['track']
        search_url = 'https://api.spotify.com/v1/search'
        search = request.args.get("search-results").strip().lower()
        
        if search == '':
            flash('Please search for artists, tracks, or albums')
            return redirect('/user/playlists/', code=302)
        
        payload = {
            'q': search,
            'type': ','.join(item_types),
            'include_external': 'audio',
            'market': 'US',
            'limit': 10
        }
        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {spotifyApiHandle.getToken.access_token}'
        }
        r = requests.get(search_url, headers=header, params=payload)
        # return str(r.json())
        data = json.loads(r.text)
        # return str(data['albums']['items'])
        search_results = data['tracks']['items']
        
        results = []
        for result in search_results:
            results.append({
                'artist_name': result['artists'][0]['name'],
                'artist_id': result['id'],
                'album_type': result['album']['album_type'],
                'track_uri': result['uri'],
                'track_name': result['name'],
                'popularity': result['popularity'] # sort search results by popularity 
            })
        
        return render_template(
            'searchResults.html',
            search_results = results
        )

    def refreshAccessToken():
        refresh_token = 'https://accounts.spotify.com/api/token'
        header = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': spotifyApiHandle.getToken.refresh_token,
            'client_id': CLIENT_ID
        }
        r = requests.post(refresh_token, params=payload, headers=header)
        if r.status_code != 200: 
            print(f'error: {r.status_code}')
            return r.close()
        print(r.json()) 
        spotifyApiHandle.refreshAccessToken.new_access_token = r.json()['access_token'] # new access token if requested refresh
    
if __name__ == '__main__':
    app.run(debug=True, port=8080)
    
