# agar.io
A 1-player implementation of the game agar.io written in Python

The rules of the game are virtually identical to those of online versions of agar.io. The user controls a blob and can move around by moving the mouse. The goal is to eat smaller blobs and food and avoid being eaten by larger blobs. The user can press the spacebar to split themselves into double the number of blobs, reducing the size of each blob by half and shooting the newly created blobs in the current direction. If the user loses the game, the game immediately restarts.

The other blobs in the game are automated, and determine their motion using a heuristic involving the blob in their range of sight (same as the player) with the largest danger and largest reward, both of which are a function of the distance between the two blobs and the difference in their radii.

To play the game, simply run the game.py file.
