import math
from gameobject import GameObject
import datetime


class Blob(GameObject):
    '''A Blob represents a single disk in the game. It can move, eat others,
    and change its size. A player controls a collection of Blobs'''

    def __init__(self, x, y, r, color, shoot, id_number, init_direction):
        super().__init__(x, y, r, color, False)
        self.shoot = shoot
        self.time = datetime.datetime.now()
        self.id_number = id_number
        self.recover = False
        self.init_direction = init_direction

    def decr_radius(self):
        '''Halves the radius of the given blob. This is used when a player
        shoots a new, smaller blob and decreases the sizes of its existing
        blobs'''
        self.r = self.r / 2

    def velocity(self):
        '''Calculates the current velocity of the blob, which is a function
        of its mass. If the blob was shot by a parent, its velocity is
        temporarily (for 2 seconds) higher'''
        if not self.shoot:
            return 20 * math.pow(self.r, -0.439)
        else:
            now = datetime.datetime.now()
            seconds = (now - self.time).seconds
            micros = (now - self.time).microseconds / (10 ** 6)
            delta = seconds + micros
            if delta > 2:
                self.shoot = False
                self.recover = True
            v_0 = 20 * math.pow(self.r, -0.439)
            v = 5 * v_0 + ((v_0 * (1 - 5)) / 2) * delta
            return v

    def eatObj(self, obj):
        '''Eats the given object, growing its radius accordingly. Note that
        the new size is defined by the total area of this blob and the
        eaten blob, so it is not linear in the radii'''
        other_radius = obj.r
        other_area = math.pi * math.pow(other_radius, 2)
        this_area = math.pi * math.pow(self.r, 2)
        new_area = other_area + this_area
        self.r = math.sqrt(new_area / math.pi)

    def move(self, direction, parent):
        '''Moves the given blob in the given direction. If it is recovering
        from being shot out, it moves back towards its parent'''
        if self.recover:
            px, py = parent.get_absolute_position()
            parent_vector = (px - self.x, py-self.y)
            x, y = GameObject.normalize(parent_vector)
            if math.hypot(px - self.x, py - self.y) < 1.5 * parent.r:
                self.recover = False
        elif self.shoot:
            x, y = GameObject.normalize(self.init_direction)
        else:
            x, y = GameObject.normalize(direction)
        self.x += self.velocity() * x
        self.y += self.velocity() * y

    def decay(self):
        '''Decreases the radius of the blob, called every 10 seconds and
        decreases larger players faster'''
        self.r = max(10, 0.99 * self.r)

    def __lt__(self, other):
        '''Compares two blobs to see if one is less than the other, defined by
        comparing their radii. A blob can only be eaten by another blob if it
        is less than that blob'''
        return self.r < 0.75 * other.r

    def __gt__(self, other):
        '''Compares two blobs to see if one is greater than the other, defined
        by comparing their radii. A blob can only eat another blob if it
        is greater than that blob'''
        return self.r > other.r / 0.75
