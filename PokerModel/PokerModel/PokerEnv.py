from .Player import Player
from treys import Deck, Evaluator, Card
from .Enums import Position, Action
import numpy as np
import math

INITIAL_STACK_SIZE = 100
SMALL_BLIND = 1
BIG_BLIND = 2


class PokerEnv():

    def __init__(self):
        self.pot = None
        self.community_cards = None
        self.evaluator = None
        self.deck = None
        # self.cards_dictionary = self.create_cards_dictionary()
        self.player = None
        self.opponent = None
        self.reset()

    def reset(self):
        self.deck = Deck()
        self.evaluator = Evaluator()
        self.player = Player(INITIAL_STACK_SIZE, False)
        self.opponent = Player(INITIAL_STACK_SIZE, True)
        self.reset_board()

    def reset_board(self):
        self.deck = Deck()
        self.community_cards = []
        self.player.total_bet = 0
        self.opponent.total_bet = 0
        self.player.previous_bet = 0
        self.opponent.previous_bet = 0
        self.player.is_fold = False
        self.opponent.is_fold = False
        self.pot = 0
        if self.player.is_small_blind:
            self.player.is_small_blind = False
            self.player.position = Position.BIG_BLIND
            self.opponent.is_small_blind = True
            self.opponent.position = Position.SMALL_BLIND
            self.pot += self.player.place_bet(BIG_BLIND)
            self.pot += self.opponent.place_bet(SMALL_BLIND)
        else:
            self.player.is_small_blind = True
            self.player.position = Position.SMALL_BLIND
            self.opponent.is_small_blind = False
            self.opponent.position = Position.BIG_BLIND
            self.pot += self.player.place_bet(SMALL_BLIND)
            self.pot += self.opponent.place_bet(BIG_BLIND)
        self.player.already_played = False
        self.opponent.already_played = False
        self.deal_hole_cards()

    def deal_hole_cards(self):
        self.player.receive_cards(self.deck.draw(2))
        self.opponent.receive_cards(self.deck.draw(2))

    def deal_community_cards(self, count):
        self.community_cards.extend(self.deck.draw(count))

    def is_game_over(self):
        if self.player.stack_size < BIG_BLIND and not self.player.already_played:
            return True
        if self.opponent.stack_size < BIG_BLIND and not self.opponent.already_played:
            return True
        return False

    def is_first_player_won(self):
        if self.opponent.is_fold:
            return True
        if self.player.is_fold:
            return False
        player_score = self.evaluator.evaluate(self.community_cards, self.player.get_hand())
        opponent_score = self.evaluator.evaluate(self.community_cards, self.opponent.get_hand())
        if player_score <= opponent_score:
            return True
        else:  # need to deal with tie
            return False

    def is_stage_ready(self):
        # check if both players execute action
        if not self.player.already_played or not self.opponent.already_played:
            return False
        if self.player.total_bet != self.opponent.total_bet:
            return False
        # check check
        if self.player.position == Position.CHECK and self.opponent.position == Position.CHECK:
            return True
        # raise call
        if (self.player.position == Position.RAISE and self.opponent.position == Position.CALL) or \
                (self.player.position == Position.CALL and self.opponent.position == Position.RAISE):
            return True
        # small call big checks
        if (self.player.position == Position.CHECK and self.opponent.position == Position.CALL) or (
                self.player.position == Position.CALL and self.opponent.position == Position.CHECK):
            return True
        return False

    def is_hand_over(self):
        if self.player.is_fold or self.opponent.is_fold:
            return True
        if len(self.community_cards) == 5 and self.player.already_played and self.opponent.already_played:
            if (self.player.position == Position.CHECK and self.opponent.position == Position.CHECK) or \
                    (
                            self.player.position == Position.CALL and self.opponent.position == Position.RAISE) or \
                    (self.player.position == Position.RAISE and self.opponent.position == Position.CALL):
                return True
        return False

    def update_board(self):
        cards_on_board = len(self.community_cards)
        if cards_on_board == 0:
            self.deal_community_cards(3)
        if cards_on_board == 3:
            self.deal_community_cards(1)
        if cards_on_board == 4:
            self.deal_community_cards(1)
        self.player.already_played = False
        self.opponent.already_played = False

    def update_all_in_stage(self):
        for i in range(3):
            self.update_board()
        self.player.already_played = True
        self.opponent.already_played = True

    def update_stage(self):
        if self.is_stage_ready():
            self.update_board()

    def perform_player_action(self, cur_player, other_player, action):
        final_action = None
        if action == Action.FOLD.value:
            final_action = self.perform_fold(cur_player)
        if action == Action.CHECK_CALL.value:
            final_action = self.perform_call(cur_player, other_player)
        if action == Action.RAISE_BIG_BLIND.value:
            final_action = self.perform_raise_big_blind(cur_player, other_player)
        if action == Action.RAISE_HALF_POT.value:
            final_action = self.perform_raise_half_pot(cur_player, other_player)
        if action == Action.RAISE_POT.value:
            final_action = self.perform_raise_pot(cur_player, other_player)
        if action == Action.RAISE_TWO_POT.value:
            final_action = self.perform_raise_two_pot(cur_player, other_player)
        return final_action

    def perform_fold(self, cur_player):
        cur_player.is_fold = True
        return Action.FOLD

    def perform_check(self, cur_player, other_player):
        if cur_player.total_bet != other_player.total_bet:
            return self.perform_call(cur_player, other_player)
        cur_player.position = Position.CHECK
        return Action.CHECK_CALL

    def perform_call(self, cur_player, other_player):
        amount = other_player.total_bet - cur_player.total_bet
        if amount == 0:
            return self.perform_check(cur_player, other_player)
        self.pot += cur_player.place_bet(int(amount))
        cur_player.position = Position.CALL
        if cur_player.total_bet != other_player.total_bet:
            pot_change = other_player.total_bet - cur_player.total_bet
            self.pot -= pot_change
            other_player.stack_size += pot_change
            other_player.total_bet -= pot_change
        return Action.CHECK_CALL

    def perform_raise_big_blind(self, cur_player, other_player):
        amount = other_player.total_bet - cur_player.total_bet
        if amount >= cur_player.stack_size:
            return self.perform_call(cur_player, other_player)
        if amount == 0:
            bet_amount = BIG_BLIND
        else:
            bet_amount = amount * 2
        if other_player.stack_size < bet_amount:
            bet_amount = other_player.stack_size + amount
        if cur_player.stack_size < bet_amount:
            return self.perform_call(cur_player, other_player)
        else:
            self.pot += cur_player.place_bet(int(bet_amount))
            cur_player.position = Position.RAISE
            return Action.RAISE_BIG_BLIND

    def perform_raise_half_pot(self, cur_player, other_player):
        amount = other_player.total_bet - cur_player.total_bet
        if amount >= cur_player.stack_size:
            return self.perform_call(cur_player, other_player)
        if amount == 0:
            bet_amount = math.ceil(self.pot / 2.0)
        else:
            bet_amount = amount + self.pot // 2
        if other_player.stack_size < bet_amount:
            bet_amount = other_player.stack_size + amount
        if cur_player.stack_size < bet_amount:
            return self.perform_call(cur_player, other_player)
        else:
            self.pot += cur_player.place_bet(int(bet_amount))
            cur_player.position = Position.RAISE
            return Action.RAISE_HALF_POT

    def perform_raise_pot(self, cur_player, other_player):
        amount = other_player.total_bet - cur_player.total_bet
        if amount >= cur_player.stack_size:
            return self.perform_call(cur_player, other_player)
        if amount == 0:
            bet_amount = self.pot
        else:
            bet_amount = amount + self.pot
        if other_player.stack_size < bet_amount:
            bet_amount = other_player.stack_size + amount
        if cur_player.stack_size < bet_amount:
            return self.perform_call(cur_player, other_player)
        else:
            self.pot += cur_player.place_bet(int(bet_amount))
            cur_player.position = Position.RAISE
            return Action.RAISE_POT

    def perform_raise_two_pot(self, cur_player, other_player):
        amount = other_player.total_bet - cur_player.total_bet
        if amount >= cur_player.stack_size:
            return self.perform_call(cur_player, other_player)
        if amount == 0:
            bet_amount = self.pot * 2
        else:
            bet_amount = amount + self.pot * 2
        if other_player.stack_size < bet_amount:
            bet_amount = other_player.stack_size + amount
        if cur_player.stack_size < bet_amount:
            return self.perform_call(cur_player, other_player)
        else:
            self.pot += cur_player.place_bet(int(bet_amount))
            cur_player.position = Position.RAISE
            return Action.RAISE_TWO_POT

    def execute_player_action(self, cur_player, other_player, action):
        final_action = ""
        wining_env = ""
        if self.check_if_playable(cur_player, other_player):
                final_action = self.perform_player_action(cur_player, other_player, action).name
                cur_player.already_played = True
        if cur_player.stack_size == 0:
            if cur_player.position == Position.CALL:
                self.update_all_in_stage()
        if self.is_hand_over():
            if self.is_first_player_won():
                self.player.stack_size += self.pot
                wining_env = self.full_print() + "\nplayer won"
            else:
                self.opponent.stack_size += self.pot
                wining_env += self.full_print() + "\nopponent won"
            self.reset_board()
        else:
            self.update_stage()
        return self.is_game_over(), final_action,  wining_env

    # def check_if_playable(self, cur_player, other_player):
    #     if not cur_player.already_played and not other_player.already_played and not cur_player.is_small_blind:
    #         return False
    #     else:
    #         return True

    def check_if_playable(self, cur_player, other_player):
        if not cur_player.already_played and not other_player.already_played and not cur_player.is_small_blind:
            return False
        if cur_player.already_played and not other_player.already_played:
            return False
        if cur_player.already_played and other_player.already_played:
            if cur_player.total_bet < other_player.total_bet:
                return True
            else:
                return False
        if not cur_player.already_played and other_player.already_played:
            return True
        if cur_player.already_played and not other_player.already_played:
            return False
        else:
            return True

    def get_player_valid_actions(self, other_player):
        if other_player.already_played:
            if other_player.position == Position.CHECK or other_player.position == Position.CALL:
                valid_actions = [1, 2, 3, 4, 5]
            else:
                valid_actions = [0, 1, 2, 3, 4, 5]
        else:
            valid_actions = [1, 2, 3, 4, 5]
        return valid_actions

    def full_print(self):
        s = \
            "community cards:" + self.cards_print(self.community_cards) + "\n" + \
            "player cards:" + self.cards_print(self.player.get_hand()) + "\n" + \
            "opponent cards:" + self.cards_print(self.opponent.get_hand()) + "\n"
        return s

    def status_print(self):
        return "player position: {} , opponent position: {}, pot: {}, player bet: {}, opponent bet:" \
               " {}, cards on deck: {}, player stack: {}, opponent stack: {} total:{}" \
            .format(self.player.position.name, self.opponent.position.name, \
                    self.pot, self.player.total_bet, self.opponent.total_bet, len(self.community_cards), \
                    self.player.stack_size, self.opponent.stack_size, \
                    self.player.stack_size + self.opponent.stack_size + self.pot)

    def cards_print(self, cards):
        s = ""
        if len(cards) != 0:
            for card in cards[:-1]:
                s += Card.int_to_pretty_str(card) + ","
            s += Card.int_to_pretty_str(cards[-1])
        return s

    def calculate_reward(self):
        if self.is_hand_over():
            if self.is_first_player_won():
                return self.opponent.total_bet + self.player.total_bet
            else:
                return -(self.player.total_bet - self.player.previous_bet)
        else:
            return -(self.player.total_bet - self.player.previous_bet)

    def calculate_reward(self):
        if self.is_hand_over():
            if self.is_first_player_won():
                return self.opponent.total_bet
            else:
                return -self.player.total_bet
        else:
            return 0