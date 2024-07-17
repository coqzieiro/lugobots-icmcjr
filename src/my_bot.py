import traceback  # Importa o módulo traceback para lidar com exceções
from random import randint  # Importa a função randint do módulo random
from abc import ABC  # Importa a classe ABC do módulo abc
from typing import List  # Importa o tipo de dados List do módulo typing
import lugo4py  # Importa o módulo lugo4py
from settings import get_distance_between_points, get_distance, get_closest_enemy_dist, get_closest_ally_position, Point, get_my_expected_position, has_other_closest  # Importa funções e classes do módulo settings

class MyBot(lugo4py.Bot, ABC):  # Define a classe MyBot, que herda de lugo4py.Bot e ABC
    def on_disputing(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        """
        Função chamada quando o bot está disputando a bola.
        O bot se move em direção à bola ou se posiciona conforme a expectativa.
        """
        try:
            order_list = []
            ball_position = inspector.get_ball().position
            me = inspector.get_me()
            my_position = me.position

            # Verifica a proximidade de outros jogadores
            my_team = inspector.get_my_team_players()
            opponents = inspector.get_opponent_players()

            closest_teammate = min(my_team, key=lambda player: get_distance_between_points(player.position.x, player.position.y, ball_position.x, ball_position.y) if player.number != me.number else float('inf'))
            closest_opponent = min(opponents, key=lambda player: get_distance_between_points(player.position.x, player.position.y, ball_position.x, ball_position.y))

            distance_to_ball = get_distance_between_points(my_position.x, my_position.y, ball_position.x, ball_position.y)
            distance_to_teammate = get_distance_between_points(closest_teammate.position.x, closest_teammate.position.y, ball_position.x, ball_position.y)
            distance_to_opponent = get_distance_between_points(closest_opponent.position.x, closest_opponent.position.y, ball_position.x, ball_position.y)

            # Se for o jogador mais próximo da bola, mover-se em direção à bola
            if distance_to_ball < distance_to_teammate and distance_to_ball < distance_to_opponent:
                order_list.append(inspector.make_order_move_max_speed(ball_position))
                order_list.append(inspector.make_order_catch())
            else:
                # Se um adversário estiver mais próximo da bola, tentar interceptá-lo
                if distance_to_opponent < distance_to_teammate:
                    intercept_position = Point(
                        (my_position.x + ball_position.x) / 2,
                        (my_position.y + ball_position.y) / 2
                    )
                    order_list.append(inspector.make_order_move_max_speed(intercept_position))
                else:
                    # Posicionar-se estrategicamente entre a bola e o gol adversário
                    expected_position = get_my_expected_position(inspector, self.mapper, self.number)
                    order_list.append(inspector.make_order_move_max_speed(expected_position))

            # Adiciona um comportamento para cobrir zonas específicas dependendo da posição da bola
            if ball_position.x < my_position.x:
                defensive_position = Point(my_position.x - 500, my_position.y)
                order_list.append(inspector.make_order_move_max_speed(defensive_position))
            elif ball_position.x > my_position.x:
                offensive_position = Point(my_position.x + 500, my_position.y)
                order_list.append(inspector.make_order_move_max_speed(offensive_position))

            # Verifica se a bola está em uma posição crítica perto do gol
            if ball_position.y < 1000 or ball_position.y > 7000:
                critical_position = Point(ball_position.x, 4500)
                order_list.append(inspector.make_order_move_max_speed(critical_position))

            # Adiciona um comportamento de passe para um companheiro de equipe em uma posição melhor
            if distance_to_teammate < 2000 and closest_teammate.number != me.number:
                order_list.append(inspector.make_order_kick_max_speed(closest_teammate.position))

            return order_list

        except Exception as e:
            print(f'did not play this turn due to exception {e}')
            traceback.print_exc()


    def on_defending(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:
        """
        Função chamada quando o bot está defendendo.
        O bot tenta interceptar a bola e marcar adversários.
        """
        try:  # Inicia um bloco try para lidar com exceções
            order_list = []  # Inicializa uma lista de pedidos
            distance_player1 = float('inf')  # Inicializa a distância do primeiro jogador como infinito
            distance_player2 = float('inf')  # Inicializa a distância do segundo jogador como infinito
            my_players = inspector.get_my_team_players()  # Obtém informações sobre os jogadores da própria equipe
            ball_owner = inspector.get_ball().position  # Obtém a posição do dono da bola
            ball_owner_region = self.mapper.get_region_from_point(ball_owner)  # Obtém a região do dono da bola
            players_on_ball = ["", ""]  # Inicializa uma lista para os jogadores na bola

            # Itera sobre os jogadores próprios
            for player in my_players:
                my_region = self.mapper.get_region_from_point(player.position)  # Obtém a região do jogador
                get_player_distance_from_ball = get_distance(my_region, ball_owner_region)  # Obtém a distância do jogador à bola
                # Verifica e atualiza as distâncias dos jogadores mais próximos à bola
                if get_player_distance_from_ball < distance_player1 and get_player_distance_from_ball > distance_player2:
                    distance_player1 = get_player_distance_from_ball
                    players_on_ball[0] = player.number
                elif get_player_distance_from_ball > distance_player1 and get_player_distance_from_ball < distance_player2:
                    distance_player2 = get_player_distance_from_ball
                    players_on_ball[1] = player.number
                elif get_player_distance_from_ball < distance_player1 and get_player_distance_from_ball < distance_player2:
                    if players_on_ball[0] == "":
                        distance_player1 = get_player_distance_from_ball
                        players_on_ball[0] = player.number
                    else:
                        distance_player2 = get_player_distance_from_ball
                        players_on_ball[1] = player.number

            # Se o próprio jogador estiver entre os jogadores na bola
            if self.number in players_on_ball:
                move_order = inspector.make_order_move_max_speed(ball_owner)  # Adiciona um pedido para mover na velocidade máxima em direção à bola
                order_list.append(move_order)
                catch_order = inspector.make_order_catch()  # Adiciona um pedido para tentar pegar a bola
                order_list.append(catch_order)
            else:  # Caso contrário
                my_region = self.mapper.get_region_from_point(inspector.get_me().position)  # Obtém a região do próprio jogador
                region = my_region.back()  # Obtém a região anterior à região do próprio jogador
                move_dest = region.center  # Obtém o centro da região
                move_order = inspector.make_order_move_max_speed(move_dest)  # Adiciona um pedido para mover na velocidade máxima para o centro da região anterior
                order_list.append(move_order)

            return order_list  # Retorna a lista de pedidos

        except Exception as e:  # Se ocorrer uma exceção
            print(f'did not play this turn due to exception {e}')  # Imprime uma mensagem de exceção
            traceback.print_exc()  # Imprime o rastreamento da pilha da exceção


    def on_holding(self, inspector: lugo4py.GameSnapshotInspector) -> List[lugo4py.Order]:  # Define um método on_holding que retorna uma lista de objetos Order
            try:  # Inicia um bloco try para lidar com exceções
                order_list = []  # Inicializa uma lista de pedidos

                opponent_goal_point = self.mapper.get_attack_goal()  # Obtém o ponto do gol adversário
                enemy_goal = opponent_goal_point.get_center()  # Obtém o centro do gol adversário
                goal_region = self.mapper.get_region_from_point(enemy_goal)  # Obtém a região do centro do gol adversário
                me = inspector.get_me().position  # Obtém a posição do próprio jogador
                my_region = self.mapper.get_region_from_point(me)  # Obtém a região do próprio jogador

                # Se houver um oponente perto, ele deve passar a bola para um companheiro de equipe
                closest_oponnentdis, closest_oponnent  = get_closest_enemy_dist(inspector, my_region)

                # Se estiver perto do gol adversário
                if self.is_near(my_region, goal_region):
                    goalkeeper = inspector.get_opponent_players()[0]  # Obtém o goleiro adversário
                    if (enemy_goal.x == 20000):  # Se o gol adversário estiver à direita
                        if (goalkeeper.position.y < 5000):  # Se o goleiro estiver abaixo do centro
                            target = Point(20000, 6200)  # Define um ponto alvo acima do centro
                            kick_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo
                        elif (goalkeeper.position.y > 5000):  # Se o goleiro estiver acima do centro
                            target = Point(20000, 3800)  # Define um ponto alvo abaixo do centro
                            kick_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo
                        else:  # Se o goleiro estiver no centro
                            target = Point(20000, 6200)  # Define um ponto alvo acima do centro
                            kick_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo
                    else:  # Se o gol adversário estiver à esquerda
                        if (goalkeeper.position.y < 5000):  # Se o goleiro estiver abaixo do centro
                            target = Point(0, 6200)  # Define um ponto alvo acima do centro
                            kick_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo
                        elif (goalkeeper.position.y > 5000):  # Se o goleiro estiver acima do centro
                            target = Point(0, 3800)  # Define um ponto alvo abaixo do centro
                            kick_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo
                        else:  # Se o goleiro estiver no centro
                            target = Point(0, 6200)  # Define um ponto alvo acima do centro
                            kick_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo

                    order_list.append(kick_order)  # Adiciona o pedido de chute à lista de pedidos

                else:  # Caso contrário
                    if (closest_oponnentdis < 800000):  # Se houver um oponente perto
                        ord_ally_posi = get_closest_ally_position(inspector, my_region)  # Obtém a posição dos aliados mais próximos

                        # Percorre os aliados mais próximos e passa para o mais avançado
                        pass_order = None
                        minimun_distance = 800000
                        for ally_list in ord_ally_posi.values():
                            counter = 0
                            for ally in ally_list:
                                counter += 1
                                if (enemy_goal.x == 20000):
                                    if ally.position.x > me.x and get_distance(me.x, me.y, ally.position.x, ally.position.y) > minimun_distance:
                                        pass_order = inspector.make_order_kick_max_speed(ally.position)
                                        break
                                elif (enemy_goal.x == 0):
                                    if ally.position.x < me.x and get_distance(me.x, me.y, ally.position.x, ally.position.y) > minimun_distance:
                                        pass_order = inspector.make_order_kick_max_speed(ally.position)
                                        break
                                if counter == 5:
                                    break

                        if pass_order is None:
                            # Percorre os aliados mais próximos novamente para encontrar o primeiro que esteja com uma distância maior que 10000
                            for ally_list in ord_ally_posi.values():
                                for ally in ally_list:
                                    if get_distance(me.x, me.y, ally.position.x, ally.position.y) > minimun_distance and ally.number != 0:
                                        move_order = inspector.make_order_move_max_speed(ally.position)
                                        pass_order = inspector.make_order_kick_max_speed(ally.position)
                                        order_list.append(move_order)
                                        order_list.append(pass_order)
                                        break
                                if pass_order is not None:
                                    break

                        if pass_order is None:
                            # Passa para uma posição aleatória caso não exista aliado com uma distância mínima
                            enemy_goal = opponent_goal_point.get_center()
                            if (enemy_goal.x == 20000):
                                x = randint(me.x + 1, 20000)
                                y = randint(3500,6500)
                                target = Point(x, y)
                                pass_order = inspector.make_order_kick(target, 250)
                            else:
                                x = randint(0, me.x - 1)
                                y = randint(3500,6500)
                                target = Point(x, y)
                                pass_order = inspector.make_order_kick(target, 250)

                        order_list.append(pass_order)  # Adiciona o pedido de passe à lista de pedidos

                move_order = inspector.make_order_move_max_speed(self.mapper.get_attack_goal().get_center())  # Adiciona um pedido para mover na velocidade máxima para o centro do gol adversário
                order_list.append(move_order)  # Adiciona o pedido de movimento à lista de pedidos

                return order_list  # Retorna a lista de pedidos

            except Exception as e:  # Se ocorrer uma exceção
                print(f'did not play this turn due to exception. {e}')  # Imprime uma mensagem de exceção
                traceback.print_exc()  # Imprime o rastreamento da pilha da exceção


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
            order_list = []
            me = inspector.get_me()
            my_position = me.position
            ball_position = inspector.get_ball().position
            my_team = inspector.get_my_team_players()
            opponents = inspector.get_opponent_players()
            
            # Posição esperada com base na tática
            expected_position = get_my_expected_position(inspector, self.mapper, self.number)
            
            # Analisando a situação do jogo
            closest_teammate = min(my_team, key=lambda player: get_distance_between_points(player.position.x, player.position.y, ball_position.x, ball_position.y))
            closest_opponent = min(opponents, key=lambda player: get_distance_between_points(player.position.x, player.position.y, ball_position.x, ball_position.y))
            
            distance_to_ball = get_distance_between_points(my_position.x, my_position.y, ball_position.x, ball_position.y)
            distance_to_teammate = get_distance_between_points(closest_teammate.position.x, closest_teammate.position.y, ball_position.x, ball_position.y)
            distance_to_opponent = get_distance_between_points(closest_opponent.position.x, closest_opponent.position.y, ball_position.x, ball_position.y)
            
            # Posicionamento defensivo se o adversário estiver próximo da bola
            if distance_to_opponent < distance_to_teammate:
                defensive_position = Point(
                    (my_position.x + ball_position.x) / 2,
                    (my_position.y + ball_position.y) / 2
                )
                order_list.append(inspector.make_order_move_max_speed(defensive_position))
            
            # Posicionamento ofensivo se a equipe estiver com a posse da bola
            elif distance_to_teammate < distance_to_opponent:
                offensive_position = Point(
                    (my_position.x + expected_position.x) / 2,
                    (my_position.y + expected_position.y) / 2
                )
                order_list.append(inspector.make_order_move_max_speed(offensive_position))
            
            # Movimentação para cobrir zonas críticas do campo
            if ball_position.y < 1000 or ball_position.y > 7000:
                critical_position = Point(ball_position.x, 4500)
                order_list.append(inspector.make_order_move_max_speed(critical_position))
            
            # Suporte ao jogador mais próximo da bola
            if distance_to_teammate < 2000:
                support_position = Point(
                    closest_teammate.position.x + 500,
                    closest_teammate.position.y
                )
                order_list.append(inspector.make_order_move_max_speed(support_position))
            
            # Movimentação para a posição esperada conforme a tática
            move_order = inspector.make_order_move_max_speed(expected_position)
            order_list.append(move_order)
            
            return order_list

        except Exception as e:
            print(f'did not play this turn due to exception {e}')
            traceback.print_exc()

    def as_goalkeeper(self, inspector: lugo4py.GameSnapshotInspector, state: lugo4py.PLAYER_STATE) -> List[lugo4py.Order]:  # Define um método as_goalkeeper que retorna uma lista de objetos Order
        try:  # Inicia um bloco try para lidar com exceções
            order_list = []  # Inicializa uma lista de pedidos
            ball_position = inspector.get_ball().position  # Obtém a posição da bola
            me = inspector.get_me()  # Obtém informações sobre o próprio jogador
            me_positon = inspector.get_me().position  # Obtém a posição do próprio jogador
            my_region = self.mapper.get_region_from_point(me_positon)  # Obtém a região do próprio jogador
            goalkeeper_position = inspector.get_my_team_goalkeeper().position.x  # Obtém a posição do goleiro próprio
            opponent_goal_point = self.mapper.get_attack_goal()  # Obtém o ponto do gol adversário
            enemy_goal = opponent_goal_point.get_center()  # Obtém o centro do gol adversário

            # Determina a posição dependendo do estado do jogador
            if state == lugo4py.PLAYER_STATE.DEFENDING:  # Se estiver defendendo
                position = ball_position  # A posição é a da bola
            elif state == lugo4py.PLAYER_STATE.HOLDING_THE_BALL:  # Se estiver com a bola
                position = self.mapper.get_attack_goal().get_center()  # A posição é o centro do gol adversário
                closest_allypos = get_closest_ally_position(inspector, my_region)  # Obtém a posição dos aliados mais próximos
                first_ally_position = list(closest_allypos.values())[0][0].position  # Obtém a posição do primeiro aliado mais próximo
                pass_order = None  # Inicializa um pedido de passe como None
                if (enemy_goal.x == 20000):  # Se o gol adversário estiver à direita
                    target = Point(1221, 414)  # Define um ponto alvo
                    pass_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo
                else:  # Se o gol adversário estiver à esquerda
                    target = Point(18773, 414)  # Define um ponto alvo
                    pass_order = inspector.make_order_kick_max_speed(target)  # Adiciona um pedido para chutar a bola na velocidade máxima para o ponto alvo

                order_list.append(pass_order)  # Adiciona o pedido de passe à lista de pedidos

            else:  # Caso contrário
                position = ball_position  # A posição é a da bola
            if ball_position.x <= 1300 and ((ball_position.y - me.position.y) > 2000):  # Se a bola estiver dentro da área e acima do jogador
                move_order = inspector.make_order_jump(position, 200)  # Adiciona um pedido para saltar
            else:  # Caso contrário
                if position.y > self.mapper.get_defense_goal().get_top_pole().y:  # Se a bola estiver acima do poste superior do gol próprio
                    position = Point(goalkeeper_position, 5600)  # A posição é ajustada para o meio da parte superior do gol
                elif position.y < self.mapper.get_defense_goal().get_bottom_pole().y:  # Se a bola estiver abaixo do poste inferior do gol próprio
                    position = Point(goalkeeper_position, 4400)  # A posição é ajustada para o meio da parte inferior do gol

                move_order = inspector.make_order_jump(position, 200)  # Adiciona um pedido para saltar para a posição
            order_list.append(move_order)  # Adiciona o pedido de movimento à lista de pedidos
            order_list.append(inspector.make_order_catch())  # Adiciona um pedido para tentar pegar a bola à lista de pedidos

            return order_list  # Retorna a lista de pedidos

        except Exception as e:  # Se ocorrer uma exceção
            print(f'did not play this turn due to exception {e}')  # Imprime uma mensagem de exceção
            traceback.print_exc()  # Imprime o rastreamento da pilha da exceção
            
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