#!/usr/bin/python3.6
import argparse
import glob
import logging
import signal
import time
from os.path import exists
import coloredlogs
from .bot_factory import retrieve_bots
from .bot_storage import LocalBotStorage, SscaitBotStorage
from .docker import check_docker_requirements, BASE_VNC_PORT, launch_game, stop_containers
from .game import GameType, find_winner, create_data_dirs, find_replays
from .map import check_map_exists, download_sscait_maps
from .player import HumanPlayer, PlayerRace, bot_regex
from .utils import random_string, get_data_dir
from .vnc import check_vnc_exists
VERSION = '0.2a9'
logger = logging.getLogger(__name__)
base_dir = get_data_dir()
SC_LOG_DIR = ('%s/logs' % (base_dir, ))
SC_BWAPI_DATA_BWTA_DIR = ('%s/bwapi-data/BWTA' % (base_dir, ))
SC_BWAPI_DATA_BWTA2_DIR = ('%s/bwapi-data/BWTA2' % (base_dir, ))
SC_BOT_DIR = ('%s/bots' % (base_dir, ))
SC_MAP_DIR = ('%s/maps' % (base_dir, ))
SC_IMAGE = 'starcraft:game'
parser = argparse.ArgumentParser(
    description=
    'Launch StarCraft docker images for bot/human headless/headful play',
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument(
    '--bots',
    nargs='+',
    required=True,
    type=bot_regex,
    metavar='BOT_NAME[:RACE]',
    help=("""Specify the names of the bots that should play.
Optional RACE can be one of %s 
If RACE isn't specified it will be loaded from cache if possible.
The bots are looked up in the --bot_dir directory.
If some does not exist, launcher 
will try to download it from SSCAIT server.
Examples: 
  --bots Tyr:P PurpleWave:P
  --bots Tyr PurpleWave """ % ([race.value for race in PlayerRace], )))
parser.add_argument(
    '--human',
    action='store_true',
    help="""Allow play as human against bot.
""")
parser.add_argument(
    '--map',
    type=str,
    metavar='MAP.scx',
    default='sscai/(2)Benzene.scx',
    help="""Name of map on which SC should be played,
relative to --map_dir""")
parser.add_argument(
    '--headless',
    action='store_true',
    help="""Launch play in headless mode. 
No VNC viewer will be launched.""")
parser.add_argument(
    '--game_name',
    type=str,
    default=random_string(8),
    help='Override the auto-generated game name')
parser.add_argument(
    '--game_type',
    type=str,
    metavar='GAME_TYPE',
    default=GameType.FREE_FOR_ALL.value,
    choices=[game_type.value for game_type in GameType],
    help=("""Set game type. It can be one of:
- """ + """
- """.join([game_type.value for game_type in GameType])))
parser.add_argument(
    '--game_speed',
    type=int,
    default=0,
    help="""Set game speed (pause of ms between frames),
use -1 for game default.""")
parser.add_argument(
    '--timeout',
    type=int,
    default=None,
    help="""Kill docker container after timeout seconds.
If not set, run without timeout.""")
parser.add_argument(
    '--bot_dir',
    type=str,
    default=SC_BOT_DIR,
    help=("""Directory where bots are stored, default:
%s""" % (SC_BOT_DIR, )))
parser.add_argument(
    '--log_dir',
    type=str,
    default=SC_LOG_DIR,
    help=("""Directory where logs are stored, default:
%s""" % (SC_LOG_DIR, )))
parser.add_argument(
    '--map_dir',
    type=str,
    default=SC_MAP_DIR,
    help=("""Directory where maps are stored, default:
%s""" % (SC_MAP_DIR, )))
parser.add_argument(
    '--bwapi_data_bwta_dir',
    type=str,
    default=SC_BWAPI_DATA_BWTA_DIR,
    help=("""Directory where BWTA map caches are stored, default:
%s""" % (SC_BWAPI_DATA_BWTA_DIR, )))
parser.add_argument(
    '--bwapi_data_bwta2_dir',
    type=str,
    default=SC_BWAPI_DATA_BWTA2_DIR,
    help=("""Directory where BWTA2 map caches are stored, default:
%s""" % (SC_BWAPI_DATA_BWTA2_DIR, )))
parser.add_argument(
    '--vnc_base_port',
    type=int,
    default=BASE_VNC_PORT,
    help="""VNC lowest port number (for server).
Each consecutive n-th client (player)
has higher port number - vnc_base_port+n """)
parser.add_argument(
    '--show_all',
    action='store_true',
    help='Launch VNC viewers for all containers, not just the server.')
parser.add_argument(
    '--log_level',
    type=str,
    default='INFO',
    choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
    help='Logging level.')
parser.add_argument(
    '--read_overwrite',
    action='store_true',
    help="""At the end of each game, copy the contents
of 'write' directory to the read directory
of the bot.
Needs to be explicitly turned on.""")
parser.add_argument(
    '--docker_image',
    type=str,
    default=SC_IMAGE,
    help="""The name of the image that should 
be used to launch the game.
This helps with local development.""")
parser.add_argument(
    '--opt', type=str, help='Specify custom docker run options')


def main():
    args = parser.parse_args()
    coloredlogs.install(level=args.log_level, fmt='%(levelname)s %(message)s')
    check_docker_requirements(args.docker_image)
    create_data_dirs(args.bot_dir, args.log_dir, args.map_dir,
                     args.bwapi_data_bwta_dir, args.bwapi_data_bwta2_dir)
    try:
        check_map_exists(((args.map_dir + '/') + args.map))
    except Exception:
        if (('sscai' in args.map) and (not exists(
            ('%s/sscai' % (args.map_dir, ))))):
            download_sscait_maps(args.map_dir)
    if (not args.headless):
        check_vnc_exists()
    if (args.human and args.headless):
        raise Exception('Cannot use human play in headless mode')
    if (args.headless and args.show_all):
        raise Exception('Cannot show all screens in headless mode')
    game_name = ('GAME_' + args.game_name)
    players = []
    if args.human:
        players.append(HumanPlayer())
    bot_storages = (LocalBotStorage(args.bot_dir),
                    SscaitBotStorage(args.bot_dir))
    players += retrieve_bots(args.bots, bot_storages)
    opts = ([] if (not args.opt) else args.opt.split(' '))
    launch_params = dict(
        headless=args.headless,
        game_name=game_name,
        map_name=args.map,
        game_type=GameType(args.game_type),
        game_speed=args.game_speed,
        timeout=args.timeout,
        log_dir=args.log_dir,
        bot_dir=args.bot_dir,
        map_dir=args.map_dir,
        bwapi_data_bwta_dir=args.bwapi_data_bwta_dir,
        bwapi_data_bwta2_dir=args.bwapi_data_bwta2_dir,
        vnc_base_port=args.vnc_base_port,
        docker_image=args.docker_image,
        docker_opts=opts)
    try:
        time_start = time.time()
        launch_game(players, launch_params, args.show_all, args.read_overwrite)
        diff = (time.time() - time_start)
        logger.info(('Game %s finished in %s seconds.' % (game_name, diff)))
        logger.info('Logs are saved here:')
        log_files = glob.glob(('%s/*%s*.log' % (args.log_dir, game_name)))
        for log_file in log_files:
            logger.info(log_file)
        replay_files = find_replays(args.map_dir, game_name)
        logger.info('Replays are saved here:')
        for replay_file in replay_files:
            logger.info(replay_file)
        nth_player = find_winner(game_name, args.map_dir, len(players))
        logger.info(('Winner is %s (player %s)' % (players[nth_player],
                                                   nth_player)))
        print(nth_player)
    except KeyboardInterrupt:
        logger.info('Caught interrupt, shutting down containers')
        logger.info('This can take a moment, please wait.')
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        stop_containers(game_name)
        logger.info(('Game cancelled.' % ()))


if (__name__ == '__main__'):
    main()
