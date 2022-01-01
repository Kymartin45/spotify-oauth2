# venv activation (bash)
# source ./env/Scripts/activate

import requests 
from dotenv import dotenv_values
import base64
import os 
import hashlib

config = dotenv_values('.env')
CLIENT_ID = config.get('CLIENT_ID')
CLIENT_SECRET = config.get('CLIENT_SECRET')
REDIRECT_URI = config.get('REDIRECT_URI')

scopes = [
    'ugc-image-upload',
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

def authUser():
    auth = 'https://accounts.spotify.com/authorize'
    req_params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'state': 'state',
        'scope': ' '.join(scopes),
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge
    }
    r = requests.get(auth, params=req_params)
    
    if r.status_code != 200:
        print(f'error: {r.status_code}')
        return r.close()
    print(r.url) # temp manually get auth url 

def getToken(code):
    req_token = 'https://accounts.spotify.com/api/token'
    header = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth}'
    }
    req_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'code_verifier': code_verifier
    }
    r = requests.post(req_token, params=req_params, headers=header)
    if r.status_code != 200: 
        print(f'error: {r.status_code}')
        return r.close()
    getToken.access_token = r.json()['access_token'] # retreive access token for future requests
    getToken.refresh_token = r.json()['refresh_token'] # refresh token for POST /api/token

authUser()
code = input('paste your auth code from redirect url: ')
getToken(code)

def refreshAccessToken():
    refresh_token = 'https://accounts.spotify.com/api/token'
    header = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    req_params = {
        'grant_type': 'refresh_token',
        'refresh_token': getToken.refresh_token,
        'client_id': CLIENT_ID
    }
    r = requests.post(refresh_token, params=req_params, headers=header)
    if r.status_code != 200: 
        print(f'error: {r.status_code}')
        return r.close()
    print(r.json()) 
    refreshAccessToken.new_access_token = r.json()['access_token'] # new access token if requested refresh
    
# refreshAccessToken()