  # -*- coding: latin-1 -*-
import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *


##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):
    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "The Hungry Bat")
        #these variables will be used to store the locations
        self.batFood = None
        self.batTunnel = None
        self.batCave = None

    #getPlacement
    #
    #Description: The getPlacement method corresponds to the 
    #action taken on setup phase 1 and setup phase 2 of the game. 
    #In setup phase 1, the AI player will be passed a copy of the 
    #state as currentState which contains the board, accessed via 
    #currentState.board. The player will then return a list of 11 tuple 
    #coordinates (from their side of the board) that represent Locations 
    #to place the anthill and 9 grass pieces. In setup phase 2, the player 
    #will again be passed the state and needs to return a list of 2 tuple
    #coordinates (on their opponent's side of the board) which represent
    #Locations to place the food sources. This is all that is necessary to 
    #complete the setup phases.
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is 
    #       requesting a placement from the player.(GameState)
    #
    #Return: If setup phase 1: list of eleven 2-tuples of ints -> [(x1,y1), (x2,y2),…,(x10,y10)]
    #       If setup phase 2: list of two 2-tuples of ints -> [(x1,y1), (x2,y2)]
    #Creates a defensive wall of grass, while putting the tunnel and the anthill in the middle
    ##
    def getPlacement(self, currentState):
        self.batFood = None
        self.batTunnel = None
        self.batCave = None

        if currentState.phase == SETUP_PHASE_1:
            return[(2,1), (7,1), (0,3), (1,3), (2,3), (3,3), (4,3),( 6,3), (7,3), (8,3), (9,3)];    #grass placement 
        #Randomly places enemy food, *stolen from Dr. Nuxoll's Simple Food Gatherer AI*
        elif currentState.phase == SETUP_PHASE_2:
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:            
            return None  #should never happen

    ##
    #getMove
    #Description: The getMove method corresponds to the play phase of the game 
    #and requests from the player a Move object. All types are symbolic 
    #constants which can be referred to in Constants.py. The move object has a 
    #field for type (moveType) as well as field for relevant coordinate 
    #information (coordList). If for instance the player wishes to move an ant, 
    #they simply return a Move object where the type field is the MOVE_ANT constant 
    #and the coordList contains a listing of valid locations starting with an Ant 
    #and containing only unoccupied spaces thereafter. A build is similar to a move 
    #except the type is set as BUILD, a buildType is given, and a single coordinate 
    #is in the list representing the build location. For an end turn, no coordinates 
    #are necessary, just set the type as END and return.
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is 
    #       requesting a move from the player.(GameState)   
    #
    #Return: Move(moveType [int], coordList [list of 2-tuples of ints], buildType [int]
    ##
    def getMove(self, currentState):
        inventory = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn
        self.initConstAndFood(currentState, me)     
        
        #If we dont have a soldier, try to build one
        if (len(getAntList(currentState, me, (SOLDIER,))) < 1):
            if(getAntAt(currentState, self.batCave[0].coords) == None and inventory.foodCount >= 3):
                    return Move(BUILD, [self.batCave[0].coords,], SOLDIER)

        #Try to build an extra soldier ant if the enemy is in the neutral zone, or in our territory
        if (len(getAntList(currentState, me, (SOLDIER,))) < 2):  
            for ant in getAntList(currentState, not me, (QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER)):
                if(ant.coords[1] < 6 and inventory.foodCount >= 3 and 
                        getAntAt(currentState, self.batCave[0].coords) == None):
                    return Move(BUILD, [self.batCave[0].coords,], SOLDIER) 

        #Build New Worker(s)
        if(len(getAntList(currentState, me, (WORKER,))) < 2):
            if(inventory.foodCount > 0 and getAntAt(currentState, self.batCave[0].coords) == None):
                return Move(BUILD, [self.batCave[0].coords,], WORKER)

        #Moves the worker ants to/from food sources and drop points
        workerParty = getAntList(currentState, me, (WORKER,))
        for worker in workerParty:    
            if not worker.hasMoved: 
                return Move(MOVE_ANT, self.getWorkerPath(currentState, worker, workerParty.index(worker)), None)

        #Moves the queen into the back and out of the way
        myQueen = getAntList(currentState, me, (QUEEN,))[0]
        if not myQueen.hasMoved:
            return Move(MOVE_ANT, self.queenPath(currentState, myQueen), None)

        #if we have at least one soldier, have them move towards the enemy
        if(len(getAntList(currentState, me, (SOLDIER,))) >= 1):
            for soldier in getAntList(currentState, me, (SOLDIER,)):
                if not soldier.hasMoved:
                    return Move(MOVE_ANT, self.findBestPath(currentState, soldier, 
                            self.findNearestEnemy(currentState, soldier)), None)

        #If we are out of moves, end our turn
        return Move(END, None, None)
    ####### END OF GET MOVE #######

    ##
    #initConstAndFood
    #
    #Initilizes various constructs and food locations
    #
    #Parameters:
    #       CurrentState - current game state
    #       me - the current player ID
    #
    #Return: None
    def initConstAndFood(self, currentState, me):
        #if we dont know where our food is yet, find the two locations
        if(self.batFood == None): 
            self.batFood = []
            for food in getConstrList(currentState, None, (FOOD,)): 
                if food.coords[1] < 4: #get only the two foods on our side
                    self.batFood.append(food)
        if(self.batCave == None):
            self.batCave = getConstrList(currentState, me, (ANTHILL,))
        if(self.batTunnel == None):
            self.batTunnel = getConstrList(currentState, me, (TUNNEL,))    
    ##
    #getWorkerPath
    #
    #determines the best path for the worker between the closest food and 
    #the workers assigned drop point
    #
    #Parameters
    #   CurrentState - current game state
    #   worker - a reference to a worker ant
    #   workerIndex - the index of the worker ant in the worker ant list
    #
    #Return: A path to be used by a Move command
    # 
    def getWorkerPath(self, currentState, worker, workerIndex):
        if worker.carrying:
            if(workerIndex == 0):
                destination = self.batTunnel[0].coords                    
            else:
                destination = self.batCave[0].coords
            return self.findBestPath(currentState, worker, destination)
        else:
            closestFood = stepsToReach(currentState, self.batFood[0].coords, worker.coords)
            if(closestFood > stepsToReach(currentState, self.batFood[1].coords, worker.coords)):
                closestFood = 1
            else:
                closestFood = 0
            return self.findBestPath(currentState, worker, self.batFood[closestFood].coords)

    ##
    #findNearestEnemy
    #Gets the coordinates of the nearest enemy
    #
    #Parameters
    #   CurrentState - current game state
    #   ant - reference to the the ant we wish to move
    #
    #Return: the coordinates of the nearest enemy
    #
    def findNearestEnemy(self, currentState, ant):
        dist = 100.0
        targetCoords = (0,0)
        for enemyAnt in getAntList(currentState, not currentState.whoseTurn, (QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER)):
            if(approxDist(enemyAnt.coords, ant.coords) < dist):
                        targetCoords = enemyAnt.coords
        return targetCoords

    ##
    #findBestPath
    #
    #Finds the best path to the destination
    #
    #Parameters
    #   CurrentState - current game state
    #   ant - reference to the the ant we wish to move
    #   destCoords - location we want to move to
    #
    #Return: A path to be used by a Move command
    #
    def findBestPath(self, currentState, ant, destCoords):
        moveArray = listAllMovementPaths(currentState, ant.coords, UNIT_STATS[ant.type][MOVEMENT])
        shortestDist = 100 #impossibly large value
        bestCoords = (0,0) #default
        #check if the desired location is availible for the worker to move to
        if ant.type == WORKER and approxDist(ant.coords, destCoords) < 2 and getAntAt(currentState, destCoords) != None:
            dest = random.choice(listReachableAdjacent(currentState, ant.coords, UNIT_STATS[ant.type][MOVEMENT]))
            return createPathToward(currentState, ant.coords, dest, UNIT_STATS[ant.type][MOVEMENT])

        for movelists in moveArray:
            for move in movelists:
                dist = stepsToReach(currentState, move, destCoords)
                if(shortestDist > dist):
                    shortestDist = dist
                    bestCoords = move
        return createPathToward(currentState, ant.coords, bestCoords, UNIT_STATS[ant.type][MOVEMENT])
    ##
    #queenPath
    #
    #This moves the queen off the cave, and also keeps her away from the
    #tunnels and the food resources so workers can be more efficient
    #
    #Parameters
    #   CurrentState - current game state
    #   myQueen - reference to the queen ant
    #
    #Return: A path to be used by a Move command
    #
    def queenPath(self, currentState, myQueen):
        queenCoordinates = myQueen.coords
        while(stepsToReach(currentState, queenCoordinates, self.batFood[0].coords) <= 2
            or stepsToReach(currentState, queenCoordinates, self.batFood[1].coords) <= 2
            or stepsToReach(currentState, queenCoordinates, self.batCave[0].coords) <= 2
            or stepsToReach(currentState, queenCoordinates, self.batTunnel[0].coords) <= 2):
            queenCoordinates = (random.randint(0,9), random.randint(0,1))
        return self.findBestPath(currentState, myQueen, queenCoordinates)

    ##
    #getAttack
    #Description: The getAttack method is called on the player whenever an ant completes 
    #a move and has a valid attack. It is assumed that an attack will always be made 
    #because there is no strategic advantage from withholding an attack. The AIPlayer 
    #is passed a copy of the state which again contains the board and also a clone of 
    #the attacking ant. The player is also passed a list of coordinate tuples which 
    #represent valid locations for attack. Hint: a random AI can simply return one of 
    #these coordinates for a valid attack. 
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is requesting 
    #       a move from the player. (GameState)
    #   attackingAnt - A clone of the ant currently making the attack. (Ant)
    #   enemyLocation - A list of coordinate locations for valid attacks (i.e. 
    #       enemies within range) ([list of 2-tuples of ints])
    #
    #Return: A coordinate that matches one of the entries of enemyLocations. ((int,int))
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        return enemyLocations[0] 
        
    ##
    #registerWin
    #Description: The last method, registerWin, is called when the game ends and simply 
    #indicates to the AI whether it has won or lost the game. This is to help with 
    #learning algorithms to develop more successful strategies.
    #
    #Parameters:
    #   hasWon - True if the player has won the game, False if the player lost. (Boolean)
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass
