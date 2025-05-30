# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2018 plugin.video.youtube

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only for more information.
"""

from __future__ import absolute_import, division, unicode_literals

import sys

from ..constants import SETTINGS
from ..utils import (
    current_system_version,
    get_kodi_setting_bool,
    get_kodi_setting_value,
)
from ..network.http_server import validate_ip_address


class AbstractSettings(object):
    _vars = vars()
    for name, value in SETTINGS.__dict__.items():
        _vars[name] = value
    del _vars

    _echo = False
    _cache = {}
    _check_set = True

    @classmethod
    def flush(cls, xbmc_addon):
        raise NotImplementedError()

    def get_bool(self, setting, default=None, echo=None):
        raise NotImplementedError()

    def set_bool(self, setting, value, echo=None):
        raise NotImplementedError()

    def get_int(self, setting, default=-1, converter=None, echo=None):
        raise NotImplementedError()

    def set_int(self, setting, value, echo=None):
        raise NotImplementedError()

    def get_string(self, setting, default='', echo=None):
        raise NotImplementedError()

    def set_string(self, setting, value, echo=None):
        raise NotImplementedError()

    def get_string_list(self, setting, default=None, echo=None):
        raise NotImplementedError()

    def set_string_list(self, setting, value, echo=None):
        raise NotImplementedError()

    def open_settings(self):
        raise NotImplementedError()

    def items_per_page(self, value=None):
        if value is not None:
            return self.set_int(SETTINGS.ITEMS_PER_PAGE, value)
        return self.get_int(SETTINGS.ITEMS_PER_PAGE, 50)

    _VIDEO_QUALITY_MAP = {
        0: 240,
        1: 360,
        2: 480,  # 576 seems not to work well
        3: 720,
        4: 1080,
    }

    def fixed_video_quality(self, value=None):
        default = 3
        if value is None:
            _value = self.get_int(SETTINGS.VIDEO_QUALITY, default)
        else:
            _value = value
        if _value not in self._VIDEO_QUALITY_MAP:
            _value = default
        if value is not None:
            self.set_int(SETTINGS.VIDEO_QUALITY, _value)
        return self._VIDEO_QUALITY_MAP[_value]

    def ask_for_video_quality(self):
        if self.use_mpd_videos():
            return self.get_int(SETTINGS.MPD_STREAM_SELECT) == 4
        return self.get_bool(SETTINGS.VIDEO_QUALITY_ASK, False)

    def fanart_selection(self):
        return self.get_int(SETTINGS.FANART_SELECTION, 2)

    def cache_size(self, value=None):
        if value is not None:
            return self.set_int(SETTINGS.CACHE_SIZE, value)
        return self.get_int(SETTINGS.CACHE_SIZE, 20)

    def get_search_history_size(self):
        return self.get_int(SETTINGS.SEARCH_SIZE, 10)

    def setup_wizard_enabled(self, value=None):
        # Set run_required to release date (as Unix timestamp in seconds)
        # to enable oneshot on first run
        # Tuesday, 8 April 2025 12:00:00 AM = 1744070400
        run_required = 1744070400

        if value is False:
            self.set_int(SETTINGS.SETUP_WIZARD_RUNS, run_required)
            return self.set_bool(SETTINGS.SETUP_WIZARD, False)
        if value is True:
            self.set_int(SETTINGS.SETUP_WIZARD_RUNS, 0)
            return self.set_bool(SETTINGS.SETUP_WIZARD, True)

        last_run = self.get_int(SETTINGS.SETUP_WIZARD_RUNS, 0)
        if last_run < run_required:
            self.set_int(SETTINGS.SETUP_WIZARD_RUNS, run_required)
            self.set_bool(SETTINGS.SETTINGS_END, True)
            return run_required
        return self.get_bool(SETTINGS.SETUP_WIZARD, False)

    def support_alternative_player(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.SUPPORT_ALTERNATIVE_PLAYER, value)
        return self.get_bool(SETTINGS.SUPPORT_ALTERNATIVE_PLAYER, False)

    def default_player_web_urls(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.DEFAULT_PLAYER_WEB_URLS, value)
        if self.support_alternative_player():
            return False
        return self.get_bool(SETTINGS.DEFAULT_PLAYER_WEB_URLS, False)

    def alternative_player_web_urls(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.ALTERNATIVE_PLAYER_WEB_URLS, value)
        if (self.support_alternative_player()
                and not self.alternative_player_mpd()):
            return self.get_bool(SETTINGS.ALTERNATIVE_PLAYER_WEB_URLS, False)
        return False

    def alternative_player_mpd(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.ALTERNATIVE_PLAYER_MPD, value)
        if self.support_alternative_player():
            return self.get_bool(SETTINGS.ALTERNATIVE_PLAYER_MPD, False)
        return False

    def use_isa(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.USE_ISA, value)
        return self.get_bool(SETTINGS.USE_ISA, False)

    def subtitle_download(self):
        return self.get_bool(SETTINGS.SUBTITLE_DOWNLOAD, False)

    def audio_only(self):
        return self.get_bool(SETTINGS.AUDIO_ONLY, False)

    def get_subtitle_selection(self):
        return self.get_int(SETTINGS.SUBTITLE_SELECTION, 0)

    def set_subtitle_selection(self, value):
        return self.set_int(SETTINGS.SUBTITLE_SELECTION, value)

    def set_subtitle_download(self, value):
        return self.set_bool(SETTINGS.SUBTITLE_DOWNLOAD, value)

    _THUMB_SIZES = {
        0: {  # Medium (16:9)
            'size': 320 * 180,
            'ratio': 320 / 180,
        },
        1: {  # High (4:3)
            'size': 480 * 360,
            'ratio': 480 / 360,
        },
        2: {  # Best available
            'size': 0,
            'ratio': 0,
        },
    }

    def get_thumbnail_size(self, value=None):
        default = 1
        if value is None:
            value = self.get_int(SETTINGS.THUMB_SIZE, default)
        if value in self._THUMB_SIZES:
            return self._THUMB_SIZES[value]
        return self._THUMB_SIZES[default]

    _SAFE_SEARCH_LEVELS = {
        0: 'moderate',
        1: 'none',
        2: 'strict',
    }

    def safe_search(self):
        index = self.get_int(SETTINGS.SAFE_SEARCH, 0)
        return self._SAFE_SEARCH_LEVELS[index]

    def age_gate(self):
        return self.get_bool(SETTINGS.AGE_GATE, True)

    def verify_ssl(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.VERIFY_SSL, value)

        if sys.version_info <= (2, 7, 9):
            verify = False
        else:
            verify = self.get_bool(SETTINGS.VERIFY_SSL, True)
        return verify

    def requests_timeout(self, value=None):
        if value is not None:
            self.set_int(SETTINGS.CONNECT_TIMEOUT, value[0])
            self.set_int(SETTINGS.READ_TIMEOUT, value[1])
            return value

        connect_timeout = self.get_int(SETTINGS.CONNECT_TIMEOUT, 9) + 0.5
        read_timout = self.get_int(SETTINGS.READ_TIMEOUT, 27)
        return connect_timeout, read_timout

    _PROXY_TYPE_SCHEME = {
        0: 'http',
        1: 'socks4',
        2: 'socks4a',
        3: 'socks5',
        4: 'socks5h',
        5: 'https',
    }

    _PROXY_SETTINGS = {
        SETTINGS.PROXY_ENABLED: {
            'value': None,
            'type': bool,
            'default': False,
            'kodi_name': 'network.usehttpproxy',
        },
        SETTINGS.PROXY_TYPE: {
            'value': None,
            'type': int,
            'default': 0,
            'kodi_name': 'network.httpproxytype',
        },
        SETTINGS.PROXY_SERVER: {
            'value': None,
            'type': str,
            'default': '',
            'kodi_name': 'network.httpproxyserver',
        },
        SETTINGS.PROXY_PORT: {
            'value': None,
            'type': int,
            'default': 8080,
            'kodi_name': 'network.httpproxyport',
        },
        SETTINGS.PROXY_USERNAME: {
            'value': None,
            'type': str,
            'default': '',
            'kodi_name': 'network.httpproxyusername',
        },
        SETTINGS.PROXY_PASSWORD: {
            'value': None,
            'type': str,
            'default': '',
            'kodi_name': 'network.httpproxypassword',
        },
    }

    def proxy_settings(self, value=None, as_mapping=True):
        if value is not None:
            for setting_name, setting in value.items():
                setting_value = setting.get('value')
                if setting_value is None:
                    continue

                setting_type = setting.get('type', int)
                if setting_type is int:
                    self.set_int(setting_name, setting_value)
                elif setting_type is str:
                    self.set_string(setting_name, setting_value)
                else:
                    self.set_bool(setting_name, setting_value)
            return value

        proxy_source = self.get_int(SETTINGS.PROXY_SOURCE, 1)
        if not proxy_source:
            return None

        settings = {}
        for setting_name, setting in self._PROXY_SETTINGS.items():
            setting_default = setting.get('default')
            setting_type = setting.get('type', int)
            if proxy_source == 1:
                setting_value = get_kodi_setting_value(
                    setting.get('kodi_name'),
                    process=setting_type,
                ) or setting_default
            elif setting_type is int:
                setting_value = self.get_int(setting_name, setting_default)
            elif setting_type is str:
                setting_value = self.get_string(setting_name, setting_default)
            else:
                setting_value = self.get_bool(setting_name, setting_default)

            settings[setting_name] = {
                'value': setting_value,
                'type': setting_type,
                'default': setting_default,
            }

        if not as_mapping:
            return settings

        if proxy_source == 1 and not settings[SETTINGS.PROXY_ENABLED]['value']:
            return None

        scheme = self._PROXY_TYPE_SCHEME[settings[SETTINGS.PROXY_TYPE]['value']]
        if scheme.startswith('socks'):
            from ..compatibility import xbmc, xbmcaddon

            pysocks = None
            install_attempted = False
            while not pysocks:
                try:
                    pysocks = xbmcaddon.Addon('script.module.pysocks')
                except RuntimeError:
                    if install_attempted:
                        break
                    xbmc.executebuiltin(
                        'InstallAddon(script.module.pysocks)',
                        wait=True,
                    )
                    install_attempted = True
            if pysocks:
                del pysocks
            else:
                return None

        host = settings[SETTINGS.PROXY_SERVER]['value']
        if not host:
            return None

        port = settings[SETTINGS.PROXY_PORT]['value']
        if port:
            host_port_string = ':'.join((host, str(port)))
        else:
            host_port_string = host

        username = settings[SETTINGS.PROXY_USERNAME]['value']
        if username:
            password = settings[SETTINGS.PROXY_PASSWORD]['value']
            if password:
                auth_string = ':'.join((username, password))
            else:
                auth_string = username
            auth_string += '@'
        else:
            auth_string = ''

        proxy_string = ''.join((scheme, '://', auth_string, host_port_string))
        return {
            'http': proxy_string,
            'https': proxy_string,
        }

    def allow_dev_keys(self):
        return self.get_bool(SETTINGS.ALLOW_DEV_KEYS, False)

    def use_mpd_videos(self, value=None):
        if self.use_isa():
            if value is not None:
                return self.set_bool(SETTINGS.MPD_VIDEOS, value)
            return self.get_bool(SETTINGS.MPD_VIDEOS, True)
        return False

    _LIVE_STREAM_TYPES = {
        0: 'mpegts',
        1: 'hls',
        2: 'isa_hls',
        3: 'isa_mpd',
    }

    def live_stream_type(self, value=None):
        if self.use_isa():
            default = 3
            setting = SETTINGS.LIVE_STREAMS + '.1'
        else:
            default = 1
            setting = SETTINGS.LIVE_STREAMS + '.2'
        if value is not None:
            return self.set_int(setting, value)
        value = self.get_int(setting, default)
        if value in self._LIVE_STREAM_TYPES:
            return self._LIVE_STREAM_TYPES[value]
        return self._LIVE_STREAM_TYPES[default]

    def use_isa_live_streams(self):
        if self.use_isa():
            return self.get_int(SETTINGS.LIVE_STREAMS + '.1', 2) > 1
        return False

    def use_mpd_live_streams(self):
        if self.use_isa():
            return self.get_int(SETTINGS.LIVE_STREAMS + '.1', 2) == 3
        return False

    def httpd_port(self, value=None):
        default = 50152

        if value is None:
            port = self.get_int(SETTINGS.HTTPD_PORT, default)
        else:
            port = value

        try:
            port = int(port)
        except ValueError:
            port = default

        if value is not None:
            return self.set_int(SETTINGS.HTTPD_PORT, port)
        return port

    def httpd_listen(self, value=None):
        default = '127.0.0.1'

        if value is None:
            ip_address = self.get_string(SETTINGS.HTTPD_LISTEN, default)
        else:
            ip_address = value

        octets = validate_ip_address(ip_address)
        ip_address = '.'.join(map(str, octets))

        if value is not None:
            return self.set_string(SETTINGS.HTTPD_LISTEN, ip_address)
        return ip_address

    def httpd_whitelist(self):
        whitelist = self.get_string(SETTINGS.HTTPD_WHITELIST, '')
        whitelist = ''.join(whitelist.split()).split(',')
        allow_list = []
        for ip_address in whitelist:
            octets = validate_ip_address(ip_address)
            if not any(octets):
                continue
            allow_list.append('.'.join(map(str, octets)))
        return allow_list

    def httpd_sleep_allowed(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.HTTPD_IDLE_SLEEP, value)
        return self.get_bool(SETTINGS.HTTPD_IDLE_SLEEP, True)

    def httpd_stream_redirect(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.HTTPD_STREAM_REDIRECT, value)
        return self.get_bool(SETTINGS.HTTPD_STREAM_REDIRECT, False)

    def api_config_page(self):
        return self.get_bool(SETTINGS.API_CONFIG_PAGE, False)

    def api_id(self, new_id=None):
        if new_id is not None:
            self.set_string(SETTINGS.API_ID, new_id)
            return new_id
        return self.get_string(SETTINGS.API_ID)

    def api_key(self, new_key=None):
        if new_key is not None:
            self.set_string(SETTINGS.API_KEY, new_key)
            return new_key
        return self.get_string(SETTINGS.API_KEY)

    def api_secret(self, new_secret=None):
        if new_secret is not None:
            self.set_string(SETTINGS.API_SECRET, new_secret)
            return new_secret
        return self.get_string(SETTINGS.API_SECRET)

    def get_location(self):
        location = self.get_string(SETTINGS.LOCATION, '').replace(' ', '').strip()
        coords = location.split(',')
        latitude = longitude = None
        if len(coords) == 2:
            try:
                latitude = float(coords[0])
                longitude = float(coords[1])
                if latitude > 90.0 or latitude < -90.0:
                    latitude = None
                if longitude > 180.0 or longitude < -180.0:
                    longitude = None
            except ValueError:
                latitude = longitude = None
        if latitude and longitude:
            return '{lat},{long}'.format(lat=latitude, long=longitude)
        return ''

    def set_location(self, value):
        self.set_string(SETTINGS.LOCATION, value)

    def get_location_radius(self):
        return ''.join((self.get_int(SETTINGS.LOCATION_RADIUS, 500, str), 'km'))

    def get_play_count_min_percent(self):
        return self.get_int(SETTINGS.PLAY_COUNT_MIN_PERCENT, 0)

    def use_local_history(self):
        return self.get_bool(SETTINGS.USE_LOCAL_HISTORY, False)

    def use_remote_history(self):
        return self.get_bool(SETTINGS.USE_REMOTE_HISTORY, False)

    # Selections based on max width and min height at common (utra-)wide aspect ratios
    _QUALITY_SELECTIONS = {                                                                         # Setting | Resolution
        7:   {'width': 7680, 'min_height': 3148, 'nom_height': 4320, 'label': '{0}p{1} (8K){2}'},   #   7     |   4320p 8K
        6:   {'width': 3840, 'min_height': 1080, 'nom_height': 2160, 'label': '{0}p{1} (4K){2}'},   #   6     |   2160p 4K
        5:   {'width': 2560, 'min_height': 984,  'nom_height': 1440, 'label': '{0}p{1} (QHD){2}'},  #   5     |   1440p 2.5K / QHD
        4.1: {'width': 2048, 'min_height': 858,  'nom_height': 1152, 'label': '{0}p{1} (2K){2}'},   #   N/A   |   1152p 2K / QWXGA
        4:   {'width': 1920, 'min_height': 787,  'nom_height': 1080, 'label': '{0}p{1} (FHD){2}'},  #   4     |   1080p FHD
        3:   {'width': 1280, 'min_height': 525,  'nom_height': 720,  'label': '{0}p{1} (HD){2}'},   #   3     |   720p  HD
        2:   {'width': 854,  'min_height': 350,  'nom_height': 480,  'label': '{0}p{1}{2}'},        #   2     |   480p
        1:   {'width': 640,  'min_height': 263,  'nom_height': 360,  'label': '{0}p{1}{2}'},        #   1     |   360p
        0:   {'width': 426,  'min_height': 175,  'nom_height': 240,  'label': '{0}p{1}{2}'},        #   0     |   240p
        -1:  {'width': 256,  'min_height': 105,  'nom_height': 144,  'label': '{0}p{1}{2}'},        #   N/A   |   144p
        -2:  {'width': 0,    'min_height': 0,    'nom_height': 0,    'label': '{0}p{1}{2}'},        #   N/A   |   Custom
    }

    def mpd_video_qualities(self, value=None):
        if value is not None:
            return self.set_int(SETTINGS.MPD_QUALITY_SELECTION, value)
        if not self.use_mpd_videos():
            return []
        value = self.get_int(SETTINGS.MPD_QUALITY_SELECTION, 4)
        return [quality
                for key, quality in sorted(self._QUALITY_SELECTIONS.items(),
                                           reverse=True)
                if value >= key]

    def stream_features(self, value=None):
        if value is not None:
            return self.set_string_list(SETTINGS.MPD_STREAM_FEATURES, value)
        return frozenset(self.get_string_list(SETTINGS.MPD_STREAM_FEATURES))

    _STREAM_SELECT = {
        1: 'auto',
        2: 'list',
        3: 'auto+list',
        4: 'ask+auto+list',
    }

    def stream_select(self, value=None):
        if self.use_mpd_videos():
            setting = SETTINGS.MPD_STREAM_SELECT
            default = 3
        else:
            setting = SETTINGS.VIDEO_STREAM_SELECT
            default = 2

        if value is not None:
            return self.set_int(setting, value)
        value = self.get_int(setting, default)
        if value in self._STREAM_SELECT:
            return self._STREAM_SELECT[value]
        return self._STREAM_SELECT[default]

    _DEFAULT_FILTER = {
        'shorts': True,
        'upcoming': True,
        'upcoming_live': True,
        'live': True,
        'premieres': True,
        'completed': True,
        'vod': True,
        'custom': None,
    }

    def item_filter(self, update=None, override=None, exclude=None):
        if override is None:
            override = self.get_string_list(SETTINGS.HIDE_VIDEOS)
            override = dict.fromkeys(override, False)
            override['custom'] = (self.get_string(SETTINGS.FILTER_LIST)
                                  .split(','))
        elif isinstance(override, (list, tuple)):
            _override = {'custom': []}
            for value in override:
                if value in self._DEFAULT_FILTER:
                    _override[value] = False
                else:
                    _override['custom'].append(value)
            override = _override
        types = dict(self._DEFAULT_FILTER, **override)

        if update:
            if 'live_folder' in update:
                if 'live_folder' not in types:
                    update.update((
                        ('vod', False),
                        ('upcoming', True),
                        ('upcoming_live', True),
                        ('live', True),
                        ('premieres', True),
                        ('completed', True),
                    ))
            types.update(update)

        if exclude:
            types['exclude'] = exclude

        return types

    def subscriptions_filter_enabled(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.SUBSCRIPTIONS_FILTER_ENABLED, value)
        return self.get_bool(SETTINGS.SUBSCRIPTIONS_FILTER_ENABLED, True)

    def subscriptions_filter_blacklist(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.SUBSCRIPTIONS_FILTER_BLACKLIST, value)
        return self.get_bool(SETTINGS.SUBSCRIPTIONS_FILTER_BLACKLIST, True)

    def subscriptions_filter(self, value=None):
        if value is not None:
            if isinstance(value, (list, tuple, set)):
                value = ','.join(value).lstrip(',')
            return self.set_string(SETTINGS.SUBSCRIPTIONS_FILTER_LIST, value)
        return self.get_string(
            SETTINGS.SUBSCRIPTIONS_FILTER_LIST, ''
        ).replace(', ', ',')

    def shorts_duration(self, value=None):
        if value is not None:
            return self.set_int(SETTINGS.SHORTS_DURATION, value)
        return self.get_int(SETTINGS.SHORTS_DURATION, 60)

    def show_detailed_description(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.DETAILED_DESCRIPTION, value)
        return self.get_bool(SETTINGS.DETAILED_DESCRIPTION, True)

    def show_detailed_labels(self, value=None):
        if value is not None:
            return self.set_bool(SETTINGS.DETAILED_LABELS, value)
        return self.get_bool(SETTINGS.DETAILED_LABELS, True)

    def get_language(self):
        return self.get_string(SETTINGS.LANGUAGE, 'en_US').replace('_', '-')

    def set_language(self, language_id):
        return self.set_string(SETTINGS.LANGUAGE, language_id)

    def get_region(self):
        return self.get_string(SETTINGS.REGION, 'US')

    def set_region(self, region_id):
        return self.set_string(SETTINGS.REGION, region_id)

    def get_watch_later_playlist(self):
        return self.get_string(SETTINGS.WATCH_LATER_PLAYLIST, '').strip()

    def set_watch_later_playlist(self, value):
        return self.set_string(SETTINGS.WATCH_LATER_PLAYLIST, value)

    def get_history_playlist(self):
        return self.get_string(SETTINGS.HISTORY_PLAYLIST, '').strip()

    def set_history_playlist(self, value):
        return self.set_string(SETTINGS.HISTORY_PLAYLIST, value)

    if current_system_version.compatible(20):
        _COLOR_SETTING_MAP = {
            'itemCount': 'commentCount',
            'subscriberCount': 'likeCount',
            'videoCount': 'commentCount',
        }

        def get_label_color(self, label_part):
            label_part = self._COLOR_SETTING_MAP.get(label_part) or label_part
            setting_name = '.'.join((SETTINGS.LABEL_COLOR, label_part))
            return self.get_string(setting_name, 'white')
    else:
        _COLOR_MAP = {
            'commentCount': 'cyan',
            'favoriteCount': 'gold',
            'itemCount': 'cyan',
            'likeCount': 'lime',
            'viewCount': 'lightblue',
        }

        def get_label_color(self, label_part):
            return self._COLOR_MAP.get(label_part, 'white')

    def get_channel_name_aliases(self):
        return frozenset(self.get_string_list(SETTINGS.CHANNEL_NAME_ALIASES))

    def logging_enabled(self):
        return (self.get_int(SETTINGS.LOGGING_ENABLED, 0)
                or get_kodi_setting_bool('debug.showloginfo'))
