import glob
import os
from enum import Enum
import numpy as np


class GameType(Enum):
    TOP_VS_BOTTOM = 'TOP_VS_BOTTOM'
    MELEE = 'MELEE'
    FREE_FOR_ALL = 'FREE_FOR_ALL'
    ONE_ON_ONE = 'ONE_ON_ONE'
    USE_MAP_SETTINGS = 'USE_MAP_SETTINGS'
    CAPTURE_THE_FLAG = 'CAPTURE_THE_FLAG'
    GREED = 'GREED'
    SLAUGHTER = 'SLAUGHTER'
    SUDDEN_DEATH = 'SUDDEN_DEATH'
    TEAM_MELEE = 'TEAM_MELEE'
    TEAM_FREE_FOR_ALL = 'TEAM_FREE_FOR_ALL'
    TEAM_CAPTURE_THE_FLAG = 'TEAM_CAPTURE_THE_FLAG'


def find_replays(map_dir, game_name):
    return glob.glob(('%s/replays/*-*-*_%s_*.rep' % (map_dir, game_name)))


def find_winner(game_name, map_dir, num_players):
    replay_files = find_replays(map_dir, game_name)
    if (len(replay_files) != num_players):
        raise Exception((
            "The game did not finish properly! Did not find replay files from all players in '%s/replays/'."
            % (map_dir, )))
    replay_sizes = map(os.path.getsize, replay_files)
    winner_idx = np.argmax(replay_sizes)
    winner_file = replay_files[winner_idx]
    nth_player = winner_file.replace('.rep', '').split('_')[(-1)]
    return int(nth_player)


def create_data_dirs(*dir_paths):
    for dir_path in dir_paths:
        os.makedirs(dir_path, mode=509, exist_ok=True)
