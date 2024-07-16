import traceback  # Importa o módulo traceback para lidar com exceções
from random import randint  # Importa a função randint do módulo random
from abc import ABC  # Importa a classe ABC do módulo abc
from typing import List  # Importa o tipo de dados List do módulo typing
import lugo4py  # Importa o módulo lugo4py
from settings import get_distance, get_closest_enemy_dist, get_closest_ally_position, Point, get_my_expected_position, has_other_closest  # Importa funções e classes do módulo settings

class MyBot(lugo4py.Bot, ABC):  # Define a classe MyBot, que herda de lugo4py.Bot e ABC
    def on_disputing(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        """
        Função chamada quando o bot está disputando a bola.
        O bot se move em direção à bola ou se posiciona conforme a expectativa.
        """
        try:
            order_list = []  # Inicializa a lista de pedidos de ação para o bot
            ball_position = inspector.get_ball().position  # Obtém a posição atual da bola
            me = inspector.get_me()  # Obtém uma referência ao próprio bot

            if not has_other_closest(inspector, me):  # Verifica se o bot é o mais próximo da bola
                order_list.append(inspector.make_order_move_max_speed(ball_position))  # Adiciona pedido para mover em direção à bola na velocidade máxima
                order_list.append(inspector.make_order_catch())  # Adiciona pedido para tentar capturar a bola
            else:
                expected_position = get_my_expected_position(inspector, self.mapper, self.number)  # Obtém a posição esperada do bot
                order_list.append(inspector.make_order_move_max_speed(expected_position))  # Adiciona pedido para mover para a posição esperada na velocidade máxima

            return order_list  # Retorna a lista de pedidos

        except Exception as e:
            print(f'did not play this turn due to exception {e}')  # Imprime a exceção
            traceback.print_exc()  # Imprime o rastreamento da pilha de exceções

    def on_defending(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        """
        Função chamada quando o bot está defendendo.
        O bot tenta interceptar a bola e marcar adversários.
        """
        try:
            order_list = []  # Inicializa a lista de pedidos de ação para o bot
            distance_player1 = float('inf')  # Inicializa a maior distância do jogador 1 como infinito
            distance_player2 = float('inf')  # Inicializa a maior distância do jogador 2 como infinito
            my_players = inspector.get_my_team_players()  # Obtém a lista de jogadores do próprio time
            ball_owner = inspector.get_ball().position  # Obtém a posição do jogador com a bola
            ball_owner_region = self.mapper.get_region_from_point(ball_owner)  # Obtém a região da bola
            players_on_ball = ["", ""]  # Inicializa a lista de jogadores mais próximos da bola

            # Encontra os dois jogadores mais próximos da bola
            for player in my_players:
                my_region = self.mapper.get_region_from_point(player.position)  # Obtém a região do jogador
                get_player_distance_from_ball = get_distance(my_region, ball_owner_region)  # Calcula a distância do jogador até a bola
                if get_player_distance_from_ball < distance_player1 and get_player_distance_from_ball > distance_player2:
                    distance_player1 = get_player_distance_from_ball  # Atualiza a distância do jogador 1
                    players_on_ball[0] = player.number  # Atualiza o número do jogador 1
                elif get_player_distance_from_ball > distance_player1 and get_player_distance_from_ball < distance_player2:
                    distance_player2 = get_player_distance_from_ball  # Atualiza a distância do jogador 2
                    players_on_ball[1] = player.number  # Atualiza o número do jogador 2
                elif get_player_distance_from_ball < distance_player1 and get_player_distance_from_ball < distance_player2:
                    if players_on_ball[0] == "":
                        distance_player1 = get_player_distance_from_ball  # Atualiza a distância do jogador 1
                        players_on_ball[0] = player.number  # Atualiza o número do jogador 1
                    else:
                        distance_player2 = get_player_distance_from_ball  # Atualiza a distância do jogador 2
                        players_on_ball[1] = player.number  # Atualiza o número do jogador 2

            if self.number in players_on_ball:  # Se o bot é um dos jogadores mais próximos da bola
                move_order = inspector.make_order_move_max_speed(ball_owner)  # Move em direção à bola na velocidade máxima
                order_list.append(move_order)
                catch_order = inspector.make_order_catch()  # Tenta capturar a bola
                order_list.append(catch_order)
            else:
                my_region = self.mapper.get_region_from_point(inspector.get_me().position)  # Obtém a região atual do bot
                region = my_region.back()  # Move para a região defensiva
                move_dest = region.center  # Centro da região defensiva
                move_order = inspector.make_order_move_max_speed(move_dest)  # Move para a posição defensiva na velocidade máxima
                order_list.append(move_order)

            return order_list  # Retorna a lista de pedidos

        except Exception as e:
            print(f'did not play this turn due to exception {e}')  # Imprime a exceção
            traceback.print_exc()  # Imprime o rastreamento da pilha de exceções

    def on_holding(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        """
        Função chamada quando o bot está com a bola.
        O bot decide entre passar, chutar ou driblar.
        """
        try:
            order_list = []  # Inicializa a lista de pedidos de ação para o bot

            opponent_goal_point = self.mapper.get_attack_goal()  # Obtém a posição do gol adversário
            enemy_goal = opponent_goal_point.get_center()  # Obtém o centro do gol adversário
            me = inspector.get_me().position  # Obtém a posição do próprio bot
            my_region = self.mapper.get_region_from_point(me)  # Obtém a região do próprio bot

            closest_opponent_dist, closest_opponent = get_closest_enemy_dist(inspector, my_region)  # Obtém a distância e posição do oponente mais próximo

            # Adiciona um desvio lateral antes de tomar ações para tornar a movimentação menos previsível
            lateral_move = Point(me.x + 100 if randint(0, 1) == 0 else me.x - 100, me.y)
            order_list.append(inspector.make_order_move_max_speed(lateral_move))

            # Após o desvio, decide entre passar ou chutar
            if closest_opponent_dist < 800:  # Oponente próximo
                closest_ally_position, closest_ally = self.get_closest_ally(inspector)
                if closest_ally:
                    pass_order = inspector.make_order_pass(closest_ally.position)  # Passa para o aliado mais próximo
                    order_list.append(pass_order)
                else:
                    # Chuta no gol se nenhum aliado estiver disponível
                    kick_order = inspector.make_order_kick_max_speed(Point(enemy_goal.x, enemy_goal.y))
                    order_list.append(kick_order)
            else:
                # Chuta diretamente para o gol se não houver pressão imediata
                kick_order = inspector.make_order_kick_max_speed(Point(enemy_goal.x, enemy_goal.y))
                order_list.append(kick_order)

            return order_list  # Retorna a lista de pedidos

        except Exception as e:
            print(f'did not play this turn due to exception {e}')  # Imprime a exceção
            traceback.print_exc()  # Imprime o rastreamento da pilha de exceções

    def get_closest_ally(self, inspector):
        """
        Função auxiliar para encontrar o aliado mais próximo do bot, excluindo o goleiro.
        """
        me = inspector.get_me()  # Obtém a referência ao próprio bot
        allies = inspector.get_my_team_players()  # Obtém a lista de jogadores do próprio time
        min_distance = float('inf')  # Inicializa a menor distância como infinito
        closest_ally = None  # Inicializa a referência ao aliado mais próximo como None

        for ally in allies:
            if ally.number == me.number or ally.role == 'goalkeeper':  # Exclui o próprio bot e o goleiro
                continue
            distance = get_distance(me.position, ally.position)  # Calcula a distância entre o bot e o aliado
            if distance < min_distance:
                min_distance = distance  # Atualiza a menor distância
                closest_ally = ally  # Atualiza a referência ao aliado mais próximo

        return closest_ally.position, closest_ally if closest_ally else None  # Retorna a posição e a referência ao aliado mais próximo

    def on_supporting(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        """
        Função chamada quando o bot está apoiando a jogada.
        O bot se move para a posição esperada conforme a tática.
        """
        try:
            move_dest = get_my_expected_position(inspector, self.mapper, self.number)  # Obtém a posição esperada do próprio jogador
            move_order = inspector.make_order_move_max_speed(move_dest)  # Adiciona um pedido para mover na velocidade máxima para a posição esperada
            return [move_order]  # Retorna a lista de pedidos

        except Exception as e:
            print(f'did not play this turn due to exception {e}')  # Imprime a exceção
            traceback.print_exc()  # Imprime o rastreamento da pilha de exceções

    def as_goalkeeper(self, inspector: lugo4py.GameSnapshotInspector, state: lugo4py.PLAYER_STATE) -> List[lugo4py.Order]:
        """
        Função chamada quando o bot está jogando como goleiro.
        O bot se posiciona para defender e, se possível, chuta para o lado oposto da chegada da bola.
        """
        try:
            order_list = []  # Inicializa uma lista de pedidos
            ball_position = inspector.get_ball().position  # Obtém a posição da bola
            me = inspector.get_me()  # Obtém informações sobre o próprio jogador
            me_position = inspector.get_me().position  # Obtém a posição do próprio jogador
            my_region = self.mapper.get_region_from_point(me_position)  # Obtém a região do próprio jogador
            goalkeeper_position = inspector.get_my_team_goalkeeper().position.x  # Obtém a posição do goleiro próprio
            opponent_goal_point = self.mapper.get_attack_goal()  # Obtém o ponto do gol adversário
            enemy_goal = opponent_goal_point.get_center()  # Obtém o centro do gol adversário

            # Goleiro se move para seguir a posição da bola
            new_position = Point(goalkeeper_position, ball_position.y)
            move_order = inspector.make_order_move_max_speed(new_position)  # Adiciona um pedido para mover na velocidade máxima para a nova posição
            order_list.append(move_order)

            if state == lugo4py.PLAYER_STATE.HOLDING_THE_BALL:  # Se estiver com a bola
                # Chuta para o sentido oposto de onde a bola está vindo
                if ball_position.x < 10000:  # Se a bola está na metade esquerda do campo
                    target = Point(20000, 4500)  # Chuta para a metade direita
                else:  # Se a bola está na metade direita do campo
                    target = Point(0, 4500)  # Chuta para a metade esquerda
                pass_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar na velocidade máxima para o alvo
                order_list.append(pass_order)
            else:
                if ball_position.x <= 1300 and abs(ball_position.y - me_position.y) > 2000:  # Se a bola estiver perto e acima do jogador
                    move_order = inspector.make_order_jump(new_position, 200)  # Adiciona um pedido para saltar
                    order_list.append(move_order)
                else:
                    catch_order = inspector.make_order_catch()  # Adiciona um pedido para tentar pegar a bola
                    order_list.append(catch_order)

            return order_list  # Retorna a lista de pedidos

        except Exception as e:
            print(f'did not play this turn due to exception {e}')  # Imprime a exceção
            traceback.print_exc()  # Imprime o rastreamento da pilha de exceções

    def get_optimal_goalkeeper_position(self, ball_position, me):
        """
        Ajusta a posição vertical do goleiro baseado na posição da bola para melhor cobertura do gol.
        """
        if ball_position.y < me.position.y:
            return max(ball_position.y, self.mapper.get_defense_goal().get_bottom_pole().y + 200)  # Mantém uma margem acima do poste inferior
        else:
            return min(ball_position.y, self.mapper.get_defense_goal().get_top_pole().y - 200)  # Mantém uma margem abaixo do poste superior

    def get_kick_direction(self, ball_position, enemy_goal):
        """
        Chuta para o lado oposto ao movimento da bola.
        """
        if ball_position.y > enemy_goal.y:
            return Point(enemy_goal.x, enemy_goal.y - 500)  # Chute para o canto inferior do gol adversário
        else:
            return Point(enemy_goal.x, enemy_goal.y + 500)  # Chute para o canto superior do gol adversário

    def should_jump(self, ball_position, goalkeeper_position):
        """
        Decide se o goleiro deve pular baseado na proximidade e direção da bola.
        """
        return abs(ball_position.y - goalkeeper_position.y) > 1000  # Pula se a bola estiver a uma distância significativa na vertical

    def getting_ready(self, snapshot: lugo4py.GameSnapshot):
        """
        Método chamado quando o bot está se preparando para o jogo.
        """
        print('getting ready')  # Imprime uma mensagem indicando que o jogador está se preparando

    def is_near(self, region_origin: lugo4py.mapper.Region, dest_origin: lugo4py.mapper.Region) -> bool:
        """
        Verifica se duas regiões estão próximas.
        """
        max_distance = 1  # Define a distância máxima
        return abs(region_origin.get_row() - dest_origin.get_row()) <= max_distance and abs(  # Retorna True se a diferença entre as linhas for menor ou igual à distância máxima e a diferença entre as colunas for menor ou igual à distância máxima
            region_origin.get_col() - dest_origin.get_col()) <= max_distance
