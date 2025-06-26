import random

def main() -> None:
    pass
    # s1 = Sailboat("politechinka")
    # path = []
    # for i in range(5000):
    #     path.append((s1.x, s1.y))
    #     s1.move()

    # x = [p[0] for p in path]
    # y = [p[1] for p in path]
    # plt.plot(x, y)
    # plt.xlim((0, 1000))
    # plt.ylim((0, 1000))
    # plt.show()
    # while True:
    #     print(f"X: {s1.x}, Y: {s1.y}")
    #     s1.move()
    #     time.sleep(0.05)

class Sailboat:
    def __init__(self, id):
        self.id: int = id
        self.x: float = random.uniform(50, 950)
        self.y: float = random.uniform(50, 950)
        self.horizontal_speed: float = random.uniform(-1, 1)
        self.vertical_speed: float = random.uniform(-1, 1)
        

    def move(self) -> None:
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

if __name__ == "__main__":
    main()