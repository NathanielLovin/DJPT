import React from "react";

function SelectOption(props) {
	return <option value={props.value}>{props.value}</option>;
}

function DropdownForm(props) {
  console.log(props.data)
  console.log(props.value)
	return <form id={props.id}>
		<select value={props.value} onChange={props.onChangeFunction}>
			{props.data.map((dataelement) => dataelement.name).map((name) => <SelectOption key={name} value={name} />)}
		</select>
	</form>;
}

function song_display(props) {
  const song = props.song;
  return (
    <div class="song">
      <img src={song.image} class="album-art" height={"100px"} />
      <p class="song-name">{song.name}</p>
      <p class="artist-name">{song.artist}</p>
      <p class="album-name">{song.album}</p>
      <p class="song-link"><a href={song.link}>Play on Spotify</a></p>
      <button onClick={() => props.remove(song)} class="remove-button">&times;</button>
    </div>
  );
}

function Footer(props){
  return (
    <div class="footer">
      <p>Created by <a href="https://www.twitter.com/thelovinator">Nathaniel Lovin</a>. <a href="/privacy">Privacy</a>.</p>
      <p>Song information via Spotify API.</p>
      <img src="/Spotify_Logo_RGB_Green.png" height={"70px"} href="https://spotify.com" />
    </div>
  );
}

export default class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      create: true,
      number: 10,
      prompt: "",
      songs: [],
      name: "",
      loggedIn: false,
      playlists: [],
      selectedPlaylist: "",
      loading: false
    };
  }

  componentDidMount() {
    fetch("/logged_in")
      .then(response => response.json())
      .then(data => {
        console.log(data)
        this.setState({loggedIn: data}, this.getPlaylists);
      }
    );
  }
  handleNumberChange = event => {
    this.setState({ number: event.target.value });
  };

  handlePromptChange = event => {
    this.setState({ prompt: event.target.value });
  };

  handleClick = () => {
    this.setState({ loading: true})
    fetch("/playlist/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        number: this.state.number,
        prompt: this.state.prompt
      })
    })
      .then(response => response.json())
      .then(data => {
        console.log(data)
        this.setState({ songs: data, loading: false });
      });
  };

  handleSave = () => {
    fetch("/playlist/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: this.state.prompt,
        name: this.state.name,
        songs: this.state.songs
      })
    })
      .then(response => {
        if (response.status === 401) {
          alert("You must be logged in to save a playlist");
        }
      })
  };

  handleLogin = () => {
    // Redirect to Spotify login
    fetch("/sign_in").
      then(response => response.json()).
      then(data => { 
        console.log(data)
        window.location.href = data.url;
      }
    );
  };

  handleLogout = () => {
    fetch("/sign_out")
      .then(response => {
        if (response.status !== 200) {
          alert("Error logging out");
        }
        else{
          this.setState({loggedIn: false, playlists: [], selectedPlaylist: "", songs: []});
        }
      }
    );
  };

  getPlaylists = () => {
    if (!this.state.loggedIn) {
      return;
    }
    fetch("/playlists")
      .then(response => response.json())
      .then(data => {
        console.log(data.items)
        console.log(data.items[0])
        this.setState({playlists: data.items, selectedPlaylist: data.items[0]}, console.log(this.state.selectedPlaylist));
      }
    );
  };

  extendPlaylist = () => {
    fetch("/playlist/" + this.state.selectedPlaylist.id + "/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        num: this.state.number,
      })
    })
      .then(response => response.json())
      .then(data => {
        console.log(data)
        this.setState({ songs: data });
      });
  };

  handlePlaylistChange = event => {
    console.log(event.target.value);
    console.log(this.state.playlists.find(e => e.name === event.target.value));
    this.setState({ selectedPlaylist: this.state.playlists.find(e => e.name === event.target.value)});
  };

  handleSaveExtend = () => {
    fetch("/playlist/" + this.state.selectedPlaylist.id + "/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        songs: this.state.songs
      })
    })
      .then(response => {
        if (response.status === 401) {
          alert("You must be logged in to save a playlist");
        }
      })
  };

  removeSong = (song) => {
    console.log(song);
    this.setState({songs: this.state.songs.filter(e => e !== song)});
  };

  render() {
    // If privacy policy, render that
    if(window.location.pathname === "/privacy") {
      return (
        <div class="main">
          <h1>DJPT</h1>
          <h2>Privacy Policy</h2>
          <p>DJPT does not collect any personal information. The only information that is collected is your Spotify username and the playlists you create or extend. Your Spotify username is used to identify you when you log in and to save your playlists. Your playlists are saved to your Spotify account. The only information that is sent to the server is the prompt you enter and the number of songs you want to generate. This information is used to generate the playlist. The generated playlist is not saved on the server. The generated playlist is sent to your Spotify account when you save it. If you choose to extend a playlist, the songs on that playlist will be sent to OpenAI as part of the prompt.</p>
        </div>
      )
    }
    if(this.state.create) {
      return (
        <div class="main">
          <h1>DJPT</h1>
          <button onClick={() => this.setState({create: false, songs: []}, this.getPlaylists)}>Extend a Playlist</button>
          {this.state.loggedIn ? <button onClick={this.handleLogout}>Logout</button> : <button onClick={this.handleLogin}>Login to Spotify</button>}
          <h2>Create a Spotify Playlist using GPT-3</h2>
          <p>Example:<i>Odes to New York</i></p>
          <p>Example:<i>Songs for a Progress Studies Party</i></p>
          <p>Approximate Number of Songs: <input type="number" value={this.state.number} onChange={this.handleNumberChange} min="1" max="50"/></p>
          <p>Prompt:</p>
          <p><textarea rows="4" cols="50" value={this.state.prompt} onChange={this.handlePromptChange} /></p>
          <button onClick={this.handleClick}>Get Playlist</button>
          {this.state.loading && <p>Loading...</p>}
          {this.state.songs !== [] && <div class="songs">
            {this.state.songs.map(song => (
              song_display({ song: song, remove: this.removeSong})
            ))}
          </div>}
          <p>Playlist Name:</p><p><input type="text" value={this.state.name} onChange={event => this.setState({ name: event.target.value })} /></p>
          <button onClick={this.handleSave}>Save Playlist</button>
          <Footer /> 
        </div>
      );
    }
    else {
      return (
        <div class="main">
          <h1>DJPT</h1>
          <button onClick={() => this.setState({create: true, songs: [], selectedPlaylist: ""})}>Create a Playlist</button>
          {this.state.loggedIn ? <button onClick={this.handleLogout}>Logout</button> : <button onClick={this.handleLogin}>Login to Spotify</button>}
          <h2>Extend a Spotify Playlist using GPT-3</h2>
          <DropdownForm id="playlist-dropdown" value={this.state.selectedPlaylist.name} onChangeFunction={this.handlePlaylistChange} data={this.state.playlists} />
          <button onClick={this.extendPlaylist}>Get Playlist </button>
          {this.state.songs !== [] && <div class="songs">
            {this.state.songs.map(song => (
              song_display({ song: song, remove: this.removeSong})
            ))}
          </div>}
          <button onClick={this.handleSaveExtend}>Add Songs to Playlist</button>
          <Footer /> 
        </div>
      );
    }
  }
}