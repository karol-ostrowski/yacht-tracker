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
        self.x: float = random.uniform(21020602, 21043111) / 1000000
        self.y: float = random.uniform(52439085, 52456344) / 1000000
        self.horizontal_speed: float = random.uniform(-0.00005, 0.00005)
        self.vertical_speed: float = random.uniform(-0.00005, 0.00005)

    def move(self) -> None:
        """Updates the sailboat's location and speed."""
        if random.uniform(0, 1) > 0.99:
            if random.uniform(0, 1) > 0.5:
                if random.uniform(0, 1) > 0.5:
                    if self.horizontal_speed < 0.00005:
                        self.horizontal_speed += 0.00000005
                else:
                    if self.horizontal_speed > -0.00005:
                        self.horizontal_speed -= 0.00000005
            else:
                if random.uniform(0, 1) > 0.5:
                    if self.vertical_speed < 0.00005:
                        self.vertical_speed += 0.00000005
                else:
                    if self.vertical_speed > -0.00005:
                        self.vertical_speed -= 0.00000005

        if self.x + self.horizontal_speed >= 21.043111 \
        or self.x + self.horizontal_speed <= 21.020602:
            self.horizontal_speed *= -1
        else:
            self.x += self.horizontal_speed
        
        if self.y + self.vertical_speed >= 52.456344 \
        or self.y + self.vertical_speed <= 52.439085:
            self.vertical_speed *= -1
        else:
            self.y += self.vertical_speed