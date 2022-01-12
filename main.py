# venv activation (bash)
# source ./env/Scripts/activate
from flask import Flask, render_template, request
from werkzeug.utils import redirect
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

@app.route('/')
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
    getToken.access_token = r.json()['access_token']
    return redirect('/user')
    
@app.route('/user')
def userPage():
    user_url = 'https://api.spotify.com/v1/me'
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {getToken.access_token}'
    }
    r = requests.get(user_url, headers=header)
    if r.status_code != 200:
        return f'<h1>Error {r.status_code}</h1>'
    
    r.raise_for_status()
    pretty_res = json.loads(r.text)
    userPage.display_name = r.json()['display_name']
    userPage.user_id = r.json()['id']
        
    return render_template(
        'user.html',
        title = 'User authenticated', 
        access_token = getToken.access_token,
        user_info = json.dumps(pretty_res, indent=2),
        username = userPage.display_name,
        user_id = r.json()['id']
        ) 

# get user playlists
@app.route('/user/playlists')
def getUserPlaylists():
    user_playlist_url = f'https://api.spotify.com/v1/users/{userPage.user_id}/playlists'
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {getToken.access_token}'
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
    print(ids)
    
    # track_url = f'https://api.spotify.com/v1/playlists/{ids[0]}/tracks'
    # req_track = requests.get(track_url, headers=header)
    # track_data = json.loads(req_track.text)['items']
    
    # TEMPORARY BELOW (WIP) - get tracks among each playlist given their playlist_id {id}
    tracks = []
    for id in ids:
        track_url = f'https://api.spotify.com/v1/playlists/{id}/tracks'
        req_track = requests.get(track_url, headers=header)
        track_data = json.loads(req_track.text)['items']
        for track in track_data:
            tracks.append({
                'track_name': track['track']['name'],
                'track_artist': track['track']['artists'][0]['name'],
                'track_image': track['track']['album']['images'][0]['url'],
                'track_url': track['track']['external_urls']['spotify'],
                'track_id': track['track']['id']
            })

    # tracks = []
    # for track in track_data:
    #     tracks.append({
    #         'track_name': track['track']['name'],
    #         'track_artist': track['track']['artists'][0]['name']
    #     })
    # print(tracks)
    
    # map_id = map(lambda playlist : playlist['id'], playlist_data['items'])
    # playlist_ids = list(map_id)
                                        
    return render_template(
        'userPlaylists.html',
        username = userPage.display_name,
        playlist_data = playlist_data,
        tracks = tracks
        )

def refreshAccessToken():
    refresh_token = 'https://accounts.spotify.com/api/token'
    header = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': getToken.refresh_token,
        'client_id': CLIENT_ID
    }
    r = requests.post(refresh_token, params=payload, headers=header)
    if r.status_code != 200: 
        print(f'error: {r.status_code}')
        return r.close()
    print(r.json()) 
    refreshAccessToken.new_access_token = r.json()['access_token'] # new access token if requested refresh
    
if __name__ == '__main__':
    app.run(debug=True, port=8080)
    
