# venv activation (bash)
# source ./env/Scripts/activate
from flask import Flask, render_template, request
from dotenv import dotenv_values
from werkzeug.utils import redirect
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
        # print(f'error: {r.status_code}')
        return f'<h1>User not authenticated</h1><p>Error code {r.status_code}</p>'
    
    r.raise_for_status()
    getToken.access_token = r.json()['access_token']
    # return f'<h2>{getToken.access_token}</h2>'
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
    
    # render user info 
    return render_template(
        'user.html',
        title = 'User authenticated', 
        access_token = getToken.access_token,
        user_info = json.dumps(pretty_res, indent=2),
        username = r.json()['display_name']
        ) 

# authUser()
# getToken(code)

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
    
# refreshAccessToken()

if __name__ == '__main__':
    app.run(debug=True)
    
