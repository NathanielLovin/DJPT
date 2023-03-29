import os
# from dotenv import load_dotenv
import openai
import spotipy
import time
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth 
from flask import Flask, request, jsonify, render_template, Response, session, redirect, send_file, make_response
from flask_cors import CORS

# load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
# auth_manager_oauth = SpotifyOAuth(scope="playlist-modify-public playlist-modify-private")
auth_manger_client = SpotifyClientCredentials()
app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
CORS(app)

@app.route("/")
def index():
  auth_manager = spotipy.oauth2.SpotifyOAuth(scope='playlist-modify-public playlist-modify-private playlist-read-private',
                                               show_dialog=True)
  if request.args.get("code"):
    code = auth_manager.get_access_token(request.args.get("code"), as_dict=True, check_cache=False)
    resp = make_response(redirect('/'))
    print(code)
    resp.set_cookie('token', code['access_token'])
    resp.set_cookie('expires_at', str(code['expires_at']))
    return resp
  return render_template("index.html")

@app.route("/privacy")
def privacy():
  return render_template("index.html")

@app.route('/sign_out')
def sign_out():
    resp = make_response(redirect('/'))
    resp.delete_cookie('token')
    return redirect('/')

@app.route("/sign_in")
def sign_in():
  auth_manager = spotipy.oauth2.SpotifyOAuth(scope='playlist-modify-public playlist-modify-private playlist-read-private', show_dialog=True)
  auth_url = auth_manager.get_authorize_url()
  print(auth_url)
  return jsonify({"url": auth_url})

@app.route("/logged_in")
def logged_in():
  code = request.cookies.get('token')
  expires = request.cookies.get('expires_at')
  if code and int(expires) > time.time():
    return jsonify(True)
  return jsonify(False)

@app.route("/playlist/generate", methods=["POST"])
def generate_playlist():
  #Get number and prompt from request
  num = request.json.get("number")
  num = int(num)
  if num <= 0:
    num = 1
  if num > 50:
    num = 50
  prompt = request.json.get("prompt")
  output = []
  attempts = 0
  songs = []
  while len(songs) < 0.75*num and attempts < 5:
    songs = []
    messages=[{"role": "system", "content": "Create a playlist with " + str(num) + " songs that would fit the following description. Be creative with song selection but only include real songs. Create the playlist as a numbered list in the form 'song by artist'. Do not include any other information in your response."},
              {"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    # response = openai.Completion.create(model="gpt-4",prompt=prompt,temperature=0.7,max_tokens=256)
    # We need to standardize the output of the API in the future to make it easier to parse
    # For now, we'll break the output into a list of strings and then break each string into "song" and "artist" on the  - 
    # We'll then print the song and artist in a nice format
    output = response.choices[0].message.content
    output = output.split("\n")
    #Remove lines that are empty
    output = [x for x in output if x != '']
    for i in range(len(output)):
      if " - " in output[i]:
        output[i] = output[i].split(" - ")
      elif " by " in output[i]:
        output[i] = output[i].split(" by ")
      else:
        attempts += 1
        break
      print(output[i][0] + " by " + output[i][1])
      #Remove leading numbers
      while output[i][0][0].isdigit() or output[i][0][0] == ".":
        output[i][0] = output[i][0][2:]
      #Remove quotes from the song name
      output[i][0] = output[i][0].replace('"', "")
      #Remove apostrophes from the song name and artist name
      output[i][0] = output[i][0].replace("'", "")
      output[i][1] = output[i][1].replace("'", "")
      #Remove ft. and feat. from the artist name
      if " ft. " in output[i][1]:
        output[i][1] = output[i][1].split(" ft. ")[0]
      if " feat. " in output[i][1]:
        output[i][1] = output[i][1].split(" feat. ")[0]
    sp = spotipy.Spotify(auth_manager=auth_manger_client)
    for i in range(len(output)):
      results = sp.search(q="track:" + output[i][0] + " artist:" + output[i][1], limit=1)
      if len(results['tracks']['items']) > 0:
        song = results['tracks']['items'][0]
        artist = ""
        for art in song['artists']:
          artist += art['name'] + ", "
        artist = artist[:len(artist)-2]
        print(song)
        songs.append({"name": song['name'], "artist": artist, "album": song['album']['name'], "image": song['album']['images'][0]['url'], "link":song["external_urls"]["spotify"], "id": song['id']})
      else:
        output[i][0] = output[i][0][:len(output[i][0])//2]
        results = sp.search(q="track:" + output[i][0] + " artist:" + output[i][1], limit=1)
        if len(results['tracks']['items']) > 0:
          song = results['tracks']['items'][0]
          artist = ""
          for art in song['artists']:
            artist += art['name'] + ", "
          artist = artist[:len(artist)-2]
          print(song)
          songs.append({"name": song['name'], "artist": artist, "album": song['album']['name'], "image": song['album']['images'][0]['url'], "link":song["external_urls"]["spotify"], "id": song['id']})
    attempts += 1
    print(songs)
  return jsonify(songs)

@app.route("/playlist/save", methods=["POST"])
def save_playlist():
  prompt = request.json.get("prompt")
  name = request.json.get("name")
  songs = request.json.get("songs")
  print(songs)
  code = request.cookies.get('token')
  expires = request.cookies.get('expires_at')
  if not code or int(expires) < time.time():
    return Response(401, "Unauthorized")
  sp = spotipy.Spotify(auth=code)
  user = sp.current_user()
  playlist = sp.user_playlist_create(user['id'], name, public=True, description="Prompt: " + prompt)
  for song in songs:
    sp.user_playlist_add_tracks(user['id'], playlist['id'], [song['id']])
  return Response(200, "Playlist created successfully")

@app.route("/playlists")
def get_playlists():
  offset = 0
  code = request.cookies.get('token')
  expires = request.cookies.get('expires_at')
  if not code or int(expires) < time.time():
    return Response(401, "Unauthorized")
  sp = spotipy.Spotify(auth=code)
  user = sp.current_user()
  playlists = sp.current_user_playlists(offset=offset)
  return jsonify(playlists)

@app.route("/playlist/<playlist_id>/generate", methods=["POST"])
def extend_playlist(playlist_id):
  num = request.json.get("num")
  if num <= 0:
    num = 1
  if num > 50:
    num = 50
  code = request.cookies.get('token')
  expires = request.cookies.get('expires_at')
  if not code or int(expires) < time.time():
    return Response(401, "Unauthorized")
  sp = spotipy.Spotify(auth=code)
  user = sp.current_user()
  playlist = sp.playlist(playlist_id)
  prompt = "Playlist: " + playlist['name'] + "\n"
  i = 0
  for song in playlist['tracks']['items']:
    i += 1
    prompt += str(i) + ". " + song['track']['name'] + " by " + song['track']['artists'][0]['name'] + "\n" 
  output = []
  attempts = 0
  songs = []
  while len(songs) < 0.75*num and attempts < 5:
    songs = []
    messages=[{"role": "system", "content": "Add " + str(num) + " songs to the playlist. The songs should be similar to the songs in the playlist. The songs should be in the format: <Song Name> by <Artist Name>. The songs should be in a numbered list. Do not include any other information in your response"},
              {"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    output = response.choices[0].message.content
    output = output.split("\n")
    #Remove lines that are empty
    output = [x for x in output if x != '']
    for i in range(len(output)):
      if " - " in output[i]:
        output[i] = output[i].split(" - ")
      else:
        output[i] = output[i].split(" by ")
      print(output[i][0] + " by " + output[i][1])
      #Remove leading numbers
      while output[i][0][0].isdigit() or output[i][0][0] == ".":
        output[i][0] = output[i][0][2:]
      #Remove quotes from the song name
      output[i][0] = output[i][0].replace('"', "")
      #Remove apostrophes from the song name and artist name
      output[i][0] = output[i][0].replace("'", "")
      output[i][1] = output[i][1].replace("'", "")
      #Remove ft. and feat.
      if " ft. " in output[i][0]:
        output[i][0] = output[i][0].split(" ft. ")[0]
      if " feat. " in output[i][0]:
        output[i][0] = output[i][0].split(" feat. ")[0]
      #Remove leading and trailing whitespace
      output[i][0] = output[i][0].strip()
      output[i][1] = output[i][1].strip()
      #Search for the song
      results = sp.search(q="track:" + output[i][0] + " artist:" + output[i][1], limit=1)
      if len(results['tracks']['items']) > 0:
        song = results['tracks']['items'][0]
        artist = ""
        for art in song['artists']:
          artist += art['name'] + ", "
        artist = artist[:len(artist)-2]
        print(song)
        songs.append({"name": song['name'], "artist": artist, "album": song['album']['name'], "image": song['album']['images'][0]['url'], "link": song["external_urls"]["spotify"], "id": song['id']})
    attempts += 1
    print(songs)
  return jsonify(songs)

@app.route("/playlist/<playlist_id>/save", methods=["POST"])
def save_extend_playlist(playlist_id):
  songs = request.json.get("songs")
  print(songs)
  code = request.cookies.get('token')
  expires = request.cookies.get('expires_at')
  if not code or int(expires) < time.time():
    return Response(401, "Unauthorized")
  sp = spotipy.Spotify(auth=code)
  user = sp.current_user()
  for song in songs:
    sp.user_playlist_add_tracks(user['id'], playlist_id, [song['id']])
  return Response(200, "Playlist extended successfully")


@app.route("/Spotify_Logo_RGB_Green.png")
def get_spotify_logo():
  return send_file("Spotify_Logo_RGB_Green.png")

if __name__ == '__main__':
  app.run()