import math
from blob import Blob
import datetime


class Player():
    '''A Player represents either the user or a CPU player. Most importabtly,
    it stores a collection of blobs, including one that is the center, which
    is always in the middle of the screen for that player'''

    def __init__(self, x, y, r, color, id_number):
        self.blobs = set()
        b = Blob(x, y, r, color, False, id_number, None)
        self.blobs.add(b)
        self.size = 1
        self.id_number = id_number
        self.time = datetime.datetime.now()
        self.shoot_time = None
        self.has_recovered = True
        self.center = b
        self.r = r

    def get_absolute_position(self):
        '''Returns the position of the player as an x-y tuple. This is the same
        as the absolute position of the center blob (the one at the center of
        the screen at all times)'''
        return self.center.get_absolute_position()

    def shoot(self, direction):
        '''Shoot a new blob in the given direction. This creates the double
        the number of blobs (up to a max of 16), each with half the radius, and
        halves the radius of each existing blob as well'''
        if min(b.r for b in self.blobs) > 20 and self.size < 16:
            x, y = self.center.get_absolute_position()
            r = self.center.r / 2
            color = self.center.color
            for my_b in self.blobs:
                my_b.decr_radius()
            for _ in range(self.size):
                self.blobs.add(Blob(x, y, r, color, True, self.id_number,
                               direction))
            self.size *= 2
            self.shoot_time = datetime.datetime.now()

    def recovery_time(self):
        '''Gets the time needed to re-combine the constituent blob into one
        large blob. The time increases as the total mass increases'''
        total_mass = sum(b.r for b in self.blobs)
        return 30 + 0.02 * total_mass

    def move(self, direction):
        '''Moves the player in a given direction. If the time is after the
        recovery time, then some of the blobs may eat others. Note that the
        usual rules for eating do not apply (the radius does not need to be
        more than other.r/0.75).'''
        now = datetime.datetime.now()
        if self.shoot_time is None:
            delta = 0
        else:
            delta = (now - self.shoot_time).seconds
        to_remove = None
        for b in self.blobs:
            bx, by = b.get_absolute_position()
            b.move(direction, self.center)
            if delta > self.recovery_time() and to_remove is None:
                for other in self.blobs:
                    if other is not b:
                        ox, oy = other.get_absolute_position()
                        if math.hypot(bx - ox, by - oy) < b.r:
                            b.eatObj(other)
                            to_remove = other
        if to_remove is not None:
            self.remove_blob(to_remove)

    def draw(self, dc, relative_position):
        '''Draws the player by drawing all its constituent blobs'''
        [b.draw(dc, relative_position) for b in self.blobs]

    def decay(self):
        '''Decays the player by decaying all its consituent blobs'''
        (b.decay() for b in self.blobs)

    def remove_blob(self, blob):
        '''Removes a blob from the set of blobs, adjusting the center if
        necessary'''
        self.blobs.remove(blob)
        if blob is self.center and len(self.blobs) > 0:
            self.center = next(iter(self.blobs))
        self.size -= 1
