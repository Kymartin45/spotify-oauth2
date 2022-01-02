# Connect to Spotify API endpoints 
Sample code for OAuth 2.0 Authorization Code Flow with PKCE 

* [Spotify Documentation](https://developer.spotify.com/documentation/)
* [OAuth 2 Auth Code Flow with PKCE](https://developer.spotify.com/documentation/general/guides/authorization/code-flow/)
* [Flask web application framework](https://github.com/pallets/flask)

## Installing (Python 3+)
*Built on 3.10.1* 
Install using pip 

```bash 
pip install requests
pip install python-dotenv
pip install flask
```

### Usage
Set up environment variables for your Spotify project. You can find your credentials in your [Spotify Dashboard](https://developer.spotify.com/dashboard/)

```python 
client_id = {SPOTIFY_CLIENT_ID}
client_secret = {SPOTIFY_CLIENT_SECRET}
redirect_uri = {SPOTIFY_REDIRECT_URI}
```

Create `.env` file in root directory 

```dosini
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_ID=
SPOTIFY_REDIRECT_URI=
```
