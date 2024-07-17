import lugo4py  # Importa o módulo lugo4py para interagir com os elementos de simulação Lugo
import lugo4py.mapper as mapper  # Importa utilidades de mapeamento do lugo4py
import math  # Importa o módulo math para operações matemáticas, como raiz quadrada

# Constantes que definem o número de colunas e linhas no mapeador do jogo
MAPPER_COLS = 10
MAPPER_ROWS = 6

def get_my_expected_position(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper, number: int):
    """
    Calcula a posição esperada no campo para um jogador com base no estado atual do jogo.

    Args:
    - inspector: Fornece acesso às informações do estado do jogo.
    - my_mapper: Fornece utilidades de mapeamento para o campo do jogo.
    - number: O número do jogador cuja posição será calculada.

    Returns:
    - Um ponto representando a posição esperada no campo.
    """
    # Define posições táticas para os jogadores dependendo da estratégia da equipe (Defensiva, Normal, Ofensiva, Ataque)
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
    """
    Calcula a distância Euclidiana entre duas regiões no campo.

    Args:
    - r1: Primeira região
    - r2: Segunda região

    Returns:
    - A distância entre as duas regiões.
    """
    return math.sqrt((r2.get_col() - r1.get_col())**2 + (r1.get_row() - r2.get_row())**2)

def get_closest_ally_position(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper):
    """
    Calcula e retorna as posições dos aliados mais próximos à bola, exceto o goleiro e o jogador que está com a posse da bola.

    Args:
    - inspector (lugo4py.GameSnapshotInspector): Um objeto que fornece acesso ao estado atual do jogo, incluindo jogadores e a bola.
    - my_mapper (mapper.Mapper): Um objeto que fornece funcionalidades de mapeamento do campo de jogo.

    Returns:
    - dict: Um dicionário onde as chaves são distâncias da bola até cada aliado. 
    """
    player_list = inspector.get_my_team_players()
    player_position = inspector.get_ball().position
    holder_number = inspector.get_ball().holder.number

    closest_ally = {}
    for ally in player_list:
        if ally.number != holder_number and (ally.number != 1):
            distance = get_distance(ally.position.x, ally.position.y, player_position.x, player_position.y)
            if distance not in closest_ally:
                closest_ally[distance] = [ally]
            else:
                closest_ally[distance].append(ally)

    closest_ally = dict(sorted(closest_ally.items(), key=lambda x: x[0]))

    return closest_ally

def get_closest_enemy_dist(inspector: lugo4py.GameSnapshotInspector, my_mapper: mapper.Mapper):
    """
    Determina o jogador inimigo mais próximo da bola e a distância até esse jogador.

    Args:
    - inspector: Fornece acesso às informações do estado do jogo.
    - my_mapper: Fornece utilidades de mapeamento para o campo do jogo.

    Returns:
    - Tupla contendo a distância mínima até o inimigo mais próximo e o objeto do jogador inimigo.
    """
    player_position = inspector.get_ball().position
    opponents = inspector.get_opponent_players()

    nearest_opponent = None
    min_distance = math.inf  # Inicia com infinito para garantir que qualquer distância real seja menor
    for opponent in opponents:
        current_distance = get_distance_between_points(player_position.x, player_position.y, opponent.position.x, opponent.position.y)
        if current_distance < min_distance:
            min_distance = current_distance
            nearest_opponent = opponent

    return min_distance, nearest_opponent  # Retorna a distância e o oponente

def get_distance_between_points(x1, y1, x2, y2):
    """
    Calcula a distância Euclidiana entre dois pontos.

    Args:
    - x1, y1: Coordenadas do primeiro ponto.
    - x2, y2: Coordenadas do segundo ponto.

    Returns:
    - A distância entre os dois pontos.
    """
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

class Point:
    """
    Representa um ponto no campo.

    Atributos:
    - x (int): A coordenada x do ponto.
    - y (int): A coordenada y do ponto.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point(x={self.x}, y={self.y})"

def has_other_closest(inspector: lugo4py.GameSnapshotInspector, player_me):
    """
    Determina se há menos de cinco jogadores mais próximos à bola do que o jogador atual.

    Args:
    - inspector: Fornece acesso às informações do estado do jogo.
    - player_me: O jogador atual sendo considerado.
    """
    counter = 0
    players = inspector.get_my_team_players()
    ball_position = inspector.get_ball().position
    for player in players:
        if get_distance(player.position.x, player.position.y, ball_position.x, ball_position.y) > get_distance(player_me.position.x, player_me.position.y, ball_position.x, ball_position.y) and player_me.number != 1:
            counter +=1
    if counter >= 4:
        return False
    else:
        return True
