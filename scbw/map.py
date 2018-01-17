import logging
import os
from os.path import exists, abspath
from .utils import download_extract_zip
SC_MAP_DIR = abspath('maps')
logger = logging.getLogger(__name__)


def check_map_exists(map_file):
    if (not exists(map_file)):
        raise Exception(('Map %s could not be found' % (map_file, )))


def download_sscait_maps(map_dir):
    logger.info('downloading maps from SSCAI')
    download_extract_zip('http://sscaitournament.com/files/sscai_map_pack.zip',
                         map_dir)
    os.makedirs(('%s/replays' % (map_dir, )), exist_ok=True)
