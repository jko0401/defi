class Coin():
    def __init__(self, coin, price, holdings):
        self.name = coin
        self.price = price
        self.holdings = holdings
        self.value = self.price * self.holdings


class Platform():
    def __init__(self, name):
        self.name = name
        self.coins = {}

    def add(self, asset):
        self.coins[asset.name] = asset

    def value(self):
        assets = [a for a in self.coins.values()]
        return sum([c.value for c in assets])

    def tokens(self, token):
        try:
            return self.coins[token].holdings
        except NameError:
            print('Coin not in portfolio.')

    def update(self, token, amount):
        self.coins[token].value += amount