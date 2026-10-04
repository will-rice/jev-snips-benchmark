"""One-sentence definitions of the SNIPS intents and slots.

Written from the label names and the train split only. They define what a
label means and give no example values, so the condition stays zero-shot.
Slots are keyed by intent because one slot name can mean different things
under different intents.
"""

INTENT_DESCRIPTIONS = {
    "AddToPlaylist": "Add music to one of the user's playlists.",
    "BookRestaurant": "Reserve a table at a restaurant or other place to eat or drink.",
    "GetWeather": "Ask about the weather or a forecast for a place or time.",
    "PlayMusic": "Play music, chosen by what it is or where it is streamed.",
    "RateBook": "Give a rating to a book or other written work.",
    "SearchCreativeWork": "Find a creative work by its title.",
    "SearchScreeningEvent": "Find when or where movies are showing.",
}

SLOT_DESCRIPTIONS = {
    "AddToPlaylist": {
        "artist": "The name of the musician or band whose music is being added.",
        "entity_name": "The title of the specific work being added.",
        "music_item": (
            "The generic word for the kind of thing being added, used instead "
            "of a title."
        ),
        "playlist": "The name of the playlist to add to.",
        "playlist_owner": "The word or name saying whose playlist it is.",
    },
    "BookRestaurant": {
        "city": "The city or town where the restaurant is.",
        "country": "The country where the restaurant is.",
        "cuisine": "The style or national origin of the food.",
        "facility": "An amenity the place should have.",
        "party_size_description": (
            "The people in the party, named or described instead of counted."
        ),
        "party_size_number": "The number of people in the party.",
        "poi": "A landmark or personal place that the restaurant should be near.",
        "restaurant_name": "The proper name of a specific restaurant.",
        "restaurant_type": "The generic kind of eating or drinking establishment.",
        "served_dish": "A specific food or dish the place should serve.",
        "sort": "A ranking preference for which restaurant to pick.",
        "spatial_relation": (
            "Words expressing distance or position relative to another place."
        ),
        "state": (
            "The state or region where the restaurant is, as a full name or "
            "abbreviation."
        ),
        "timeRange": "The date or time of the reservation.",
    },
    "GetWeather": {
        "city": "The city or town the forecast is for.",
        "condition_description": (
            "The weather condition being asked about, other than temperature."
        ),
        "condition_temperature": "The temperature quality being asked about.",
        "country": "The country the forecast is for.",
        "current_location": "Words meaning the user's present location.",
        "geographic_poi": (
            "The name of a park, reserve, or other natural or protected area."
        ),
        "spatial_relation": (
            "Words expressing distance or position relative to another place."
        ),
        "state": (
            "The state or region the forecast is for, as a full name or abbreviation."
        ),
        "timeRange": "The date or time the forecast is for.",
    },
    "PlayMusic": {
        "album": "The title of the album to play.",
        "artist": "The name of the musician or band to play.",
        "genre": "The musical genre or style to play.",
        "music_item": (
            "The generic word for the kind of thing to play, used instead of a title."
        ),
        "playlist": "The name of the playlist to play.",
        "service": "The streaming service or app to play the music on.",
        "sort": "A ranking or recency preference for which music to pick.",
        "track": "The title of the song to play.",
        "year": "The year or decade the music is from.",
    },
    "RateBook": {
        "best_rating": "The top of the rating scale: the number the rating is out of.",
        "object_name": "The title of the work being rated.",
        "object_part_of_series_type": (
            "The word for the kind of series the work belongs to."
        ),
        "object_select": (
            "The word that picks out which work is meant by its position, used "
            "instead of a title."
        ),
        "object_type": "The generic kind of work being rated.",
        "rating_unit": "The unit the rating is counted in.",
        "rating_value": "The rating given: the number of units awarded.",
    },
    "SearchCreativeWork": {
        "object_name": "The title of the work to find.",
        "object_type": "The generic kind of work to find.",
    },
    "SearchScreeningEvent": {
        "location_name": "The name of the cinema or cinema chain.",
        "movie_name": "The title of the specific movie.",
        "movie_type": (
            "The generic word for the kind of film, used when no title is given."
        ),
        "object_location_type": "The generic word for a place that shows films.",
        "object_type": "The word for the listing of showtimes being asked for.",
        "spatial_relation": "Words expressing nearness to the user.",
        "timeRange": "The date or time of the showing.",
    },
}
