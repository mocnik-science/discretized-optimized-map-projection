import os

APP_NAME = 'Discretized Optimized Map Projection'
APP_NAME_WITH_LINEBREAK = 'Discretized Optimized\nMap Projection'
APP_COPYRIGHT = '(c) by Franz-Benjamin Mocnik, 2023–2024'
APP_URL = 'https://github.com/mocnik-science/discretized-optimized-map-projection'
APP_FILE_FORMAT = 'Discretized Optimized Map Projection file'
APP_FILES_PATH_NON_EXPANDED = '~/.domp/'
APP_FILES_PATH = os.path.expanduser(APP_FILES_PATH_NON_EXPANDED)
APP_SETTINGS_PATH = os.path.join(APP_FILES_PATH, 'settings')
APP_VIEW_SETTINGS_PATH = os.path.join(APP_FILES_PATH, 'viewSettings')
APP_CAPTURE_PATH_NON_EXPANDED = os.path.join(APP_FILES_PATH_NON_EXPANDED, 'capture')
APP_CAPTURE_PATH = os.path.expanduser(APP_CAPTURE_PATH_NON_EXPANDED)
