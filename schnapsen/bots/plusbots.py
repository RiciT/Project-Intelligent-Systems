from schnapsen.game import Bot, PlayerPerspective, SchnapsenDeckGenerator, Move, Trick, GamePhase, RegularMove, Card
from typing import Optional, cast, Literal, List, Tuple
from schnapsen.deck import Suit, Rank

import pathlib
import time

import random

class PassBot1(Bot):
    '''Really basic passive strategy
    '''
    def __init__(self, rand : random.Random, name : Optional[str] = None):
        self.rand = rand
        super().__init__(name)
    
    def get_move(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        valid_moves = perspective.valid_moves()
        trump_suit = perspective.get_trump_suit()

        chosen_move : Move = self.rand.choice(valid_moves)

        for move in valid_moves:
            #This bot does not care about making moves that arent reguler like trump exchange or marriages
            if not move.is_regular_move():
                continue
            else:
                #tries to find the smallest possible nontrump card available and play it
                if  rankIsSmaller(move.cards[0].rank, chosen_move.cards[0].rank):
                    if move.cards[0].suit == trump_suit:
                        continue
                    elif move.cards[0].suit != trump_suit:
                        chosen_move = move
        
        #print(valid_moves, chosen_move, trump_suit)

        return chosen_move
    
class PassBot2(Bot):
    '''Uncle Tibor strategy - Martin Tompa: Winning Schanpsen
    https://psellos.com/schnapsen/strategy.html#trumpcontrol
    If not leading acts similar AgrBot1
    '''
    def __init__(self, rand : random.Random, name : Optional[str] = None):
        self.rand = rand
        super().__init__(name)

    def get_move(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        valid_moves = perspective.valid_moves()
        trump_suit = perspective.get_trump_suit()
        is_lead = perspective.am_i_leader()

        leading_m : Move
        if leader_move:
            leading_m = leader_move

        chosen_move = self.rand.choice(valid_moves)

        #If leading try to play trump exchange or marriage
        if is_lead:
            for move in valid_moves:
                if move.is_trump_exchange():
                    chosen_move = move
                    break
                if move.is_marriage():
                    chosen_move = move
                    break
                #If no special moves play nontrump tens or aces to bait out trumps - else play jack nontrump
                if move.is_regular_move():
                    if move.cards[0].suit is not trump_suit:
                        if move.cards[0].rank == Rank.TEN or move.cards[0].rank ==  Rank.ACE:
                            chosen_move = move
                            break
                        elif move.cards[0].rank == Rank.JACK:
                            chosen_move = move
                    #if no good option we go with something randomly
                    else:
                        chosen_move = move
        else:
            not_dumb_moves : List[Move] = []

            for move in valid_moves:
                #gather all possible moves that arent dumb regarding our strategy
                if move.is_regular_move():
                        #a move in this case is not dumb is it can beat the enemy and its not trump
                        if (move.cards[0].suit == leading_m.cards[0].suit or \
                            (move.cards[0].suit != trump_suit and leading_m.cards[0].suit != trump_suit)) \
                                and rankIsSmaller(leading_m.cards[0].rank, move.cards[0].rank):
                            not_dumb_moves.append(move)
                        #else we just want to play any non trump card of our own 
                        else:
                            if move.cards[0].suit == trump_suit:
                                continue
                            elif move.cards[0].suit != trump_suit:
                                not_dumb_moves.append(move)
            
            #randomly selecting from best seeming moves
            if len(not_dumb_moves) != 0:
                chosen_move = self.rand.choice(not_dumb_moves)
        
        return chosen_move

class AgrBot1(Bot):
    '''Really basic agressive strategy
    If leading play highest card - if following and cant win play lowest
    '''
    def __init__(self, rand : random.Random, name : Optional[str] = None):
        self.rand = rand
        super().__init__(name)

    def get_move(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        valid_moves = perspective.valid_moves()
        trump_suit = perspective.get_trump_suit()
        is_lead = perspective.am_i_leader()

        chosen_move = self.rand.choice(valid_moves)

        leading_m : Move
        if leader_move:
            leading_m = leader_move

        for move in valid_moves:
            #if leading checks for special moves if none found...
            if is_lead:
                if move.is_trump_exchange():
                    chosen_move = move
                    break
                if move.is_marriage():
                    chosen_move = move
                    break
                #tries to play the highest card it has regarding rank and trumpness
                if move.is_regular_move():
                    if move.cards[0].suit is trump_suit:
                        if  rankIsSmaller(chosen_move.cards[0].rank, move.cards[0].rank):
                            chosen_move = move
                    elif chosen_move.cards[0].suit is not trump_suit:
                        if  rankIsSmaller(chosen_move.cards[0].rank, move.cards[0].rank):
                            chosen_move = move
            else:
                #if following see if it can win the trick if yes play that if not plays smallest card
                if move.is_regular_move():
                    if (move.cards[0].suit == leading_m.cards[0].suit or \
                        (move.cards[0].suit == trump_suit and leading_m.cards[0].suit != trump_suit)) \
                            and rankIsSmaller(leading_m.cards[0].rank, move.cards[0].rank):
                        chosen_move = move
                        break
                    else:
                        if rankIsSmaller(move.cards[0].rank, chosen_move.cards[0].rank):
                            if move.cards[0].suit == trump_suit:
                                continue
                            elif move.cards[0].suit != trump_suit:
                                chosen_move = move

        return chosen_move

class AgrBot2(Bot):
    '''Tries not to play kings and queens if theres still a chance for a marriage, tries to lose last
    trick of first phase for the extra trump - otherwise plays like agrbot1
    '''
    def __init__(self, rand : random.Random, name : Optional[str] = None):
        self.rng = rand
        super().__init__(name)

    def get_move(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        valid_moves = perspective.valid_moves()
        trump_suit = perspective.get_trump_suit()
        is_lead = perspective.am_i_leader()

        chosen_move = self.rng.choice(valid_moves)

        leading_m : Move
        if leader_move:
            leading_m = leader_move

        for move in valid_moves:
            #if on last trick of phase one tries to lose the trick to get the extra trump
            if perspective.get_talon_size() == 2:
                if is_lead:
                    if move.is_regular_move():
                        if rankIsSmaller(move.cards[0].rank, chosen_move.cards[0].rank):
                            chosen_move == move
                else:
                    if move.is_regular_move():
                        if rankIsSmaller(move.cards[0].rank, leading_m.cards[0].rank) and \
                              rankIsSmaller(move.cards[0].rank, chosen_move.cards[0].rank) and \
                                ((move.cards[0].suit == trump_suit and leading_m.cards[0].suit == trump_suit) or \
                                move.cards[0].suit != trump_suit and leading_m.cards[0].suit != trump_suit):
                            chosen_move == move
            
            #if leading tries to play special moves
            elif is_lead:
                if move.is_trump_exchange():
                    chosen_move = move
                    break
                if move.is_marriage():
                    chosen_move = move
                    break
                #and tries to find the biggest trump card to play while avoiding playing parts of possible marriages 
                if move.is_regular_move() and rankIsSmaller(chosen_move.cards[0].rank, move.cards[0].rank):
                    if move.cards[0].suit is trump_suit:
                        if move.cards[0].rank == Rank.QUEEN and \
                            Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                            Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                            continue
                        if move.cards[0].rank == Rank.KING and \
                            Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                            Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                            continue
                        chosen_move = move
                    elif chosen_move.cards[0].suit is not trump_suit:
                        if move.cards[0].rank == Rank.QUEEN and \
                            Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                            Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                            continue
                        if move.cards[0].rank == Rank.KING and \
                            Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                            Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                            continue
                        chosen_move = move
            else:
                #if following tries to beat enemy if cant it plays the lowest card, while trying to avoid playing parts of
                #still possible marriages
                if move.is_regular_move():
                    if (move.cards[0].suit == leading_m.cards[0].suit or \
                        (move.cards[0].suit == trump_suit and leading_m.cards[0].suit != trump_suit)) \
                            and rankIsSmaller(leading_m.cards[0].rank, move.cards[0].rank):
                        if move.cards[0].rank == Rank.QUEEN and \
                            Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                            Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                            continue
                        if move.cards[0].rank == Rank.KING and \
                            Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                            Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                            continue
                        chosen_move = move
                    else:
                        if rankIsSmaller(move.cards[0].rank, chosen_move.cards[0].rank):
                            if move.cards[0].rank == Rank.QUEEN and \
                                Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                                Card.get_card(Rank.KING, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                                continue
                            if move.cards[0].rank == Rank.KING and \
                                Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.get_hand().get_cards() and \
                                Card.get_card(Rank.QUEEN, move.cards[0].suit) not in perspective.seen_cards(leader_move).get_cards():
                                continue
                            if move.cards[0].suit == trump_suit:
                                continue
                            elif move.cards[0].suit != trump_suit:
                                chosen_move = move

        return chosen_move

#This function determines if rank1 is smaller in rank than rank2
def rankIsSmaller(rank1 : Rank, rank2 : Rank) -> bool:
    if  (rank1 == Rank.JACK and (rank2 == Rank.QUEEN or rank2 == Rank.KING or rank2 == Rank.TEN or rank2 == Rank.ACE)) or \
        (rank1 == Rank.QUEEN and (rank2 == Rank.KING or rank2 == Rank.TEN or rank2 == Rank.ACE)) or \
        (rank1 == Rank.KING and (rank2 == Rank.TEN or rank2 == Rank.ACE)) or \
        (rank1 == Rank.TEN and (rank2 == Rank.ACE)):
        return True
    return False