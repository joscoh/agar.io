import math
import wx

GAME_WIDTH = 2400
GAME_HEIGHT = 2400
FRAME_WIDTH = 600
FRAME_HEIGHT = 600


def find_grid(x, y):
    '''Finds the correct grid location of a given coordinate'''
    x = min(x, GAME_WIDTH - 1)
    y = min(y, GAME_HEIGHT - 1)
    x = max(x, 0)
    y = max(y, 0)
    xGrid = int(x // FRAME_WIDTH)
    yGrid = int(y // FRAME_HEIGHT)
    numYGrids = GAME_HEIGHT / FRAME_HEIGHT
    return int(yGrid * numYGrids + xGrid)


class GameObject():
    '''A GameObject represents any circular object on the game board, namely
    food and blobs. GameObjects have a position, radius, and color, but cannot
    move or do anything'''

    def __init__(self, x, y, r, color, isFood):
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.isFood = isFood
        self.relative_velocity = (0, 0)

    def get_absolute_position(self):
        '''Returns the position of the center of the game object as a tuple'''
        return (self.x + self.r, self.y + self.r)

    @staticmethod
    def has_collided(obj_1, obj_2):
        '''Static method that checks to see if two objects have collided'''
        x1, y1 = obj_1.get_absolute_position()
        x2, y2 = obj_2.get_absolute_position()
        b = math.hypot(x1 - x2, y1 - y2) < obj_1.r + obj_2.r
        return b

    @staticmethod
    def hasEaten(obj_1, obj_2):
        '''Static method that checks to see if object 1 has eaten object 2.
        Note that this is a stronger claim than a collision - the smaller
        object must be completely inside the larger one'''
        x1, y1 = obj_1.get_absolute_position()
        x2, y2 = obj_2.get_absolute_position()
        max_rad = max(obj_1.r, obj_2.r)
        b = math.hypot(x1 - x2, y1 - y2) < max_rad
        return b

    @staticmethod
    def normalize(direction):
        '''Normalizes a 2-D vector'''
        x, y = direction
        norm = math.sqrt(math.pow(x, 2) + math.pow(y, 2))
        if norm != 0:
            new_dir = (x / norm, y / norm)
        else:
            new_dir = (0, 0)
        return new_dir

    def draw(self, dc, relative_position):
        '''Draws the given GameObject with the given drawing context'''
        dc.SetBrush(wx.Brush(self.color))
        x, y = relative_position
        dc.DrawEllipse(x - self.r, y - self.r, 2 * self.r, 2 * self.r)

    def get_grid_location(self):
        '''Returns the list of grid locations that the object encompasses. Note
        that this will nearly always be 4 or fewer. This allows easier checks
        of possible food and other player targets - we only have the check in
        the returned grids, not in every location'''
        to_return = set()
        topLeft = find_grid(self.x - self.r, self.y - self.r)
        topRight = find_grid(self.x + self.r, self.y - self.r)
        bottomLeft = find_grid(self.x - self.r, self.y + self.r)
        ctr = 0
        while(topLeft + ctr <= bottomLeft):
            for i in range(topLeft + ctr, topRight + 1 + ctr):
                to_return.add(i)
            ctr += 4
        return list(to_return)
