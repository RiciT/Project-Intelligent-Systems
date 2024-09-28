import pickle
import os.path
from argparse import ArgumentParser
import time
import sys
# This package contains various machine learning algorithms
import sklearn
import sklearn.linear_model
from sklearn.neural_network import MLPClassifier
import joblib

from schnapsen.game import PlayerPerspective, SchnapsenGamePlayEngine, GameState
from schnapsen.game import *

from schnapsen.bots.rand import RandBot
from schnapsen.bots.plusbots import PassBot1, PassBot2, AgrBot1, AgrBot2
from schnapsen.bots.rdeep import RdeepBot
from schnapsen.bots.ml_bot import create_state_and_actions_vector_representation, get_state_feature_vector

rand = Random()

def create_dataset(path, player=RandBot(rand), player2=RandBot(rand), games=2000):
    data = []
    target = []
    
    # For progress bar
    bar_length = 30
    start = time.time()
    
    for g in range(games-1):
        # For progress bar - easily track prgress!!! Very important to have
        if g % 10 == 0:
            percent = 100.0*g/games
            sys.stdout.write('\r')
            sys.stdout.write("Generating dataset: [{:{}}] {:>3}%".format('='*int(percent/(100.0/bar_length)),bar_length,
            int(percent)))
            sys.stdout.flush()

        # Randomly generate a state object starting in specified phase.
        engine = SchnapsenGamePlayEngine()

        #Play a game of schnapsen
        winner_persp, score, loser_persp, winBot = engine.play_game(player, player2, rand)
        
        #extract all explored states of the game
        winner_persp = winner_persp.get_game_history()[:-1]
        loser_persp = loser_persp.get_game_history()[:-1]
        
        #MLBOT
        #Loop through both perspectives because its free data so that we functionally played 100000 games not 50000
        for p in (winner_persp, loser_persp):
            #loop through all perspectives of them gam and one hot encode them then append them to the data/target lists
            for round_player_perspective, round_trick in p:

                if round_trick.is_trump_exchange():
                    leader_move = round_trick.exchange
                    follower_move = None
                else:
                    leader_move = round_trick.leader_move
                    follower_move = round_trick.follower_move

                # we do not want this representation to include actions that followed. So if this agent was the leader, we ignore the followers move
                if round_player_perspective.am_i_leader():
                    follower_move = None

                #generating state vectors
                state_actions_representation = create_state_and_actions_vector_representation(
                    perspective=round_player_perspective, leader_move=leader_move, follower_move=follower_move)
                
                data.append(state_actions_representation)
                target.append(score if p == winner_persp else -score)#'win' if player == winner_persp else 'loss')
        #MLBOT

    #dumping into file
    with open(os.getcwd() + path, 'wb') as output:
        pickle.dump((data, target), output, pickle.HIGHEST_PROTOCOL)
    
    # For printing newline after progress bar
    print("\nDone. Time to generate dataset: {:.2f} seconds".format(time.time() - start))
    return data, target

## Parse the command line options
parser = ArgumentParser()
#These options can be used to call the script through
parser.add_argument("-d", "--dset-path", 
                    dest="dset_path",
                    help="Optional dataset path",
                    default="dataset.pkl")
parser.add_argument("-m", "--model-path",
                    dest="model_path",
                    help="Optional model path. Note that this path starts in bots/ml/ instead of the base folder, like dset_path above.",
                    default="model.pkl")
parser.add_argument("-o", "--overwrite",
                    dest="overwrite",
                    action="store_true",
                    help="Whether to create a new dataset regardless of whether one already exists at the specified path.")
parser.add_argument("--no-train",
                    dest="train",
                    action="store_false",
                    help="Don't train a model after generating dataset.")
parser.add_argument("-p1", "--player1",
                    dest="player1",
                    help="Specify the bot1 used to train the model (rand, pass1, pass2, agr1, agr2)",
                    choices=['rand', 'pass1', 'pass2', 'agr1', 'agr2', 'rdeep'],
                    default="rand")
parser.add_argument("-p2", "--player2",
                    dest="player2",
                    help="Specify the bot2 used to train the model (rand, pass1, pass2, agr1, agr2)",
                    choices=['rand', 'pass1', 'pass2', 'agr1', 'agr2', 'rdeep'],
                    default="rand")
options = parser.parse_args()

#setting up the two bots that play againts each other based on the info recieved through cmd
if options.overwrite or not os.path.isfile(options.dset_path):
    random = Random()
    
    p1 : Bot
    p2 : Bot

    if options.player1 == 'pass1':
        p1 = PassBot1(random)
    elif options.player1 == 'pass2':
        p1 = PassBot2(random)
    elif options.player1 == 'agr1':
        p1 = AgrBot1(random)
    elif options.player1 == 'agr2':
        p1 = AgrBot2(random)
    elif options.player1 == 'rand':
        p1 = RandBot(random)
    elif options.player1 == 'rdeep':
        p1 = RdeepBot(12,6,random)
    
    if options.player2 == 'pass1':
        p2 = PassBot1(random)
    elif options.player2 == 'pass2':
        p2 = PassBot2(random)
    elif options.player2 == 'agr1':
        p2 = AgrBot1(random)
    elif options.player2 == 'agr2':
        p2 = AgrBot2(random)
    elif options.player2 == 'rand':
        p2 = RandBot(random)
    elif options.player2 == 'rdeep':
        p2 = RdeepBot(12,6,random)

    #calling the data generation function with the given variables and making them play 50000 games agants each other
    create_dataset(options.dset_path, player=p1, player2=p2, games=50000) #15000

if options.train:
    # Play around with the model parameters below
    # HINT: Use tournament fast mode (-f flag) to quickly test your different models.
    # The following tuple specifies the number of hidden layers in the neural
    # network, as well as the number of layers, implicitly through its length.
    # You can set any number of hidden layers, even just one. Experiment and see what works.
    hidden_layer_sizes = (64, 32)
    # The learning rate determines how fast we move towards the optimal solution.
    # A low learning rate will converge slowly, but a large one might overshoot.
    learning_rate = 0.0001
    # The regularization term aims to prevent overfitting, and we can tweak its strength here.
    regularization_strength = 0.0001
    
    #############################################
    
    start = time.time()
    
    print("Starting training phase...")
    
    with open(os.getcwd() + options.dset_path, 'rb') as output:
        data, target = pickle.load(output)
    
    # Train a neural network
    learner = MLPClassifier(hidden_layer_sizes=hidden_layer_sizes, learning_rate_init=learning_rate,
    alpha=regularization_strength, verbose=True, early_stopping=True, n_iter_no_change=6)
    
    # learner = sklearn.linear_model.LogisticRegression()
    model = learner.fit(data, target)
    
    # Check for class imbalance
    count = {}
    
    for t in target:
        if t not in count:
            count[t] = 0
        count[t] += 1
    
    print('instances per class: {}'.format(count))
    
    # Store the model in the ml directory
    joblib.dump(model, "./models/" + options.model_path)
    
    end = time.time()
    
    print('Done. Time to train:', (end-start)/60, 'minutes.')