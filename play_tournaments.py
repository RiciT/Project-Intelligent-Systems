from schnapsen.game import SchnapsenGamePlayEngine
from schnapsen.bots.ml_bot import MLPlayingBot
from schnapsen.bots.rdeep import RdeepBot
from schnapsen.bots.rand import RandBot
from schnapsen.bots.plusbots import PassBot1, PassBot2, AgrBot1, AgrBot2 

import random
from pathlib import Path
import os

engine = SchnapsenGamePlayEngine()
# choose the players

rand = random.Random()

bot1 = RdeepBot(12,6,rand,name="rdeep")

bot2 = RandBot(rand, name='rdeep')

bots = [MLPlayingBot(model_location=Path(os.getcwd() + '/models/rdrd.model'), name="change")]
# bots = [RandBot(rand, name='change'), PassBot1(rand, name='change'), PassBot2(rand, name='change'), AgrBot1(rand, name='change'), AgrBot2(rand, name='change'),
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p1p1.model'), name="change"), MLPlayingBot(model_location=Path(os.getcwd() + '/models/p2r.model'), name="change"), 
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p1p2.model'), name="change"), MLPlayingBot(model_location=Path(os.getcwd() + '/models/a1a1.model'), name="change"),
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p1a1.model'), name="change"), MLPlayingBot(model_location=Path(os.getcwd() + '/models/a1a2.model'), name="change"),
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p1a2.model'), name="change"), MLPlayingBot(model_location=Path(os.getcwd() + '/models/a1r.model'), name="change"), 
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p1r.model'), name="change"), MLPlayingBot(model_location=Path(os.getcwd() + '/models/a2a2.model'), name="change"),
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p2p2.model'), name="change"), MLPlayingBot(model_location=Path(os.getcwd() + '/models/a2r.model'), name="change"),
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p2a1.model'), name="change"), MLPlayingBot(model_location=Path(os.getcwd() + '/models/rr.model'), name="change"),
#         MLPlayingBot(model_location=Path(os.getcwd() + '/models/p2a2.model'), name="change")]

botnames = ('rdeep', 'change')

for bot in bots:
    points = [0, 0]
    for i in range(1000):
        winner_persp, score, loser_persp, winBot = engine.play_game(bot1, bot, random.Random())
        #print(f"Game ended. Winner: {str(winBot)} points: {score}")
        points[botnames.index(str(winBot))] += score
        if i % 100 == 0:
            print(i)
    with open(Path(os.getcwd() + '/TOURNAMENTS_RDEEP.res.txt'), 'a') as res:
        pointText : str = f'RDEEP: {str(points[0])}, {bot.__class__.__name__.upper()}: {str(points[1])}'
        res.write(f'{pointText}\n')
    print(points)