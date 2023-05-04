from .PokerEnv import *
from tensorflow import keras
import numpy as np


def get_other_player_action(pokerEnv, model, cards_dictionary, cur_player, other_player):
    valid_actions = pokerEnv.get_player_valid_actions(other_player=other_player)
    # return np.random.choice(valid_actions)
    observation = get_observation(pokerEnv, cards_dictionary,  cur_player, other_player)
    other_player_observation = np.array([observation.reshape(1, -1)])
    q_values = model.predict(other_player_observation, verbose=0)
    mask = np.ones(model.output_shape[1])
    mask[valid_actions] = 0
    masked_q_values = q_values - (mask * 1e9)
    # Choose action with highest Q-value among valid actions
    action = np.argmax(masked_q_values)
    return action

def get_observation(pokerEnv,cards_dictionary, cur_player, other_player):
    # Convert the player's hand into one-hot encoded representation
    hand_observation = get_cards_representation(cards_dictionary, cur_player.get_hand(), 2)

    # Convert the player's hand into one-hot encoded representation
    positions_observation = get_position_representation(cur_player, other_player)

    # Convert the community cards into one-hot encoded representation
    community_cards_observation = get_cards_representation(cards_dictionary, pokerEnv.community_cards, 5)

    # Normalize the pot size
    pot_size_observation = np.array([pokerEnv.pot / INITIAL_STACK_SIZE * 2])

    # Normalize the stack sizes for both players
    stack_sizes_observation = np.array(
        [cur_player.stack_size / (INITIAL_STACK_SIZE * 2), other_player.stack_size / (INITIAL_STACK_SIZE * 2)])

    # Combine the different parts of the observation into a tuple
    observation = (
        hand_observation,
        positions_observation,
        community_cards_observation,
        pot_size_observation,
        stack_sizes_observation,
    )
    return convert_observation_to_input(observation)

def get_position_representation(cur_player, other_player):
    position_representation = np.zeros((2, 5), dtype=np.float32)
    position_representation[0, cur_player.position.value] = 1
    position_representation[0, other_player.position.value] = 1
    return position_representation

def get_cards_representation(cards_dictionary, cur_cards, mum_of_cards):
    card_representation = np.zeros((mum_of_cards, 17), dtype=np.float32)
    for i, card in enumerate(cur_cards):
        card_representation[i, cards_dictionary[card][0] - 1] = 1
        card_representation[i, 13 + cards_dictionary[card][1] - 1] = 1
    return card_representation

def convert_observation_to_input(observation):
    temp_array = np.array([])
    for obs in observation:
        temp_array = np.hstack([temp_array, obs.flatten()])
    return temp_array

def create_cards_dictionary():
    chars = ["h", "d", "c", "s"]
    nums = [str(x) for x in range(2, 10)] + ["T", "J", "Q", "K", "A"]
    index = 0
    dictionary = {}
    for n in nums:
        for c in chars:
            combo = n + c
            dictionary[Card.new(combo)] = (index, combo)
            index += 1
    final_dic = {}
    auxiliary_dic = {"T":10, "J":11, "Q":12, "K":13, "A":1,"h":1, "d":2, "c":3, "s":4}
    for num_key, tup in dictionary.items():
        card_value = tup[1][0]
        if card_value in auxiliary_dic:
            card_value = auxiliary_dic[card_value]
        card_colour = auxiliary_dic[tup[1][1]]
        final_dic[num_key] = (int(card_value), card_colour)
    return final_dic



class Game:

    def __init__(self):
        self.env = None
        self.agent_model = None
        self.cards_dictionary = None
        self.done = None
        self.agent_action = None
        self.player_action = None
        self.winner = None


    def reset(self):
        self.env = PokerEnv()
        self.agent_model = keras.models.load_model('C:/Users/Omer/WebPokerGame/PokerModel/PokerModel/model.h5')
        self.cards_dictionary = create_cards_dictionary()
        self.done = False
        self.agent_action = ""
        self.player_action = ""
        self.winner = ""
        return self.create_context()


    # def step(self, player_action):
    #     agent_action = ""
    #     done, action_taken, _ = self.env.execute_player_action(self.env.player, self.env.opponent, player_action)
    #     if not done:
    #         agent_action = get_other_player_action(self.env, self.agent_model, self.cards_dictionary,
    #                                                self.env.opponent, self.env.player)
    #         done, agent_action, _ = self.env.execute_player_action(self.env.opponent, self.env.player, agent_action)
    #     self.agent_action = agent_action
    #     self.done = done
    #     return self.create_context()

    def step(self, player_action):
        if self.is_player_turn():
            self.done, self.player_action, self.winner = self.env.execute_player_action(self.env.player, self.env.opponent, player_action)
        else:
            agent_action = get_other_player_action(self.env, self.agent_model, self.cards_dictionary,
                                                   self.env.opponent, self.env.player)
            self.done, self.agent_action, self.winner = self.env.execute_player_action(self.env.opponent, self.env.player, agent_action)

    def is_player_turn(self):
        if self.env.check_if_playable(self.env.player, self.env.opponent):
            return True
        else:
            return False

    def create_context(self):
        context = {
            "player_cards": self.env.cards_print(self.env.player.hand),
            "player_stack": self.env.player.stack_size,
            "player_position": self.env.player.position.name,
            "opponent_stack": self.env.opponent.stack_size,
            "opponent_position": self.env.opponent.position.name,
            "opponent_cards": self.env.cards_print(self.env.opponent.hand),
            "opponent_action": self.agent_action,
            "community_cards": self.env.cards_print(self.env.community_cards),
            "done": self.done,
            "pot_size": self.env.pot,
            "player_turn": self.is_player_turn(),
            "winner": self.winner
        }
        return context

    def get_absolute_winner(self):
        if self.env.player.stack_size > self.env.opponent.stack_size:
            return "Player"
        else:
            return "opponent"


def play_game():
    env = PokerEnv()
    agent_model = keras.models.load_model('model.h5')
    cards_dictionary = create_cards_dictionary()

    done = False
    print(env.full_print())
    while not done:
        player_action = 0
        while True:
            try:
                player_action = int(input("Enter Action: 0-fold, 1-check, 2-call, 3-min raise, 4-big raise"
                                          " char for status:"))
                break
            except:
                print(env.full_print())
                continue
        done, action_taken,  = env.execute_player_action(env.player, env.opponent, player_action)
        print("player move:" + action_taken)
        if not done:
            agent_action = get_other_player_action(env, agent_model, cards_dictionary, env.opponent, env.player)
            done, action_taken, _ = env.execute_player_action(env.opponent, env.player, agent_action)
            print("agent move:" + action_taken)
            print(env.full_print())

