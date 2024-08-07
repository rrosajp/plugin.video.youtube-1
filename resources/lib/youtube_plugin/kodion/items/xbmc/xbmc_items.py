# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2018 plugin.video.youtube

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only for more information.
"""

from __future__ import absolute_import, division, unicode_literals

from json import dumps

from .. import AudioItem, DirectoryItem, ImageItem, VideoItem
from ...compatibility import to_str, xbmc, xbmcgui
from ...constants import (
    CHANNEL_ID,
    PLAYLISTITEM_ID,
    PLAYLIST_ID,
    PLAY_COUNT,
    PLAY_WITH,
    SUBSCRIPTION_ID,
    VIDEO_ID,
)
from ...utils import current_system_version, datetime_parser, redact_ip_from_url


def set_info(list_item, item, properties, set_play_count=True, resume=True):
    is_video = False
    if not current_system_version.compatible(20, 0):
        if isinstance(item, VideoItem):
            is_video = True
            info_labels = {}

            value = item.get_aired(as_info_label=True)
            if value is not None:
                info_labels['aired'] = value

            value = item.get_artists()
            if value is not None:
                info_labels['artist'] = value

            value = item.get_cast()
            if value is not None:
                info_labels['castandrole'] = [(member['name'], member['role'])
                                              for member in value]

            value = item.get_code()
            if value is not None:
                info_labels['code'] = value

            value = item.get_count()
            if value is not None:
                info_labels['count'] = value

            value = item.get_date(as_info_label=True)
            if value is not None:
                info_labels['date'] = value

            value = item.get_dateadded(as_info_label=True)
            if value is not None:
                info_labels['dateadded'] = value

            value = item.get_duration()
            if value is not None:
                info_labels['duration'] = value

            value = item.get_episode()
            if value is not None:
                info_labels['episode'] = value

            value = item.get_last_played(as_info_label=True)
            if value is not None:
                info_labels['lastplayed'] = value

            value = item.get_mediatype()
            if value is not None:
                info_labels['mediatype'] = value

            value = item.get_play_count()
            if value is not None:
                if set_play_count:
                    info_labels['playcount'] = value
                properties[PLAY_COUNT] = value

            value = item.get_plot()
            if value is not None:
                info_labels['plot'] = value

            value = item.get_premiered(as_info_label=True)
            if value is not None:
                info_labels['premiered'] = value

            value = item.get_rating()
            if value is not None:
                info_labels['rating'] = value

            value = item.get_season()
            if value is not None:
                info_labels['season'] = value

            value = item.get_title()
            if value is not None:
                info_labels['title'] = value

            value = item.get_track_number()
            if value is not None:
                info_labels['tracknumber'] = value

            value = item.get_year()
            if value is not None:
                info_labels['year'] = value

            value = item.get_studios()
            if value is not None:
                info_labels['studio'] = value

            if info_labels:
                list_item.setInfo('video', info_labels)

        elif isinstance(item, DirectoryItem):
            info_labels = {}

            value = item.get_name()
            if value is not None:
                info_labels['title'] = value

            value = item.get_plot()
            if value is not None:
                info_labels['plot'] = value

            if info_labels:
                list_item.setInfo('video', info_labels)

            if properties:
                list_item.setProperties(properties)
            return

        elif isinstance(item, AudioItem):
            info_labels = {}

            value = item.get_album_name()
            if value is not None:
                info_labels['album'] = value

            value = item.get_artists()
            if value is not None:
                info_labels['artist'] = value

            value = item.get_duration()
            if value is not None:
                info_labels['duration'] = value

            value = item.get_rating()
            if value is not None:
                info_labels['rating'] = value

            value = item.get_title()
            if value is not None:
                info_labels['title'] = value

            value = item.get_track_number()
            if value is not None:
                info_labels['tracknumber'] = value

            value = item.get_year()
            if value is not None:
                info_labels['year'] = value

            if info_labels:
                list_item.setInfo('music', info_labels)

        elif isinstance(item, ImageItem):
            value = item.get_title()
            if value is not None:
                list_item.setInfo('picture', {'title': value})

            if properties:
                list_item.setProperties(properties)
            return

        resume_time = resume and item.get_start_time()
        if resume_time:
            properties['ResumeTime'] = str(resume_time)
        duration = item.get_duration()
        if duration:
            properties['TotalTime'] = str(duration)
            if is_video:
                list_item.addStreamInfo('video', {'duration': duration})

        if properties:
            list_item.setProperties(properties)
        return

    value = item.get_date(as_info_label=True)
    if value is not None:
        list_item.setDateTime(value)

    info_tag = None

    if isinstance(item, VideoItem):
        is_video = True
        info_tag = list_item.getVideoInfoTag()

        value = item.get_aired(as_info_label=True)
        if value is not None:
            info_tag.setFirstAired(value)

        value = item.get_dateadded(as_info_label=True)
        if value is not None:
            info_tag.setDateAdded(value)

        value = item.get_last_played(as_info_label=True)
        if value is not None:
            info_tag.setLastPlayed(value)

        value = item.get_premiered(as_info_label=True)
        if value is not None:
            info_tag.setPremiered(value)

        # cast: list[xbmc.Actor]
        # From list[{member: str, role: str, order: int, thumbnail: str}]
        # Used as alias for channel name if enabled
        value = item.get_cast()
        if value is not None:
            info_tag.setCast([xbmc.Actor(**member) for member in value])

        # code: str
        # eg. "466K | 3.9K | 312"
        # Production code, currently used to store misc video data for label
        # formatting
        value = item.get_code()
        if value is not None:
            info_tag.setProductionCode(value)

        # count: int
        # eg. 12
        # Can be used to store an id for later, or for sorting purposes
        # Used for Youtube video view count
        value = item.get_count()
        if value is not None:
            list_item.setInfo('video', {'count': value})

        # director: list[str]
        # eg. "Steven Spielberg"
        # Currently unused
        # info_tag.setDirectors(item.get_directors())

        # episode: int
        value = item.get_episode()
        if value is not None:
            info_tag.setEpisode(value)

        # imdbnumber: str
        # eg. "tt3458353"
        # Currently unused
        # info_tag.setIMDBNumber(item.get_imdb_id())

        # mediatype: str
        value = item.get_mediatype()
        if value is not None:
            info_tag.setMediaType(value)

        # playcount: int
        value = item.get_play_count()
        if value is not None:
            if set_play_count:
                info_tag.setPlaycount(value)
            properties[PLAY_COUNT] = value

        # plot: str
        value = item.get_plot()
        if value is not None:
            info_tag.setPlot(value)

        # season: int
        value = item.get_season()
        if value is not None:
            info_tag.setSeason(value)

        # studio: list[str]
        # Used as alias for channel name if enabled
        value = item.get_studios()
        if value is not None:
            info_tag.setStudios(value)

    elif isinstance(item, DirectoryItem):
        info_tag = list_item.getVideoInfoTag()

        value = item.get_name()
        if value is not None:
            info_tag.setTitle(value)

        value = item.get_plot()
        if value is not None:
            info_tag.setPlot(value)

        if properties:
            list_item.setProperties(properties)
        return

    elif isinstance(item, ImageItem):
        info_tag = list_item.getPictureInfoTag()

        value = item.get_title()
        if value is not None:
            info_tag.setTitle(value)

        if properties:
            list_item.setProperties(properties)
        return

    elif isinstance(item, AudioItem):
        info_tag = list_item.getMusicInfoTag()

        # album: str
        # eg. "Buckle Up"
        value = item.get_album_name()
        if value is not None:
            info_tag.setAlbum(value)

    resume_time = resume and item.get_start_time()
    duration = item.get_duration()
    if resume_time and duration:
        info_tag.setResumePoint(resume_time, float(duration))
    elif resume_time:
        info_tag.setResumePoint(resume_time)
    if is_video and duration:
        info_tag.addVideoStream(xbmc.VideoStreamDetail(duration=duration))

    # artist: list[str]
    # eg. ["Angerfist"]
    # Used as alias for channel name
    value = item.get_artists()
    if value is not None:
        info_tag.setArtists(value)

    # duration: int
    # As seconds
    if duration is not None:
        info_tag.setDuration(duration)

    # genre: list[str]
    # eg. ["Hardcore"]
    # Currently unused
    # info_tag.setGenres(item.get_genres())

    # rating: float
    value = item.get_rating()
    if value is not None:
        info_tag.setRating(value)

    # title: str
    # eg. "Blow Your Head Off"
    value = item.get_title()
    if value is not None:
        info_tag.setTitle(value)

    # tracknumber: int
    # eg. 12
    value = item.get_track_number()
    if value is not None:
        info_tag.setTrackNumber(value)

    # year: int
    # eg. 1994
    value = item.get_year()
    if value is not None:
        info_tag.setYear(value)

    if properties:
        list_item.setProperties(properties)


def video_playback_item(context, video_item, show_fanart=None, **_kwargs):
    uri = video_item.get_uri()
    context.log_debug('Converting VideoItem |%s|' % redact_ip_from_url(uri))

    settings = context.get_settings()
    headers = video_item.get_headers()
    license_key = video_item.get_license_key()
    is_external = context.get_ui().get_property(PLAY_WITH)
    is_strm = context.get_param('strm')
    mime_type = None

    if is_strm:
        kwargs = {
            'path': uri,
            'offscreen': True,
        }
        props = {}
    else:
        kwargs = {
            'label': video_item.get_title() or video_item.get_name(),
            'label2': video_item.get_short_details(),
            'path': uri,
            'offscreen': True,
        }
        props = {
            'isPlayable': str(video_item.playable).lower(),
        }

    if video_item.use_isa_video() and context.use_inputstream_adaptive():
        if video_item.use_mpd_video():
            manifest_type = 'mpd'
            mime_type = 'application/dash+xml'
            if 'auto' in settings.stream_select():
                props['inputstream.adaptive.stream_selection_type'] = 'adaptive'
        else:
            manifest_type = 'hls'
            mime_type = 'application/x-mpegURL'

        inputstream_property = ('inputstream'
                                if current_system_version.compatible(19, 0) else
                                'inputstreamaddon')
        props[inputstream_property] = 'inputstream.adaptive'

        if current_system_version.compatible(21, 0):
            if video_item.live:
                props['inputstream.adaptive.manifest_config'] = dumps({
                    'timeshift_bufferlimit': 4 * 60 * 60,
                })
        else:
            props['inputstream.adaptive.manifest_type'] = manifest_type

        if headers:
            props['inputstream.adaptive.manifest_headers'] = headers
            props['inputstream.adaptive.stream_headers'] = headers

        if license_key:
            props['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            props['inputstream.adaptive.license_key'] = license_key

    else:
        if 'mime=' in uri:
            mime_type = uri.split('mime=', 1)[1].split('&', 1)[0]
            mime_type = mime_type.replace('%2F', '/')

        if (headers and uri.startswith('http')
                and not (is_external
                         or settings.default_player_web_urls())):
            kwargs['path'] = '|'.join((uri, headers))

    list_item = xbmcgui.ListItem(**kwargs)

    if mime_type or is_external:
        list_item.setContentLookup(False)
        list_item.setMimeType(mime_type or '*/*')

    if is_strm:
        list_item.setProperties(props)
        return list_item

    if show_fanart is None:
        show_fanart = settings.fanart_selection()
    image = video_item.get_image()
    art = {'icon': image}
    if image:
        art['thumb'] = image
    if show_fanart:
        art['fanart'] = video_item.get_fanart()
    list_item.setArt(art)

    if video_item.subtitles:
        list_item.setSubtitles(video_item.subtitles)

    resume = context.get_param('resume')
    set_info(list_item, video_item, props, resume=resume)

    return list_item


def audio_listitem(context,
                   audio_item,
                   show_fanart=None,
                   for_playback=False,
                   **_kwargs):
    uri = audio_item.get_uri()
    context.log_debug('Converting AudioItem |%s|' % uri)

    kwargs = {
        'label': audio_item.get_title() or audio_item.get_name(),
        'label2': audio_item.get_short_details(),
        'path': uri,
        'offscreen': True,
    }
    props = {
        'isPlayable': str(audio_item.playable).lower(),
        'ForceResolvePlugin': 'true',
    }

    list_item = xbmcgui.ListItem(**kwargs)

    if show_fanart is None:
        show_fanart = context.get_settings().fanart_selection()
    image = audio_item.get_image()
    art = {'icon': image}
    if image:
        art['thumb'] = image
    if show_fanart:
        art['fanart'] = audio_item.get_fanart()
    list_item.setArt(art)

    resume = context.get_param('resume') or not for_playback
    set_info(list_item, audio_item, props, resume=resume)

    context_menu = audio_item.get_context_menu()
    if context_menu:
        list_item.addContextMenuItems(context_menu)

    if for_playback:
        return list_item
    return uri, list_item, False


def directory_listitem(context, directory_item, show_fanart=None, **_kwargs):
    uri = directory_item.get_uri()
    context.log_debug('Converting DirectoryItem |%s|' % uri)

    kwargs = {
        'label': directory_item.get_name(),
        'path': uri,
        'offscreen': True,
    }
    props = {
        'ForceResolvePlugin': 'true',
    }

    if directory_item.next_page:
        props['specialSort'] = 'bottom'
    else:
        special_sort = 'top'

        prop_value = directory_item.get_subscription_id()
        if prop_value:
            special_sort = None
            props[SUBSCRIPTION_ID] = prop_value

        prop_value = directory_item.get_channel_id()
        if prop_value:
            special_sort = None
            props[CHANNEL_ID] = prop_value

        prop_value = directory_item.get_playlist_id()
        if prop_value:
            special_sort = None
            props[PLAYLIST_ID] = prop_value

        if special_sort:
            props['specialSort'] = special_sort

    list_item = xbmcgui.ListItem(**kwargs)

    if show_fanart is None:
        show_fanart = context.get_settings().fanart_selection()
    image = directory_item.get_image()
    art = {'icon': image}
    if image:
        art['thumb'] = image
    if show_fanart:
        art['fanart'] = directory_item.get_fanart()
    list_item.setArt(art)

    set_info(list_item, directory_item, props)

    """
    # ListItems that do not open a lower level list should have the isFolder
    # parameter of the xbmcplugin.addDirectoryItem set to False, however this
    # now appears to mark the ListItem as playable, even if the IsPlayable
    # property is not set or set to "false".
    # Set isFolder to True as a workaround, regardless of whether the ListItem
    # is actually a folder.
    is_folder = not directory_item.is_action()
    """
    is_folder = True

    context_menu = directory_item.get_context_menu()
    if context_menu is not None:
        list_item.addContextMenuItems(context_menu)

    return uri, list_item, is_folder


def image_listitem(context, image_item, show_fanart=None, **_kwargs):
    uri = image_item.get_uri()
    context.log_debug('Converting ImageItem |%s|' % uri)

    kwargs = {
        'label': image_item.get_name(),
        'path': uri,
        'offscreen': True,
    }
    props = {
        'isPlayable': str(image_item.playable).lower(),
        'ForceResolvePlugin': 'true',
    }

    list_item = xbmcgui.ListItem(**kwargs)

    if show_fanart is None:
        show_fanart = context.get_settings().fanart_selection()
    image = image_item.get_image()
    art = {'icon': image}
    if image:
        art['thumb'] = image
    if show_fanart:
        art['fanart'] = image_item.get_fanart()
    list_item.setArt(art)

    set_info(list_item, image_item, props)

    context_menu = image_item.get_context_menu()
    if context_menu is not None:
        list_item.addContextMenuItems(context_menu)

    return uri, list_item, False


def uri_listitem(context, uri_item, **_kwargs):
    uri = uri_item.get_uri()
    context.log_debug('Converting UriItem |%s|' % uri)

    kwargs = {
        'label': uri_item.get_name(),
        'path': uri,
        'offscreen': True,
    }
    props = {
        'isPlayable': str(uri_item.playable).lower(),
        'ForceResolvePlugin': 'true',
    }

    list_item = xbmcgui.ListItem(**kwargs)
    list_item.setProperties(props)
    return list_item


def video_listitem(context,
                   video_item,
                   show_fanart=None,
                   focused=None,
                   **_kwargs):
    uri = video_item.get_uri()
    context.log_debug('Converting VideoItem |%s|' % uri)

    kwargs = {
        'label': video_item.get_title() or video_item.get_name(),
        'label2': video_item.get_short_details(),
        'path': uri,
        'offscreen': True,
    }
    props = {
        'isPlayable': str(video_item.playable).lower(),
        'ForceResolvePlugin': 'true',
    }

    published_at = video_item.get_added_utc()
    scheduled_start = video_item.get_scheduled_start_utc()
    datetime = scheduled_start or published_at
    local_datetime = None
    if datetime:
        local_datetime = datetime_parser.utc_to_local(datetime)
        props['PublishedLocal'] = to_str(local_datetime)
    if video_item.live:
        props['PublishedSince'] = context.localize('live')
    elif local_datetime:
        props['PublishedSince'] = to_str(datetime_parser.datetime_to_since(
            context, local_datetime
        ))

    set_play_count = True
    resume = True
    prop_value = video_item.video_id
    if prop_value:
        if focused and focused == prop_value:
            set_play_count = False
            resume = False
        props[VIDEO_ID] = prop_value

    # make channel_id property available for keymapping
    prop_value = video_item.get_channel_id()
    if prop_value:
        props[CHANNEL_ID] = prop_value

    # make subscription_id property available for keymapping
    prop_value = video_item.get_subscription_id()
    if prop_value:
        props[SUBSCRIPTION_ID] = prop_value

    # make playlist_id property available for keymapping
    prop_value = video_item.get_playlist_id()
    if prop_value:
        props[PLAYLIST_ID] = prop_value

    # make playlist_item_id property available for keymapping
    prop_value = video_item.get_playlist_item_id()
    if prop_value:
        props[PLAYLISTITEM_ID] = prop_value

    list_item = xbmcgui.ListItem(**kwargs)

    if show_fanart is None:
        show_fanart = context.get_settings().fanart_selection()
    image = video_item.get_image()
    art = {'icon': image}
    if image:
        art['thumb'] = image
    if show_fanart:
        art['fanart'] = video_item.get_fanart()
    list_item.setArt(art)

    if video_item.subtitles:
        list_item.setSubtitles(video_item.subtitles)

    set_info(list_item,
             video_item,
             props,
             set_play_count=set_play_count,
             resume=resume)

    if not set_play_count:
        video_id = video_item.video_id
        playback_history = context.get_playback_history()
        playback_history.set_item(video_id, dict(
            playback_history.get_item(video_id) or {},
            play_count=int(not video_item.get_play_count()),
            played_time=0.0,
            played_percent=0,
        ))

    context_menu = video_item.get_context_menu()
    if context_menu:
        list_item.addContextMenuItems(context_menu)

    return uri, list_item, False
