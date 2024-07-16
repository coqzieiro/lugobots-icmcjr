import lugo4py
import lugo4py.mapper as mapper
import math

# MAPPER_COLS and MAPPER_ROWS define the number of regions on the field.
# great values leads to more precision
# Use this tool to help you to decide about it https://github.com/mauriciorobertodev/strategy-creator-lugo-bots
MAPPER_COLS = 10
MAPPER_ROWS = 6

def get_my_expected_position(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper, number: int):
    mapper_cols = MAPPER_COLS

    player_tactic_positions = {
        'DEFENSIVE': {
            2: {'Col': 1, 'Row': 2},
            3: {'Col': 2, 'Row': 1},
            4: {'Col': 2, 'Row': 4},
            5: {'Col': 1, 'Row': 3},
            6: {'Col': 3, 'Row': 2},
            7: {'Col': 2, 'Row': 2},
            8: {'Col': 2, 'Row': 3},
            9: {'Col': 3, 'Row': 3},
            10: {'Col': 4, 'Row': 4},
            11: {'Col': 5, 'Row': 1},
        },
        'NORMAL': {
            2: {'Col': 2, 'Row': 2},
            3: {'Col': 4, 'Row': 2},
            4: {'Col': 4, 'Row': 3},
            5: {'Col': 2, 'Row': 3},
            6: {'Col': 5, 'Row': 1},
            7: {'Col': 5, 'Row': 2},
            8: {'Col': 5, 'Row': 3},
            9: {'Col': 5, 'Row': 4},
            10: {'Col': 6, 'Row': 3},
            11: {'Col': 7, 'Row': 1},
        },
        'OFFENSIVE': {
            2: {'Col': 4, 'Row': 2},
            3: {'Col': 6, 'Row': 2},
            4: {'Col': 6, 'Row': 3},
            5: {'Col': 4, 'Row': 3},
            6: {'Col': 7, 'Row': 1},
            7: {'Col': 7, 'Row': 2},
            8: {'Col': 9, 'Row': 3},
            9: {'Col': 7, 'Row': 4},
            10: {'Col': 9, 'Row': 4},
            11: {'Col': 9, 'Row': 1},
        },
        'ATTACK': {
            2: {'Col': 5, 'Row': 2},
            3: {'Col': 7, 'Row': 2},
            4: {'Col': 7, 'Row': 3},
            5: {'Col': 5, 'Row': 3},
            6: {'Col': 8, 'Row': 1},
            7: {'Col': 8, 'Row': 2},
            8: {'Col': 10, 'Row': 3},
            9: {'Col': 8, 'Row': 4},
            10: {'Col': 10, 'Row': 4},
            11: {'Col': 10, 'Row': 1},
        }
    }

    ball_region = my_mapper.get_region_from_point(inspector.get_ball().position)
    ball_cols = ball_region.get_col()

    ball_holder = inspector.get_ball().holder
    team_state = "OFFENSIVE"

    if ball_cols < 4 or (ball_holder is not None and ball_holder.get_team_side() != inspector.get_my_team().side):
        team_state = "DEFENSIVE"
    elif ball_cols < 6:
        team_state = "NORMAL"
    elif ball_holder is not None and ball_holder.get_team_side() == inspector.get_my_team().side:
        team_state = "ATTACK"

    expected_region = my_mapper.get_region(
        player_tactic_positions[team_state][number]['Col'],
        player_tactic_positions[team_state][number]['Row']
    )
    return expected_region.get_center()

def get_distance(r1: mapper.Region, r2: mapper.Region):
    return math.sqrt((r2.get_col() - r1.get_col())**2 + (r1.get_row() - r2.get_row())**2)

def get_closest_enemy_dist(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper):
    player_position = inspector.get_ball().position
    opponents = inspector.get_opponent_players()

    nearest_opponent = None
    min_distance = math.inf
    for opponent in opponents:
        current_distance = get_distance_between_points(player_position.x, player_position.y, opponent.position.x, opponent.position.y)
        if current_distance < min_distance:
            min_distance = current_distance
            nearest_opponent = opponent

    return min_distance, nearest_opponent

def get_distance_between_points(x1, y1, x2, y2):
    distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    return distance

def get_closest_ally_position(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper):
    player_list = inspector.get_my_team_players()
    player_position = inspector.get_ball().position
    holder_number = inspector.get_ball().holder.number

    closest_ally = {}
    for ally in player_list:
        if ally.number != holder_number and ally.number != 1:
            distance = get_distance_between_points(ally.position.x, ally.position.y, player_position.x, player_position.y)
            if distance not in closest_ally:
                closest_ally[distance] = [ally]
            else:
                closest_ally[distance].append(ally)

    closest_ally = dict(sorted(closest_ally.items(), key=lambda x: x[0]))

    return closest_ally

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point(x={self.x}, y={self.y})"

def has_other_closest(inspector: lugo4py.GameSnapshotInspector, player_me):
    counter = 0
    players = inspector.get_my_team_players()
    ball_position = inspector.get_ball().position
    for player in players:
        if get_distance_between_points(player.position.x, player.position.y, ball_position.x, ball_position.y) > get_distance_between_points(player_me.position.x, player_me.position.y, ball_position.x, ball_position.y) and player_me.number != 1:
            counter += 1
    return counter < 5
