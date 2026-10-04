"""What each slot is, as questions about its value, for the docs' patterns.

The shape of the spec in the Jev function-calling cookbook. For every slot of
every intent: `definition` says in one sentence what the value is, `question`
asks for it, and `stated` asks whether the utterance gives one at all. The
questions are written about the idea, not the slot's name.
"""

SLOT_SPEC = {
    "AddToPlaylist": {
        "artist": {
            "definition": (
                "The name of the musician or band whose music is being added."
            ),
            "question": "Which musician or band's music does the user want added?",
            "stated": "Does the user name a musician or band?",
        },
        "entity_name": {
            "definition": "The title of the specific work being added.",
            "question": (
                "What is the title of the specific song, album, or other work the"
                " user wants added?"
            ),
            "stated": (
                "Does the user give the title of a specific work to add, rather "
                "than only a generic word for it?"
            ),
        },
        "music_item": {
            "definition": (
                "The generic word for the kind of thing being added, used instead"
                " of a title."
            ),
            "question": (
                "Which generic word does the user use for the kind of thing to "
                "add, in place of a title?"
            ),
            "stated": (
                "Does the user refer to what to add by a generic word for its "
                "kind, rather than only by title or artist?"
            ),
        },
        "playlist": {
            "definition": "The name of the playlist to add to.",
            "question": "What is the name of the playlist the user wants to add to?",
            "stated": "Does the user name the playlist to add to?",
        },
        "playlist_owner": {
            "definition": "The word or name saying whose playlist it is.",
            "question": "Which word or name says whose playlist it is?",
            "stated": "Does the user say whose playlist it is?",
        },
    },
    "BookRestaurant": {
        "city": {
            "definition": "The city or town where the restaurant is.",
            "question": "Which city or town should the restaurant be in?",
            "stated": (
                "Does the user name a city or town, as opposed to a state or a country?"
            ),
        },
        "country": {
            "definition": "The country where the restaurant is.",
            "question": "Which country should the restaurant be in?",
            "stated": "Does the user name a country, as opposed to a city or a state?",
        },
        "cuisine": {
            "definition": "The style or national origin of the food.",
            "question": "Which style or national origin of food does the user want?",
            "stated": (
                "Does the user name a style of cooking, as opposed to a specific dish?"
            ),
        },
        "facility": {
            "definition": "An amenity the place should have.",
            "question": "Which amenity should the place have?",
            "stated": "Does the user ask for an amenity at the place?",
        },
        "party_size_description": {
            "definition": (
                "The people in the party, named or described instead of counted."
            ),
            "question": "Which words name or describe the people in the party?",
            "stated": (
                "Does the user say who is coming by naming or describing people, "
                "rather than giving a count?"
            ),
        },
        "party_size_number": {
            "definition": "The number of people in the party.",
            "question": "How many people is the booking for?",
            "stated": "Does the user give a count of people?",
        },
        "poi": {
            "definition": (
                "A landmark or personal place that the restaurant should be near."
            ),
            "question": (
                "Which landmark or personal place should the restaurant be near?"
            ),
            "stated": (
                "Does the user mention a landmark or someone's place that the "
                "restaurant should be near?"
            ),
        },
        "restaurant_name": {
            "definition": "The proper name of a specific restaurant.",
            "question": "What is the proper name of the specific restaurant?",
            "stated": "Does the user name a specific restaurant by its proper name?",
        },
        "restaurant_type": {
            "definition": "The generic kind of eating or drinking establishment.",
            "question": (
                "Which generic kind of eating or drinking place does the user want?"
            ),
            "stated": (
                "Does the user say what kind of establishment they want, in "
                "generic words?"
            ),
        },
        "served_dish": {
            "definition": "A specific food or dish the place should serve.",
            "question": "Which specific food or dish should the place serve?",
            "stated": (
                "Does the user name a specific food or dish, as opposed to a "
                "style of cooking?"
            ),
        },
        "sort": {
            "definition": "A ranking preference for which restaurant to pick.",
            "question": "Which word says how the user wants the options ranked?",
            "stated": "Does the user ask for the best, top, or most popular option?",
        },
        "spatial_relation": {
            "definition": (
                "Words expressing distance or position relative to another place."
            ),
            "question": (
                "Which words say how near or far the place should be from somewhere?"
            ),
            "stated": (
                "Does the user express distance or position relative to another place?"
            ),
        },
        "state": {
            "definition": (
                "The state or region where the restaurant is, as a full name or "
                "abbreviation."
            ),
            "question": "Which state or region should the restaurant be in?",
            "stated": (
                "Does the user name a state or region, in full or abbreviated, as"
                " opposed to a city or a country?"
            ),
        },
        "timeRange": {
            "definition": "The date or time of the reservation.",
            "question": "What date or time is the reservation for?",
            "stated": "Does the user say when the reservation is for?",
        },
    },
    "GetWeather": {
        "city": {
            "definition": "The city or town the forecast is for.",
            "question": "Which city or town does the user want the weather for?",
            "stated": (
                "Does the user name a city or town, as opposed to a state or a country?"
            ),
        },
        "condition_description": {
            "definition": (
                "The weather condition being asked about, other than temperature."
            ),
            "question": (
                "Which weather condition, other than temperature, is the user "
                "asking about?"
            ),
            "stated": (
                "Does the user ask about a specific weather condition other than "
                "temperature?"
            ),
        },
        "condition_temperature": {
            "definition": "The temperature quality being asked about.",
            "question": "Which word about temperature is the user asking about?",
            "stated": "Does the user ask about how hot or cold it will be?",
        },
        "country": {
            "definition": "The country the forecast is for.",
            "question": "Which country does the user want the weather for?",
            "stated": "Does the user name a country, as opposed to a city or a state?",
        },
        "current_location": {
            "definition": "Words meaning the user's present location.",
            "question": "Which words refer to where the user is right now?",
            "stated": "Does the user refer to their own present location?",
        },
        "geographic_poi": {
            "definition": (
                "The name of a park, reserve, or other natural or protected area."
            ),
            "question": (
                "Which park, reserve, or other natural area does the user want "
                "the weather for?"
            ),
            "stated": (
                "Does the user name a park, reserve, or other natural or "
                "protected area?"
            ),
        },
        "spatial_relation": {
            "definition": (
                "Words expressing distance or position relative to another place."
            ),
            "question": "Which words say how near or far from a place the user means?",
            "stated": "Does the user express distance or position relative to a place?",
        },
        "state": {
            "definition": (
                "The state or region the forecast is for, as a full name or "
                "abbreviation."
            ),
            "question": "Which state or region does the user want the weather for?",
            "stated": (
                "Does the user name a state or region, in full or abbreviated, as"
                " opposed to a city or a country?"
            ),
        },
        "timeRange": {
            "definition": "The date or time the forecast is for.",
            "question": "What date or time does the user want the weather for?",
            "stated": "Does the user say when they want the weather for?",
        },
    },
    "PlayMusic": {
        "album": {
            "definition": "The title of the album to play.",
            "question": "What is the title of the album the user wants to hear?",
            "stated": (
                "Does the user give the title of an album, as opposed to a single song?"
            ),
        },
        "artist": {
            "definition": "The name of the musician or band to play.",
            "question": "Which musician or band does the user want to hear?",
            "stated": "Does the user name a musician or band?",
        },
        "genre": {
            "definition": "The musical genre or style to play.",
            "question": "Which musical genre or style does the user want to hear?",
            "stated": "Does the user name a genre or style of music?",
        },
        "music_item": {
            "definition": (
                "The generic word for the kind of thing to play, used instead of "
                "a title."
            ),
            "question": (
                "Which generic word does the user use for the kind of thing to "
                "play, in place of a title?"
            ),
            "stated": (
                "Does the user refer to what to play by a generic word for its kind?"
            ),
        },
        "playlist": {
            "definition": "The name of the playlist to play.",
            "question": "What is the name of the playlist the user wants to hear?",
            "stated": "Does the user name a playlist?",
        },
        "service": {
            "definition": "The streaming service or app to play the music on.",
            "question": "Which streaming service or app should play the music?",
            "stated": "Does the user name a streaming service or app?",
        },
        "sort": {
            "definition": "A ranking or recency preference for which music to pick.",
            "question": "Which words say which music to pick by ranking or recency?",
            "stated": "Does the user ask for the top, best, newest, or similar?",
        },
        "track": {
            "definition": "The title of the song to play.",
            "question": "What is the title of the song the user wants to hear?",
            "stated": (
                "Does the user give the title of a single song, as opposed to an album?"
            ),
        },
        "year": {
            "definition": "The year or decade the music is from.",
            "question": "Which year or decade should the music be from?",
            "stated": "Does the user give a year or decade?",
        },
    },
    "RateBook": {
        "best_rating": {
            "definition": (
                "The top of the rating scale: the number the rating is out of."
            ),
            "question": "What number is the rating out of?",
            "stated": "Does the user say what the rating is out of?",
        },
        "object_name": {
            "definition": "The title of the work being rated.",
            "question": "What is the title of the work being rated?",
            "stated": (
                "Does the user give the title of the work, rather than pointing "
                "to it with a word like a pronoun?"
            ),
        },
        "object_part_of_series_type": {
            "definition": "The word for the kind of series the work belongs to.",
            "question": "Which word names the kind of series the work belongs to?",
            "stated": "Does the user mention that the work is part of a series?",
        },
        "object_select": {
            "definition": (
                "The word that picks out which work is meant by its position, "
                "used instead of a title."
            ),
            "question": (
                "Which word points to the work by its position, in place of a title?"
            ),
            "stated": (
                "Does the user point to the work with a word about which one it "
                "is, rather than by title?"
            ),
        },
        "object_type": {
            "definition": "The generic kind of work being rated.",
            "question": "Which generic kind of work is being rated?",
            "stated": "Does the user say what kind of work it is, in a generic word?",
        },
        "rating_unit": {
            "definition": "The unit the rating is counted in.",
            "question": "Which unit is the rating counted in?",
            "stated": "Does the user name the unit of the rating?",
        },
        "rating_value": {
            "definition": "The rating given: the number of units awarded.",
            "question": "What rating does the user give?",
            "stated": "Does the user give a rating as a number?",
        },
    },
    "SearchCreativeWork": {
        "object_name": {
            "definition": "The title of the work to find.",
            "question": "What is the title of the work the user is looking for?",
            "stated": "Does the user give the title of a work?",
        },
        "object_type": {
            "definition": "The generic kind of work to find.",
            "question": "Which generic kind of work is the user looking for?",
            "stated": "Does the user say what kind of work it is, in a generic word?",
        },
    },
    "SearchScreeningEvent": {
        "location_name": {
            "definition": "The name of the cinema or cinema chain.",
            "question": "What is the name of the cinema or cinema chain?",
            "stated": "Does the user name a specific cinema or chain?",
        },
        "movie_name": {
            "definition": "The title of the specific movie.",
            "question": "What is the title of the movie the user is asking about?",
            "stated": "Does the user give the title of a specific movie?",
        },
        "movie_type": {
            "definition": (
                "The generic word for the kind of film, used when no title is given."
            ),
            "question": (
                "Which generic word does the user use for the kind of film, in "
                "place of a title?"
            ),
            "stated": "Does the user refer to films generically, rather than by title?",
        },
        "object_location_type": {
            "definition": "The generic word for a place that shows films.",
            "question": (
                "Which generic word does the user use for a place that shows films?"
            ),
            "stated": (
                "Does the user refer to a kind of venue generically, rather than "
                "by name?"
            ),
        },
        "object_type": {
            "definition": "The word for the listing of showtimes being asked for.",
            "question": "Which word does the user use for the listing of showtimes?",
            "stated": "Does the user ask for a schedule or showtimes?",
        },
        "spatial_relation": {
            "definition": "Words expressing nearness to the user.",
            "question": "Which words say how near the user wants it to be?",
            "stated": "Does the user ask for somewhere near them?",
        },
        "timeRange": {
            "definition": "The date or time of the showing.",
            "question": "What date or time does the user want showings for?",
            "stated": "Does the user say when they want to see it?",
        },
    },
}
