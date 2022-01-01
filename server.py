# https://projects.raspberrypi.org/en/projects/python-web-server-with-flask/1
# setup Flask environment
# https://pythonbasics.org/flask-http-methods/ (HTTP methods)
# https://medium.com/analytics-vidhya/discoverdaily-a-flask-web-application-built-with-the-spotify-api-and-deployed-on-google-cloud-6c046e6e731b

from flask import Flask, render_template
from requests.api import request
 
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') # find index.html

# @app.route('https://accounts.spotify.com/authorize', methods = ['POST'])
# def authUser():
    

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)