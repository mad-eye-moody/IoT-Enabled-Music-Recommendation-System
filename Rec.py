# Establish connection with Spotify's API



import streamlit as st
import time
import json
import requests             #HTTP requests (getting url, data, etc.)
import pandas as pd

st.title("Music Recommendation System")
text = "Here's introducing the first-of-its-kind music recommendation system that recommends playlists not only based on your digital activity but also on your physical whereabouts! Feel the pulse!"

def stream_data():
  for word in text.split():
    yield word + " "
    time.sleep(0.07)

st.write_stream(stream_data)


#IDs from Spotify Developer Dashboard
CLIENT_ID = '5ee273d90d6e4e59ab58bba4f6404dde'
CLIENT_SECRET = 'c098389d7bca435f82e852a54e012ede'
REDIRECT_URI= 'https://iot-enabled-music-recommendation-system.streamlit.app/'

# Spotify API endpoints
BASE_URL = 'https://api.spotify.com/v1'
TOKEN_ENDPOINT = '/api/token'
LIKED_SONGS_ENDPOINT = '/me/tracks'

# Authorization URL for the user to grant access to their Spotify account
SCOPES = ['user-top-read', 'playlist-modify-private', 'playlist-modify-public']
AUTHORIZATION_URL = ( 'https://accounts.spotify.com/authorize?client_id=' + CLIENT_ID + '&response_type=code&redirect_uri=' + REDIRECT_URI + '&scope=' + "%20".join(SCOPES))

# Print the authorization URL for the user to visit
st.link_button("Please authorize the app", AUTHORIZATION_URL, help = "We need your permission to access your Spotify data")
authorization_code = st.text_input("Authorization code:", help="Required to authorize the app", placeholder="You can find it appended in the url as a paramater", label_visibility="visible")

# Get the authorization code from the user after they grant access
if authorization_code is not None:
    st.write("Authorization successful!")
    st.balloons()
else:
    st.write("Authorization not found. Please authorize the app first.")

AUTH_URL = 'https://accounts.spotify.com/api/token'

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'authorization_code',
    'code': authorization_code,
    'redirect_uri': REDIRECT_URI,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})
st.write(auth_response.content)
# convert the response to JSON
auth_response_data = auth_response.json()
headers = {'Authorization': 'Bearer {token}'.format(token=auth_response_data['access_token'])}

"""# Get user's top 50 tracks"""

#Getting top 50 tracks
response = requests.get( BASE_URL + '/me/top/tracks?limit=50&offset=0&time_range=short_term' , headers=headers)
top_tracks = response.json()

# Extract the 'items' list from the dictionary
items_list = top_tracks.get('items', [])

# Flatten the data and create a DataFrame
flattened_data = [{'track_name': item['name'],
                   'track_id': item['id'],
                   'artist_name': item['artists'][0]['name'],
                   'album_name': item['album']['name'],
                   'duration': item['duration_ms'],
                   'popularity': item['popularity'],
                   'uri': item['uri'],
                   'artist_uri': item['artists'][0]['uri'],
                   'artist_id': item['artists'][0]['id'],
                   }
                  for item in items_list]

df_t = pd.DataFrame(flattened_data)

"""# Get user's top 5 artists"""

#getting top 5 artists
response = requests.get(BASE_URL + '/me/top/artists?limit=5&time_range=short_term', headers=headers)
top_artists = response.json()
top_artists = response.json()

# Extract the 'items' list from the dictionary
items_list = top_artists.get('items', [])

# Flatten the data and create a DataFrame
flattened_data = [{'artist_name': item['name'],
                   'artist_popularity': item['popularity'],
                   'artist_id': item['id'],
                   'genres': item['genres']
                   }
                  for item in items_list]

df_a = pd.DataFrame(flattened_data)

# Print the DataFrame

"""# Get Audio Features"""

# create blank dictionary to store audio features
feature_dict = {}

# convert track_uri column to an iterable list
track_ids = df_t['track_id'].to_list()

# loop through track URIs and pull audio features using the API,
# store all these in a dictionary
for track_id in track_ids:

  feature_dict[track_id] = {'danceability': 0,
                         'energy': 0,
                         'speechiness': 0,
                         'instrumentalness': 0,
                         'tempo': 0,
                         'loudness': 0,
                         'valence': 0,
                         'acousticness': 0}

  j = requests.get(BASE_URL + '/audio-features/' + track_id, headers=headers)
  j = j.json()

  feature_dict[track_id]['danceability'] = j['danceability']
  feature_dict[track_id]['energy'] = j['energy']
  feature_dict[track_id]['speechiness'] = j['speechiness']
  feature_dict[track_id]['instrumentalness'] = j['instrumentalness']
  feature_dict[track_id]['tempo'] = j['tempo']
  feature_dict[track_id]['loudness'] = j['loudness']
  feature_dict[track_id]['valence'] = j['valence']
  feature_dict[track_id]['acousticness'] = j['acousticness']

# convert dictionary into dataframe with track_uri as the first column
df_features = pd.DataFrame.from_dict(feature_dict, orient='index')
df_features.insert(0, 'track_id', df_features.index)
df_features.reset_index(inplace=True, drop=True)

user_music = pd.merge(df_t, df_features, on='track_id', how='outer')

"""# Part 3: Loading the Fitbit Datasets
* Load the dataset
* Select a random cell from the dataset
"""


#user_input = input("Are you heading to sleep?")
#index = 'sleep' if (user_input.lower() == 'yes') else 'other'

user_input = st.text_input("Are you heading to sleep?", help="This information will help us generate a better playlist for you", placeholder="Please answer in yes or no", label_visibility="visible")
index = 'sleep' if (user_input.lower() == 'yes') else 'other'

import numpy as np

if not index == 'sleep':
  Fitbit = pd.read_csv('minuteIntensitiesWide_merged.csv')
  intensities = Fitbit.iloc[1:, 2:]  # Exclude first row and first two columns
  # Generate random indices for row and column
  random_row_index = np.random.randint(0, len(intensities))             # Generate random row index
  random_column_index = np.random.randint(0, len(intensities.columns))  # Generate random column index
  random_cell_value = intensities.iloc[random_row_index, random_column_index]

  while random_cell_value == 0:
    random_row_index = np.random.randint(0, len(intensities))             # Generate new random row index
    random_column_index = np.random.randint(0, len(intensities.columns))  # Generate new random column index
    random_cell_value = intensities.iloc[random_row_index, random_column_index]

  index = random_cell_value
  prev= intensities.iloc[random_row_index-1, random_column_index-1]
  if prev == random_cell_value-1:
    index = 'cooldown'

  Time = Fitbit.iloc[random_row_index+1,1]
  ID= Fitbit.iloc[random_row_index+1,0]


  info = "The current intensity of your physical activity is" + index
  body = "Here are your current details: "
  date_and_time = "The current date and time is" + Time


  st.header(body, divider='rainbow')
  st.header(info)
  st.caption(date_and_time)

# Criteria for audio features based on intensity levels
criteria = {
    1: {
        'danceability': (0.4, 0.6),
        'energy': (0.0, 0.2),
        'acousticness': (0.8, 0.1),
        'valence': (0.2, 0.4),
        'instrumentalness': (0.4, 0.6),
        'desc': ("move around at a light intensity. Your heart rate and breathing are slightly elevated. Our guess is, you're probably enaging in yoga, light Stretching, or maybe just walking! Then again, this is just a statistical deduction and not a precise represention of reality :)" )
        },
    2: {
        'danceability': (0.6, 0.8),
        'energy': (0.6, 0.8),
        'acousticness': (0.0, 0.2),
        'valence': (0.4, 0.6),
        'instrumentalness': (0.2, 0.4),
        'desc': ( "move around at a moderate intensity. Your heart rate and breathing are noticeably elevated. Our guess is, you're probably enaging in aerobics, pilates or maybe just jogging! Then again, this is just a statistical deduction and not a precise represention of reality :)")
    },
    3: {
        'danceability': (0.6, 0.8),
        'energy': (0.8, 1.0),
        'acousticness': (0.0, 0.2),
        'valence': (0.4, 0.6),
        'instrumentalness': (0.0, 0.2),
        'desc': ("move around at a high intensity. Your heart rate and breathing are significantly elevated. Our guess is, you're probably enaging in HIIT workouts, competitive sports or maybe just moving around vigourously! Then again, this is just a statistical deduction and not a precise represention of reality :)")
        },
    'cooldown': {
        'danceability': (0.4, 0.6),
        'energy': (0.2, 0.4),
        'acousticness': (0.6, 0.8),
        'valence': (0.2, 0.4),
        'instrumentalness': (0.2, 0.4),
        'desc': ("cool down after a higher intensity activity, to bring your heart rate and breathing back to the pre-exercise state. Our guess is, you're probably stretching, practicing deep breathing, or simply slowing down the pace and intensity of your activity. Then again, this is just an algorithm's statistical deduction and not a precise represention of reality :)")
        },
    'sleep': {
        'danceability': (0.0, 0.2),
        'energy': (0.0, 0.2),
        'acousticness': (0.8, 1.0),
        'valence': (0.0, 0.2),
        'instrumentalness': (0.8, 0.1),
        'desc': ("head to sleep. These tunes are custom picked to promote relaxation and lull you into a deep slumber. Then again, this is just an algorithm's statistical deduction and not a precise represention of reality :)")
        }
}

# Get criteria for audio features based on intensity level
audio_feature_criteria = criteria[index]

"""# Get Spotify's Recommendations"""

#Ask for Spotify's Recommendations based on top 5 artists.

TOP_ARTISTS = df_a['artist_id'].to_list()
seed_artists = ','.join(TOP_ARTISTS)

params = {'limit': 20,
          'seed_artists': seed_artists,
          'target_acousticness': (audio_feature_criteria['acousticness'][0] + audio_feature_criteria['acousticness'][1]) / 2,
          'target_danceability': (audio_feature_criteria['danceability'][0] + audio_feature_criteria['danceability'][1]) / 2,
          'target_energy': (audio_feature_criteria['energy'][0] + audio_feature_criteria['energy'][1]) / 2,
          'target_instrumentalness': (audio_feature_criteria['instrumentalness'][0] + audio_feature_criteria['instrumentalness'][1]) / 2,
          'target_valence': (audio_feature_criteria['valence'][0] + audio_feature_criteria['valence'][1]) / 2}

response = requests.get(BASE_URL + '/recommendations?', params=params, headers=headers)
recommendations = response.json()

tracks = recommendations.get('tracks', [])

# Extracting relevant information from each track
track_data = []
for track in tracks:
    track_info = {
        'track_name': track['name'],
        'artist_name': ', '.join([artist['name'] for artist in track['artists']]),
        'album_name': track['album']['name'],
        'release_date': track['album']['release_date'],
        'track_id': track['id'],
        'uri': track['uri']
    }
    track_data.append(track_info)

# Creating DataFrame
recommendations_df = pd.DataFrame(track_data)

"""# Part 4: Get Recommended Playlist
* Define a function to obtain the final playlist
"""

# Get User ID (Required to create a playlist for the user)
Response = requests.get(BASE_URL + '/me', headers=headers)
profile_data = Response.json()
user_id = profile_data['id']

#Create a playlist for the user

data = {
     "name": 'Your Personalized Playlist',
     "public": True,
     "description": "Enjoy these beats as you " + criteria[Intensity]['desc']}

RESP = requests.post(BASE_URL + '/users/' + user_id +'/playlists' , headers=headers, json=data)

RESP = RESP.json()
playlist_id = RESP['id']

def get_playlist(criteria, user_music):
    # Initialize an empty list to store selected songs
    playlist = []

    # Iterate over criteria for each intensity level
    for intensity, audio_feature_criteria in criteria.items():
      # Filter user_music DataFrame based on the criteria for each intensity level
      filtered_music = user_music[
            ((user_music['danceability'] >= audio_feature_criteria['danceability'][0]) &
            (user_music['danceability'] <= audio_feature_criteria['danceability'][1])) &
            ((user_music['energy'] >= audio_feature_criteria['energy'][0]) &
            (user_music['energy'] <= audio_feature_criteria['energy'][1])) &
            ((user_music['valence'] >= audio_feature_criteria['valence'][0]) &
            (user_music['valence'] <= audio_feature_criteria['valence'][1])) &
            ((user_music['instrumentalness'] >= audio_feature_criteria['instrumentalness'][0]) &
            (user_music['instrumentalness'] <= audio_feature_criteria['instrumentalness'][1])) &
            ((user_music['acousticness'] >= audio_feature_criteria['acousticness'][0]) &
            (user_music['acousticness'] <= audio_feature_criteria['acousticness'][1]))
            ]

      selected_songs = filtered_music.sample(min(5, len(filtered_music)))
      playlist.extend(selected_songs[['track_name', 'uri', 'track_id']].to_dict('records'))

      # If needed, add more songs from recommendations_df, avoiding duplicates
      if len(playlist) < 10:
            remaining = 10 - len(playlist)
            available = recommendations_df[~recommendations_df['uri'].isin(playlist)]
            additional_songs = available.sample(remaining)
            playlist.extend(additional_songs[['track_name', 'uri', 'track_id']].to_dict('records'))

    # Ensure a maximum of 10 songs
    playlist = playlist[:10]

    track_uris = [track['uri'] for track in playlist]
    uris = ','.join(track_uris)
    data_last = {"uris": track_uris}

    #Add these songs to the playlist
    put_songs = requests.post(BASE_URL + '/playlists/' + playlist_id + '/tracks' , headers=headers, json=data_last)
    return playlist_id

playlist = get_playlist(criteria, user_music)
#Display the output
print("Here's your Playlist!")
print( data['description'] )
print('https://open.spotify.com/playlist/' + playlist_id)

playlist = get_playlist(criteria, user_music)
link = 'https://open.spotify.com/playlist/' + playlist_id

st.header("Here's your Playlist!", divider='rainbow')
st.caption(data['description'])
st.link_button("Find your playlist here", link, help="This link will lead you out of this app")
