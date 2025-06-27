"""A module implementing a class for generating fake data for development purposes."""
import random

class Sailboat:
    """Creates fake sailboat sensor data.
    
    Attributes:
        id: Identification number of a sailboat.
        x: x-coordinate, randomly generated upon creation, changed by using the move() method.
        y: y-coordinate, randomly generated upon creation, changed by using the move() method.
        horizontal_speed: x-axis component of the speed, randomly generated,
                          changed by using the move() method.
        vertical_speed: y-axis component of the speed, randomly generated,
                          changed by using the move() method.
    """
    def __init__(self, id):
        """Initializes a Sailboat object.

        Args:
            id: Identification number of a sailboat.
        """
        self.id: int = id
        self.x: float = random.uniform(50, 950)
        self.y: float = random.uniform(50, 950)
        self.horizontal_speed: float = random.uniform(-1, 1)
        self.vertical_speed: float = random.uniform(-1, 1)
        

    def move(self) -> None:
        """Updates the sailboat's location and speed."""
        if random.uniform(0, 1) > 0.8:
            if random.uniform(0, 1) > 0.5:
                if random.uniform(0, 1) > 0.5:
                    if self.horizontal_speed < 1:
                        self.horizontal_speed += 0.1
                else:
                    if self.horizontal_speed > -1:
                        self.horizontal_speed -= 0.1
            else:
                if random.uniform(0, 1) > 0.5:
                    if self.vertical_speed < 1:
                        self.vertical_speed += 0.1
                else:
                    if self.vertical_speed > -1:
                        self.vertical_speed -= 0.1

        if self.x + self.horizontal_speed >= 950 \
        or self.x + self.horizontal_speed <= 50:
            self.horizontal_speed *= -1
        else:
            self.x += self.horizontal_speed
        
        if self.y + self.vertical_speed >= 950 \
        or self.y + self.vertical_speed <= 50:
            self.vertical_speed *= -1
        else:
            self.y += self.vertical_speed