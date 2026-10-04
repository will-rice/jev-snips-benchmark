"""Definitions of the SNIPS intents and slots, as shown to the model.

Each slot definition says what a single word must be to count as part of
that slot, because the model is asked about one word at a time. They were
written intent by intent from the label names and the training split: how
each slot's values look, which typical words fill it, and where SNIPS draws
the boundary (for example that the word playlist after a playlist name is
not part of the name). Each set was checked and revised against 200 training
utterances of its intent, then confirmed on other training utterances. No
test utterance was used.

Slots are keyed by intent because one slot name can mean different things
under different intents, and so is the none option, because what counts as
filler differs by intent.
"""

INTENT_DESCRIPTIONS = {
    "AddToPlaylist": ("Add music to one of the user's playlists."),
    "BookRestaurant": (
        "Reserve a table at a restaurant or other place to eat or drink."
    ),
    "GetWeather": ("Ask about the weather or a forecast for a place or time."),
    "PlayMusic": ("Play music, chosen by what it is or where it is streamed."),
    "RateBook": ("Give a rating to a book or other written work."),
    "SearchCreativeWork": ("Find a creative work by its title."),
    "SearchScreeningEvent": ("Find when or where movies are showing."),
}

SLOT_DESCRIPTIONS = {
    "AddToPlaylist": {
        "artist": (
            "A word of the name of the musician or band whose music is being added,"
            " often after by or before a generic word such as album or discography."
            " A person's or band's name, not the title of a song or album."
        ),
        "entity_name": (
            "A word of the title of the specific song, album or other work being "
            "added, which is what comes right after add or put. A title can be any "
            "phrase and often contains ordinary small words such as the, a, i, of, "
            "at, on and to; inside the title they belong to it."
        ),
        "music_item": (
            "The generic word for the kind of thing being added: song, track, tune,"
            " album or artist. Only that word itself. Not a word before it such as "
            "this or the, and not a word inside a title or a playlist's name."
        ),
        "playlist": (
            "A word of the name of the playlist being added to: the phrase after "
            "to, onto, into or in, and after the word the or an owner word. Names "
            "often contain ordinary small words such as this, is, of, to and in; "
            "inside the name they belong to it. The word the just before the name, "
            "and the word playlist or list just after it, are not part of it."
        ),
        "playlist_owner": (
            "A word saying whose playlist it is: my, your, or a person's name "
            "together with the s that follows it, as in lina s."
        ),
    },
    "BookRestaurant": {
        "city": ("A word of the name of the city or town where the restaurant is."),
        "country": (
            "A word of the name of the country where the restaurant is. Country "
            "names can have several words, with and, of or the inside, as in saint "
            "pierre and miquelon or hong kong."
        ),
        "cuisine": (
            "A word naming the style or national origin of the food, such as thai, "
            "tuscan or southeastern brazilian. Not a specific dish."
        ),
        "facility": (
            "A word naming an amenity the place should have, such as pool, parking,"
            " wifi, outdoor, spa or smoking room. Not the word facility or access."
        ),
        "party_size_description": (
            "A word of the phrase naming or describing the people in the party, as "
            "in me valarie and caroline or my daughters and i. The words and, me "
            "and i inside it belong to it. Not the words party or group."
        ),
        "party_size_number": (
            "The number of people in the party, as a digit or a word. Only the "
            "number, not the word people or party."
        ),
        "poi": (
            "A word of a landmark or a personal place that the restaurant should be"
            " near, as in your daughter s campus or our apartment. Owner words and "
            "the s after them belong to it. Not the name of a city or state."
        ),
        "restaurant_name": (
            "A word of the proper name of one specific restaurant. A leading the, "
            "and a word such as house, inn, tavern, bar or restaurant that is part "
            "of the name, belong to it."
        ),
        "restaurant_type": (
            "A word of the generic kind of place wanted, with no proper name: "
            "restaurant, bar, pub, cafe, diner, bistro, bakery, tea house, food "
            "court, taverna or brasserie. Not the vague words place or somewhere."
        ),
        "served_dish": (
            "A word naming a specific food or dish the place should serve, such as "
            "sushi, burgers or pot\u00e9e. Not a style of cooking."
        ),
        "sort": (
            "A word of a ranking preference for which place to pick: best, top-"
            "rated, highly rated or popular."
        ),
        "spatial_relation": (
            "A word saying how near or far the place should be: near, close, far, "
            "faraway, distant, not far, within walking distance, or within the same"
            " area, where the and same belong to it. Not the word from or as that "
            "follows it, and not the place it is measured from."
        ),
        "state": (
            "A word of the name of the state or territory where the restaurant is, "
            "in full or abbreviated, such as michigan, nc, puerto rico or american "
            "samoa."
        ),
        "timeRange": (
            "A word of the date or time of the reservation, as in in 21 hours, 17 "
            "weeks from now, january the twentieth or nine am. A leading in before "
            "a length of time, the words from now, and the inside a date belong to "
            "it. The words on and at before a date or time, and the phrase meal "
            "time, do not."
        ),
    },
    "GetWeather": {
        "city": ("A word of the name of the city or town the forecast is for."),
        "condition_description": (
            "A word naming the weather condition asked about, other than "
            "temperature: rain, snow, snowstorm, cloudy, sunny, humid, foggy, "
            "windy, hail, blizzard or storm. Not the words weather, forecast, "
            "coverage or speed."
        ),
        "condition_temperature": (
            "A word describing how hot or cold it will be: hot, warm, cold, chilly,"
            " freezing, temperate, hotter, warmer or colder. Not the words "
            "temperature or temps."
        ),
        "country": (
            "A word of the name of the country or island territory the forecast is "
            "for. Names can have several words, with and, of or the inside, as in "
            "saint pierre and miquelon or sint maarten."
        ),
        "current_location": (
            "A word of a phrase meaning where the user is now: here, current "
            "location, current position, current spot or current place. Not the "
            "word my before it."
        ),
        "geographic_poi": (
            "A word of the name of a park, forest, reserve, wilderness or other "
            "natural or protected area, including words such as national park or "
            "state park in the name."
        ),
        "spatial_relation": (
            "A word of a phrase saying how near or far from a place is meant: near,"
            " close by, nearby, far, within walking distance, around, or in the "
            "same area as. Every word of the phrase belongs to it, including in, "
            "the and same."
        ),
        "state": (
            "A word of the name of the state the forecast is for, in full or as an "
            "abbreviation such as ct, dc or la."
        ),
        "timeRange": (
            "A word of the date or time the forecast is for, as in in 8 years, six "
            "weeks from now, 23 minutes and fourteen seconds, on the 5th of may or "
            "now. Every word of the expression belongs to it, including a leading "
            "in before a length of time, from now, and and, the, of or a inside it."
            " Not the question word when."
        ),
    },
    "PlayMusic": {
        "album": (
            "A word of the title of an album to play, including small words inside "
            "the title such as the, of, in and and. Prefer this over track when the"
            " utterance calls the work an album, record or ep."
        ),
        "artist": ("A word of the name of the musician or band to play."),
        "genre": (
            "A word naming a style of music, such as rock, jazz, acid punk or "
            "oldies. Not a word for a kind of piece such as ballad, symphony or "
            "chant."
        ),
        "music_item": (
            "A singular word for a kind of musical piece, used instead of a title: "
            "song, track, tune, album, record, ep, soundtrack, symphony, ballad, "
            "chant, movement, melody or theme. Not the general words music, songs, "
            "tunes, something or anything."
        ),
        "playlist": (
            "A word of the name of a playlist to play, including small words inside"
            " the name. The word playlist that follows the name is not part of it."
        ),
        "service": (
            "A word of the name of the streaming service or app to play on, such as"
            " deezer, youtube, pandora, groove shark or google music. The word "
            "music belongs to it only when it is part of the service's name. Not "
            "the word on before it."
        ),
        "sort": (
            "A word of a ranking or recency preference: top, top five, top-ten, top"
            " 20, best, greatest, most popular, newest, latest or last, including "
            "the number after top. Not the words sort, sorted, by or charting."
        ),
        "track": (
            "A word of the title of a song to play, including small words inside "
            "the title such as to, the, in and be. A title with no word saying what"
            " kind of work it is is usually a track."
        ),
        "year": (
            "A word giving the year or decade the music is from, such as 1997, "
            "2012, fifties or nineties. Not the word the or from before it."
        ),
    },
    "RateBook": {
        "best_rating": (
            "The number the rating is out of, the top of the scale. It is the "
            "number that comes right after out of, of or a slash, as the 6 in four "
            "out of 6 or 2 of 6."
        ),
        "object_name": (
            "A word of the title of the work being rated. A title can be any phrase"
            " and often contains ordinary small words such as the, of, a, and, "
            "about, from and with; inside the title, and at its start, they belong "
            "to it."
        ),
        "object_part_of_series_type": (
            "The word series, saga or chronicle, saying the work is part of a "
            "series. It follows a title or a word such as this or current."
        ),
        "object_select": (
            "A word that points to the work by its position instead of naming it: "
            "current, last, next, previous or following, and the word this when it "
            "stands directly before the kind of work, as in this book. In this "
            "current book only current counts and this is not selected. Not the "
            "words it or my."
        ),
        "object_type": (
            "The generic word for the kind of single work being rated: book, novel,"
            " essay, textbook or album. Not series, saga or chronicle, and not a "
            "word inside a title."
        ),
        "rating_unit": ("The unit the rating is counted in: stars or points."),
        "rating_value": (
            "The rating given: the number of stars or points awarded, as a digit or"
            " a word, including zero. It comes before out of. Not the number after "
            "out of."
        ),
    },
    "SearchCreativeWork": {
        "object_name": (
            "A word of the title of the work to find. A title can be any phrase, "
            "even a whole sentence, and often contains ordinary small words such as"
            " the, of, a, in, to, for, i, me and my; inside the title they belong "
            "to it. The word the right before a kind of work, as in the novel or "
            "the trailer of, is not part of the title."
        ),
        "object_type": (
            "A word of the generic kind of work wanted: book, novel, song, album, "
            "soundtrack, movie, show, tv show, tv series, television show, saga, "
            "game, video game, picture, photograph, painting or trailer. Usually "
            "next to called, named or titled, or just before or after the title. "
            "Not the general words work, creative work or creativity."
        ),
    },
    "SearchScreeningEvent": {
        "location_name": (
            "A word of the name of a specific cinema or cinema chain, including a "
            "word such as theatres, theaters, cinemas, cineplex or company that is "
            "part of the name, as in harkins theatres."
        ),
        "movie_name": (
            "A word of the title of a specific movie. A title can be any phrase and"
            " often contains ordinary small words such as the, a, of, in, to, from "
            "and with; inside the title they belong to it."
        ),
        "movie_type": (
            "A generic word for films when no title is given: movies, films, film, "
            "or animated movies. The word movie only when it stands alone, not in "
            "movie schedule, movie times, movie theatre or movie house."
        ),
        "object_location_type": (
            "A word of a generic phrase for a place that shows films, with no "
            "proper name: cinema, theatre, movie theatre or movie house. The word "
            "movie in movie theatre and movie house belongs here."
        ),
        "object_type": (
            "A word of the phrase for the listing being asked for: schedule, "
            "schedules, movie schedule, movie schedules, movie times or showtimes. "
            "The word movie in those phrases belongs here. Not the word time in "
            "what time, and not movie on its own."
        ),
        "spatial_relation": (
            "A word of a phrase saying how near the place should be: nearest, "
            "closest, nearby, close by, around here, in the neighbourhood or in the"
            " area. The words in and the in those phrases belong here."
        ),
        "timeRange": (
            "A word of the stated time of the showing, such as four o clock, "
            "tonight, from now or in one hour, including a leading in. Not the "
            "question words what time or when, and not today or right now."
        ),
    },
}

NONE_DESCRIPTIONS = {
    "AddToPlaylist": (
        "A word of the request itself and not of any name or title: the command "
        "(add, put, i want, needs), a linking word (to, onto, into, in, by, from, "
        "with), the or this before a generic word, please, and the word playlist or"
        " list after a playlist's name."
    ),
    "BookRestaurant": (
        "A word of the request itself and not of any name, place, time or "
        "description: the command (book, reserve, i want, i need, table, "
        "reservation, spot), a linking word (for, at, in, a, that serves, with, and"
        " between two separate details), and the word people or party after a "
        "number."
    ),
    "GetWeather": (
        "A word of the request itself and not of any place, time or condition: the "
        "question (what is, will it be, is it going to, tell me, when), the words "
        "weather, forecast and temperature, a linking word (in, for, at, on, the, "
        "a) that stands before a place name, and my before a location."
    ),
    "PlayMusic": (
        "A word of the request itself and not of any name or title: the command "
        "(play, i want to hear, open), general words for music (music, songs, "
        "tunes, something, some, any), a linking word (by, from, on, the, and), and"
        " the word playlist after a playlist's name."
    ),
    "RateBook": (
        "A word of the request itself and not of any title or number: the command "
        "(rate, give, i would give, mark, i liked), a linking word (out of, of, a, "
        "to, with, is worth, a value of, and a best rating of), and it, my or the "
        "before a generic word."
    ),
    "SearchCreativeWork": (
        "A word of the request itself and not of the title: the command (find, "
        "show, show me, look up, search for, i want, can you, help me, where can i,"
        " get, locate, play), the before a kind of work, the words called, named "
        "and titled, and the general words work, creative work and creativity."
    ),
    "SearchScreeningEvent": (
        "A word of the request itself and not of any name, title, place or time: "
        "the command (find, show me, give me, i want to see, is, are), question "
        "words (what, when, what time), a linking word (at, for, the, a, playing, "
        "showing), and words such as listings or showtimes."
    ),
}
