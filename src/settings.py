import lugo4py
import lugo4py.mapper as mapper
import math

# MAPPER_COLS and MAPPER_ROWS define the number of regions on the field.
# great values leads to more precision
# Use this tool to help you to decide about it https://github.com/mauriciorobertodev/strategy-creator-lugo-bots
MAPPER_COLS = 10
MAPPER_ROWS = 6



# Example how to create your custom initial positions
# PLAYER_INITIAL_POSITIONS = {
#     1: {'Col': 0, 'Row': 0},
#     2: {'Col': 1, 'Row': 1},
#     3: {'Col': 2, 'Row': 2},
#     4: {'Col': 2, 'Row': 3},
#     5: {'Col': 1, 'Row': 4},
#     6: {'Col': 3, 'Row': 1},
#     7: {'Col': 3, 'Row': 2},
#     8: {'Col': 3, 'Row': 3},
#     9: {'Col': 3, 'Row': 4},
#     10: {'Col': 4, 'Row': 3},
#     11: {'Col': 4, 'Row': 2},
# }

def get_my_expected_position(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper, number: int):
    mapper_cols = MAPPER_COLS

    player_tactic_positions = {
        'DEFENSIVE': {
            2: {'Col': 1, 'Row': 1},
            3: {'Col': 2, 'Row': 2},
            4: {'Col': 2, 'Row': 3},
            5: {'Col': 1, 'Row': 4},
            6: {'Col': 3, 'Row': 1},
            7: {'Col': 3, 'Row': 2},
            8: {'Col': 3, 'Row': 3},
            9: {'Col': 3, 'Row': 4},
            10: {'Col': 4, 'Row': 3},
            11: {'Col': 4, 'Row': 2},
        },
        'NORMAL': {
            2: {'Col': 2, 'Row': 1},
            3: {'Col': 4, 'Row': 2},
            4: {'Col': 4, 'Row': 3},
            5: {'Col': 2, 'Row': 4},
            6: {'Col': 6, 'Row': 1},
            7: {'Col': 8, 'Row': 2},
            8: {'Col': 8, 'Row': 3},
            9: {'Col': 6, 'Row': 4},
            10: {'Col': 7, 'Row': 4},
            11: {'Col': 7, 'Row': 1},
        },
        'OFFENSIVE': {
            2: {'Col': 3, 'Row': 1},
            3: {'Col': 5, 'Row': 2},
            4: {'Col': 5, 'Row': 3},
            5: {'Col': 3, 'Row': 4},
            6: {'Col': 7, 'Row': 1},
            7: {'Col': 8, 'Row': 2},
            8: {'Col': 8, 'Row': 3},
            9: {'Col': 7, 'Row': 4},
            10: {'Col': 9, 'Row': 3},
            11: {'Col': 9, 'Row': 2},
        }
    }

    ball_region = my_mapper.get_region_from_point(inspector.get_ball().position)
    field_third = mapper_cols / 3
    ball_cols = ball_region.get_col()

    team_state = "OFFENSIVE"
    if ball_cols < field_third:
        team_state = "DEFENSIVE"
    elif ball_cols < field_third * 2:
        team_state = "NORMAL"

    expected_region = my_mapper.get_region(player_tactic_positions[team_state][number]['Col'],
                                           player_tactic_positions[team_state][number]['Row'])
    return expected_region.get_center()


def get_distance(r1: mapper.Region, r2: mapper.Region):
    return math.sqrt((r2.get_col() - r1.get_col())**2 + (r2.get_row() - r1.get_row())**2)

def get_closestenemy_dist(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper):
    player_position = inspector.get_ball().position
    oponentes = inspector.get_opponent_players()

    nearesopponent = math.inf
    minDistance = math.inf
    for opponent in oponentes:
        current_distance = getDistance(player_position.x, player_position.y, opponent.position.x, opponent.position.y)
        if (current_distance < minDistance):
            minDistance = current_distance
            nearesopponent = opponent

    return minDistance, nearesopponent


def getDistance(x1,y1, x2, y2):
    distance = (x1-x2)**2 + (y1-y2)**2
    return distance

def get_closestally_position(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper):
    player_list = inspector.get_my_team_players()
    player_position = inspector.get_ball().position
    holder_number = inspector.get_ball().holder.number

    closest_ally = {}
    for ally in player_list:
        if ally.number != holder_number and (ally.number != 1):
            distance = getDistance(ally.position.x, ally.position.y, player_position.x, player_position.y)
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
        if getDistance(player.position.x, player.position.y, ball_position.x, ball_position.y) > getDistance(player_me.position.x, player_me.position.y, ball_position.x, ball_position.y) and player_me.number != 1:
            counter +=1
    if counter >= 8:
        return False
    else:
        return True