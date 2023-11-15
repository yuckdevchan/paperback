import sys, gi, requests, tempfile, subprocess
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from PIL import Image
from io import BytesIO
from main import load_artists, load_artist_albums, load_album_songs, get_cover, ping_server
from config import PROGRAM_NAME, PROGRAM_SLOGAN, PROGRAM_VERSION, SERVER
from main import play_song


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title(f"{PROGRAM_NAME} {PROGRAM_VERSION} - {PROGRAM_SLOGAN}")
        self.set_default_size(800, 600)
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b'''
            .colorful-button {
                background-color: #00ff00;
                color: #ffffff;
                /* Add any other styles you want */
            }
        ''')

        # Create a Gtk.Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(275)
        self.set_child(self.stack)

        # Create a ScrolledWindow for the list of artists
        scrolled_window = Gtk.ScrolledWindow()
        self.stack.add_named(scrolled_window, "artists_list")

        # Create a Box to hold the buttons
        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_window.set_child(self.box1)
        server_up = ping_server()
        if server_up:
            artists_list = load_artists()
            for artist in artists_list:
                artist_name = artist["name"]
                if artist_name.startswith("."):
                    if artist_name.endswith(".sonic"):
                        plugin_name = artist_name.split(".")[1]
                        print(f"Found {plugin_name} Plugin!")
                        button = Gtk.Button(label=plugin_name)
                        self.box1.append(button)
                        button.connect('clicked', self.on_button_clicked, artist_name)
                else:
                    button = Gtk.Button(label=artist_name)
                    self.box1.append(button)
                    button.connect('clicked', self.on_button_clicked, artist_name)
        else:
            print("Server is down")
            button = Gtk.Button(label="Server is Down")
            self.box1.append(button)
            button.connect('clicked', self.on_button_clicked, "Server is Down")

        # Create a Box for the artist details page
        self.artist_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled_artist_window = Gtk.ScrolledWindow()
        scrolled_artist_window.set_child(self.artist_details_box)
        # self.stack.add_named(scrolled_artist_window, "artist_details")

        # Create a Gtk.Box for the song listing page
        self.song_listing_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Create a new scrolled window
        scrolled_window = Gtk.ScrolledWindow()

        # Add the song_listing_box to the scrolled_window
        scrolled_window.set_child(self.song_listing_box)

        # Add the scrolled_window to the stack
        self.stack.add_named(scrolled_window, "song_listing")

        # Create a back button for the song listing page
        back_button = Gtk.Button(label="Back")
        self.song_listing_box.append(back_button)
        back_button.connect('clicked', self.on_back_button_clicked)

    def on_button_clicked(self, button, artist_name):
        # Create a new Gtk.Box for the artist details page
        new_artist_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        back_button = Gtk.Button(label=f"Back to Artists")
        new_artist_details_box.append(back_button)
        back_button.connect('clicked', self.on_back_to_artists_clicked)

        albums_list = load_artist_albums(artist_name)
        for album in albums_list:
            album_name = album["name"]
            print(f"Found {album_name}")
            if album_name.startswith("."):
                pass
            else:
                button = Gtk.Button(label=album_name)
                new_artist_details_box.append(button)
                button.connect('clicked', self.on_album_clicked, artist_name, album_name)

        # Remove the old artist details page from the stack
        if self.artist_details_box is not None:
            self.stack.remove(self.artist_details_box)

        # Add the new artist details page to the stack
        self.stack.add_named(new_artist_details_box, "artist_details")

        # Update the reference to the artist details box
        self.artist_details_box = new_artist_details_box

        # Switch to the artist details page
        self.stack.set_visible_child_name("artist_details")
        
    def on_album_clicked(self, button, artist_name, album_name):
        # Remove all children of the song_listing_box
        for child in list(self.song_listing_box):
            self.song_listing_box.remove(child)
        
        # Add the back button to the song_listing_box
        if artist_name.startswith(".") and artist_name.endswith(".sonic"):
            back_to_albums_label = f"Back to {artist_name.split('.')[1]}'s Categories"
        else:
            back_to_albums_label = f"Back to {artist_name}'s Albums"
        back_button = Gtk.Button(label=back_to_albums_label)
        self.song_listing_box.append(back_button)
        back_button.connect('clicked', self.on_back_to_albums_clicked)
        
        cover = get_cover(artist_name, album_name)
        if cover is not None:
            image = Image.open(BytesIO(cover))
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_file)
        else:
            print("Cover is None")
            image = Gtk.Image.new_from_icon_name("media-playback-start")
        
        # Add the songs to the song_listing_box
        songs = load_album_songs(artist_name, album_name)
        song_queue = []
        for song in songs:
            song_name = song["name"]
            song_path = song["path"]
            if song_name.startswith(".") or song_path.endswith(".jpg") or song_path.endswith(".png"):
                pass
            else:
                song_queue.append(song_path)
                # Create a new button
                button = Gtk.Button()

                # Create a new box
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                
                # Create a new label and set its text
                label = Gtk.Label()
                label.set_text(song_name)

                if cover is not None:
                    image = Gtk.Picture.new_for_filename(temp_file.name)
                else:
                    image = Gtk.Image.new_from_icon_name("media-playback-start")
                    
                
                # Add the image and the label to the box
                box.append(image)
                box.append(label)

                # Set the box as the child of the button
                button.set_child(box)

                # Add the button to the song_listing_box
                self.song_listing_box.append(button)

                # Connect the button to a handler function
                button.connect('clicked', self.on_song_clicked, artist_name, album_name, song_path, song_queue)
        # Switch to the song listing page
        self.stack.set_visible_child_name("song_listing")
                
    def on_song_clicked(self, button, artist_name, album_name, song_path, song_queue):
        play_song(artist_name, album_name, song_path, song_queue)

    def on_back_button_clicked(self, button):
        # Switch back to the artist details page
        self.stack.set_visible_child_name("artist_details")

    def on_back_to_albums_clicked(self, button):
        # Switch back to the artist details page
        self.stack.set_visible_child_name("artist_details")
        
    def on_back_to_artists_clicked(self, button):
        # Switch back to the artist list page
        self.stack.set_visible_child_name("artists_list")

    def __del__(self):
        # Stop mplayer
        subprocess.run("killall mplayer", shell=True)
        print("killed mplayer")

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

app = MyApp(application_id="io.davros.sonic")
app.run(sys.argv)