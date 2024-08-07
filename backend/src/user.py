from __future__ import annotations
from . import database
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import spotipy
import threading

@dataclass
class Playlist():
    id: str
    user_id: int
    name: str
    image_url: str
    tracks_url: str
    track_count: int
    public_: bool
    owner: str
    type: str
    last_updated: datetime
    enabled: bool
    
    def as_dict(self):
        sd = asdict(self)
        sd['last_updated'] = str(sd['last_updated'])
        return sd

@dataclass
class Artist():
    user_id: int
    name: str
    tracks: int
    last_updated: datetime
    enabled: bool

    def as_dict(self):
        sd = asdict(self)
        sd['last_updated'] = str(sd['last_updated'])
        return sd

@dataclass
class User():
    id: str
    name: str
    email: str
    photo_url: str
    _api: spotipy.client.Spotify

    def __post_init__(self):
        if not database.get_user(user_id=self.id):
            database.insert_user(user_id=self.id, email=self.email)
        
        self._artist_thread = None
    
    def get_settings(self):
        return dict(**database.get_user(user_id=self.id))

    def update_settings(self, **kwargs):
        database.update_user(user_id=self.id, kwargs=kwargs)

    def as_dict(self):
        sd = asdict(self)
        sd.pop("_api")
        sd["playlists"] = self.get_latest_playlists_update()
        sd["artists"] = self.get_latest_artists_update()
        return sd

    def get_playlists(self) -> list[Playlist]:
        if database.get_latest_playlist_update(user_id=self.id) < (datetime.utcnow() - timedelta(days=1)):
            self.refresh_playlists()

        return [Playlist(**playlist) for playlist in database.get_playlists(user_id=self.id)]

    def get_playlist(self, id: str) -> Playlist:
        return Playlist(**database.get_playlist(user_id=self.id, id=id))
    
    def toggle_playlist(self, id: str, value: bool):
        database.update_playlist(user_id=self.id, id=id, kwargs={'enabled': value})
    
    def toggle_artist(self, name: str, value: bool):
        database.update_artist(user_id=self.id, name=name, kwargs={'enabled': value})

    def refresh_playlists(self):
        # return # TODO: REMOVE
        response = self._api.current_user_playlists()

        if not response:
            return
        playlists = list()
        playlists.extend(response['items'])
    
        while len(playlists) != response['total']:
            response = self._api.current_user_playlists(offset=len(playlists))
            if not response:
                return
            playlists.extend(response['items'])
        
        try:
            playlists.append({
                "id": "0",
                "images": [{"url":'https://misc.scdn.co/liked-songs/liked-songs-64.png'}],
                "tracks": {"total": self._api.current_user_saved_tracks()['total'], "href": ""},
                "name": 'Liked Songs',
                "public": False,
                "owner": {"display_name": self.name},
                "type": "Saved Songs"
            })
        except Exception as ex:
            print("Failed to add personal playlist")

        for playlist in playlists:
            if not playlist:
                continue

            try:
                image_url = playlist['images'][0]['url']
            except:
                image_url = ''

            if database.get_playlist(user_id=self.id, id=playlist['id']):
                database.update_playlist(
                    user_id=self.id,
                    id=playlist['id'],
                    kwargs={
                        'image_url':  image_url,
                        'track_count': playlist['tracks']['total'],
                    }
                )
                continue

            database.insert_playlist(
                user_id=self.id,
                id=playlist['id'],
                name=playlist['name'],
                image_url=image_url,
                tracks_url=playlist['tracks']['href'],
                count=playlist['tracks']['total'],
                public=playlist['public'],
                owner=playlist['owner']['display_name'],
                type=playlist['type'],
                enabled=False
            )
        
        database.update_playlist_time(user_id=self.id)
        
    def get_latest_artists_update(self):
        return database.get_latest_artists_update(self.id).strftime('%H:%M %A %d, %B %Y')

    def get_latest_playlists_update(self):
        return database.get_latest_playlist_update(self.id).strftime('%H:%M %A %d, %B %Y')

    def get_enabled_artists(self, fresh: bool=False) -> list[Artist]:
        return [Artist(**row) for row in self._get_enabled_artists(fresh=fresh)]

    def _get_enabled_artists(self, fresh: bool=False):
        existing_artists = database.get_artists(user_id=self.id)

        if fresh or len(existing_artists) == 0:
            self.queue_artist_refresh(block=True)

            existing_artists = database.get_artists(user_id=self.id)

        elif database.get_latest_artists_update(user_id=self.id) < (datetime.utcnow() - timedelta(minutes=5)):
            self.queue_artist_refresh()
        
        return existing_artists

    def queue_artist_refresh(self, block: bool=False):
        if self._artist_thread is None or (isinstance(self._artist_thread, threading.Thread) and (not self._artist_thread.is_alive())):
            self._artist_thread =  threading.Thread(target=self._get_fresh_enabled_artists, daemon=True)
            self._artist_thread.start()
        
        if block:
            self._artist_thread.join()

    def _get_fresh_enabled_artists(self):
        print("Starting fresh artists")
        existing_artists = database.get_artists(user_id=self.id)
        playlists = [p for p in self.get_playlists() if p.enabled]

        class ArtistCounter:
            def __init__(self):
                self.counts = dict()
            
            def add(self, artist: str):
                if artist in ("", None):
                    return

                self.counts[artist] = self.counts.get(artist, 0) + 1
            
            def update(self, other: ArtistCounter):
                for artist, count in other.counts.items():
                    self.counts[artist] = self.counts.get(artist, 0) + count
            
            def set(self):
                return set(self.counts)
            
            def subset(self, sub: set) -> dict:
                return {k:v for k,v in self.counts.items() if k in sub}

        def get_playlist_artists(playlist_id: str) -> set[str]:
            if playlist_id == "0":
                ret_method = lambda playlist_id, fields, offset, limit: self._api.current_user_saved_tracks(offset=offset, limit=limit)
            else:
                ret_method = self._api.playlist_items

            items = list()

            items_in = True

            while items_in:
                items_in = ret_method(playlist_id=playlist_id, fields='items(track(artists(name)))', offset=len(items), limit=50)

                if not items_in or not items_in['items']:
                    break

                items.extend(items_in['items'])

            artists = ArtistCounter()

            for item in items:
                try:
                    for artist in item['track']['artists']:
                        artists.add(artist['name'])
                except:
                    pass
            
            return artists

        artists = ArtistCounter()

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = [pool.submit(get_playlist_artists, p.id) for p in playlists]

        for result in results:
            artists.update(result.result())

        existings = {artist['name'] for artist in existing_artists}

        artists_set = artists.set()
        to_add = artists_set.difference(existings)
        to_update = artists_set.intersection(existings)
        to_delete = existings.difference(artists_set)

        for artist, tracks in artists.subset(to_add).items():
            database.insert_artist(user_id=self.id, name=artist, tracks=tracks, enabled=True)

        for artist, tracks in artists.subset(to_update).items():
            database.update_artist(user_id=self.id, name=artist, kwargs={'tracks':tracks})

        for artist in to_delete:
            database.delete_artist(user_id=self.id, name=artist)

        database.update_artist_time(user_id=self.id)
        
        print("Finishing fresh artists")
        
    
    def set_event_notification(self, event_id: str, **kwargs):
        database.set_event_notification(user_id=self.id, event_id=event_id, **kwargs)

    def get_artist_events(self, artist: str) -> list[dict]:
        events = [dict(**row) for row in database.get_artist_events(user_id=self.id, artist=artist)]
        for event in events:
            for key in list(event.keys()):
                if isinstance(event[key], datetime):
                    event[key] = str(event[key])
        
        return events
    
    def get_country_enabled_events(self) -> list[dict]:
        return database.get_user_country_specific_enabled_events(user_id=self.id)
