import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import numpy as np

MAP_SIZE = 28

TL = [[0, 14], [1, 15], [2, 16], [3, 17], [4, 18], [5, 19], [6, 20], [7, 21], [8, 22], [9, 23], [10, 24], [11, 25], [12, 26], [13, 27]]
TR = [[14, 27], [15, 26], [16, 25], [17, 24], [18, 23], [19, 22], [20, 21], [21, 20], [22, 19], [23, 18], [24, 17], [25, 16], [26, 15], [27, 14]]
BL = [[0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6], [8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0]]
BR = [[14, 0], [15, 1], [16, 2], [17, 3], [18, 4], [19, 5], [20, 6], [21, 7], [22, 8], [23, 9], [24, 10], [25, 11], [26, 12], [27, 13]]

WALL_LOCATIONS = [[4, 13], [23, 13], [9, 13], [18, 13]]
TURRET_LOCATIONS = [[4, 12], [9, 12], [18, 12], [23, 12]]
SUPPORT_LOCATIONS = [[11, 7], [12, 7], [13, 7], [14, 7], [15, 7], [16, 7], [12, 6], [13, 6], [14, 6], [15, 6], [13, 5], [14, 5]]

WALL_LOCATIONS2 = [[3, 13], [5, 13], [10, 13], [11, 13], [16, 13], [17, 13], [22, 13], [24, 13]]
TURRET_LOCATIONS2 = [[3, 12], [24, 12], [22, 12], [10, 12], [17, 12], [5, 12], [11, 12], [16, 12], [6, 12], [12, 12], [15, 12], [21, 12]]

# UNITS_LOCATIONS = [[0, 13], [27, 13], [1, 12], [26, 12], [4, 9], [23, 9], [8, 5], [19, 5], [11, 2], [16, 2], [13, 0], [14, 0]]

UNITS_LOCATIONS2 = [[13, 0], [14, 0], [6, 7], [7, 6], [20, 6], [8, 5], [19, 5], [9, 4], [18, 4], [10, 3], [17, 3], [11, 2], [16, 2], [12, 1], [15, 1]]


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.own_placed_turret = []

        
        self.board = np.zeros((MAP_SIZE, MAP_SIZE), dtype = object)
        self.turn_scored_on_locations = []
        gamelib.debug_write(TURRET_LOCATIONS2)

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        turn_number = game_state.turn_number
        gamelib.debug_write('Performing turn {}'.format(turn_number))
        game_state.suppress_warnings(True)

        self.hp0 = game_state.my_health
        self.hp1 = game_state.enemy_health
        self.mp0 = game_state.get_resource(1, 0)
        self.sp0 = game_state.get_resource(0, 0)
        self.mp1 = game_state.get_resource(1, 1)
        self.sp1 = game_state.get_resource(0, 1)

        self.get_turret_locations(game_state)

        if turn_number == 0:
            game_state.attempt_spawn(TURRET, TURRET_LOCATIONS)
            game_state.attempt_spawn(WALL, WALL_LOCATIONS)
            game_state.attempt_upgrade(TURRET_LOCATIONS)
            game_state.submit_turn()
            return


        path, damage = self.least_damage_defensive_path(game_state, [[13, 17], [14, 27]])

            # first_occurence = None
            # for coord in path:
            #     if coord[1] == 12 and coord[0] != 2 or coord[1] == 12 and coord[0] != 25:
            #         first_occurence = coord
            #         break

            # if first_occurence is not None:
            #   game_state.attempt_spawn(TURRET, first_occurence)

        self.starter_strategy(game_state)

        game_state.submit_turn()

    def starter_strategy(self, game_state):
        self.attack_strategy(game_state)
        self.build_defences(game_state)
        self.build_reactive_defense(game_state)



    def attack_strategy(self, game_state):
        to_spawn, damage = self.least_damage_spawn_location(game_state, UNITS_LOCATIONS2)

        if self.sp0 >= 8:
            support = 2
        else:
            support = 1

        hp = 12 + support * 3
        total_hp = self.mp0 * hp    

        hp_deduct = (total_hp - damage) / hp

        left = (to_spawn[0] < 13.5)

        attack = False
        if self.hp1 * 2.2 < hp_deduct:
            attack = True

        elif damage * 2.2 < total_hp:
            attack = True

        elif damage * 1.4 < total_hp and self.mp0 >= 10:
            attack = True
            
        elif self.mp0 >= 13:
            attack = True
            
        if attack:
            if left:
                game_state.attempt_spawn(SUPPORT, [to_spawn[0] - 1, to_spawn[1] + 1])
                if support == 2:
                    game_state.attempt_spawn(SUPPORT, [to_spawn[0] - 1, to_spawn[1] + 3])
            else:
                game_state.attempt_spawn(SUPPORT, [to_spawn[0] + 1, to_spawn[1] + 1])
                if support == 2:
                    game_state.attempt_spawn(SUPPORT, [to_spawn[0] + 1, to_spawn[1] + 3])
            game_state.attempt_spawn(SCOUT, to_spawn, 1000)
        
        game_state.attempt_remove([to_spawn[0] + 1, to_spawn[1] + 1])
        # game_state.attempt_remove([to_spawn[0] + 1, to_spawn[1] + 2])
        game_state.attempt_remove([to_spawn[0] - 1, to_spawn[1] + 1])
        # game_state.attempt_remove([to_spawn[0] - 1, to_spawn[1] + 2])

        gamelib.debug_write(damage)


    def killing_blow(self, game_state):
        pass

    def build_defences(self, game_state):
        # Place turrets that attack enemy units
        game_state.attempt_spawn(TURRET, TURRET_LOCATIONS)
        game_state.attempt_upgrade(TURRET_LOCATIONS)
        
        # Place walls in front of turrets to soak up damage for them
        game_state.attempt_spawn(WALL, WALL_LOCATIONS)
        game_state.attempt_upgrade(WALL_LOCATIONS)

        for turret_location in self.own_placed_turret:
            turret = game_state.game_map[turret_location[0], turret_location[1]][0]
            if turret.health > 50 and turret.upgraded:
                # gamelib.debug_write("HALLO")
                game_state.attempt_spawn(WALL, [turret_location[0], turret_location[1] + 1])

        sp = game_state.get_resource(0)

        if sp > 10:
            self.build_upgrade_n_defenses(TURRET, 1, TURRET_LOCATIONS2, game_state)
            self.build_upgrade_n_defenses(WALL, 1, WALL_LOCATIONS2, game_state)
        
        self.build_upgrade_n_defenses(TURRET, 1, TURRET_LOCATIONS2, game_state)
        self.build_n_defenses(TURRET, 2, TURRET_LOCATIONS2, game_state)

        # self.build_upgrade_n_defenses(SUPPORT, 10, SUPPORT_LOCATIONS, game_state)

    def get_turret_locations(self, game_state, player_index = 0):
        turret_locations = []
        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):
                unit = game_state.game_map[i, j]
                self.board[i][j] = unit
                if unit and unit[0].unit_type == 'DF' and unit[0].player_index == player_index:
                    turret_locations.append([unit[0].x, unit[0].y])

        self.own_placed_turret = turret_locations
        gamelib.debug_write("NUMBER OF TURRETS: {}".format(len(turret_locations)))

    def build_reactive_defense(self, game_state):
        ms0 = game_state.get_resource(0)
        if ms0 < 10:
            return

        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            wall_location = [location[0], location[1]+2]
            game_state.attempt_spawn(TURRET, build_location)
            game_state.attempt_upgrade(build_location)
            game_state.attempt_spawn(WALL, wall_location)

    def build_upgrade_n_defenses(self, defense_type, n, locations, game_state):
        for location in locations:
            if n <= 0:
                break
            spawned = game_state.attempt_spawn(defense_type, location)
            #check if turret is above certain amount of health
            unit_at_location = gamelib.game_map[location[0], location[1]]
            if unit_at_location and unit_at_location[0].health > 50:
                game_state.attempt_upgrade(location)
            n -= spawned

    def least_damage_spawn_location(self, game_state, location_options):
        damages = []
        hps = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            hp = 0
            if path is not None and path[-1][1] > 13: 
                for path_location in path:
                    potential_turret_locations = game_state.game_map.get_locations_in_range(path_location, 4.5)
                    for turret_location in potential_turret_locations:
                        units_at_location = game_state.game_map[turret_location[0], turret_location[1]]
                        for unit in units_at_location:
                            hp += unit.health
                            if unit.unit_type == TURRET and unit.player_index == 1:
                                if unit.upgraded:
                                    damage += 14
                                else:
                                    distance = game_state.game_map.distance_between_locations(path_location, turret_location)
                                    if distance <= 2.5:
                                        damage += 6
            else:
                damage = 999999
            damages.append(damage)
            hps.append(damage)
        
        min_damage = min(damages)
        if min_damage == 999999:
            return None
        else:
            min_damage_indices = [i for i, dmg in enumerate(damages) if dmg == min_damage]
            min_hp_index = min(min_damage_indices, key=lambda i: hps[i])
            best_location = location_options[min_hp_index]
            return best_location, min_damage

    def least_damage_defensive_path(self, game_state, location_options):

        damages = []
        paths = []
        
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            if path is not None and path[-1][1] < 14:
                for path_location in path:
                    potential_turret_locations = game_state.game_map.get_locations_in_range(path_location, 4.5)
                    for turret_location in potential_turret_locations:
                        units_at_location = game_state.game_map[turret_location[0], turret_location[1]]
                        for unit in units_at_location:
                            if unit.unit_type == TURRET and unit.player_index == 0:
                                if unit.upgraded:
                                    damage += 14
                                else:
                                    distance = game_state.game_map.distance_between_locations(path_location, turret_location)
                                    if distance <= 2.5:
                                        damage += 6
            else:
                damage = 999999
            damages.append(damage)
            paths.append(path)
        min_damage = min(damages)
        if min_damage == 999999:
            return None
        else:
            return paths[damages.index(min_damage)], min_damage
    
    def build_n_defenses(self, defense_type, n, locations, game_state):
        for location in locations:
            if n <= 0:
                break
            spawned = game_state.attempt_spawn(defense_type, location)
            n -= spawned

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        # Let's record at what position we get scored on
        scored_on = []
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                scored_on.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

        self.scored_on_locations = scored_on

if __name__ == "__main__": 
    algo = AlgoStrategy()
    algo.start()
