class Coin():
    def __init__(self, coin, ticker, price, holdings):
        self.name = coin
        self.ticker = ticker
        self.price = price
        self.holdings = holdings
        self.value = self.price * self.holdings

    def update(self):
        import defi_tools as dft
        self.price = dft.geckoPrice(self.name, 'usd')
        return self


class Wallet():
    def __init__(self, name):
        self.name = name
        self.coins = {}
        self.value = 0

    def add(self, asset):
        self.coins[asset.name] = asset

    def updatePrices(self):
        for c in self.coins:
            self.coins[c].update

    def totalValue(self):
        Wallet.updatePrices(self)
        assets = [a for a in self.coins.values()]
        total = sum([c.value for c in assets])
        self.value = total
        print(f'Total Value: {total}')
        return total
        
    def tokens(self, token):
        try:
            return self.coins[token].holdings
        except NameError:
            print('Coin not in portfolio.')

    def hasToken(self, token):
        return self.coins[token]

    def update(self, token, amount, overwrite=False):
        if not overwrite:
            self.coins[token].holdings += amount
        else:    
            self.coins[token].holdings = amount

    def getHoldings(self):
        return {self.coins[k].ticker:self.coins[k].holdings for k in self.coins if self.coins[k].holdings>0}

    def getValues(self):
        Wallet.updatePrices(self)
        return {self.coins[k].ticker:self.coins[k].value for k in self.coins if self.coins[k].holdings>0}

    def show(self):
        import pandas as pd
        holdings = Wallet.getHoldings(self)
        values = Wallet.getValues(self)
        total = self.value
        if total == 0:
            total = Wallet.totalValue(self)
        allocation = [float(values[v])/total for v in values]
        return pd.DataFrame({'coin':holdings.keys(),'holdings':holdings.values(), 'value':values.values(), 'allocation':allocation})

class Transaction():
    def transfer(origin, destination, token, amount, fee):
        origin.update(token, -(amount+fee))
        Transaction.add(origin, token, (amount+fee), 'transfer')
        destination.update(token, amount)
        Transaction.add(destination, token, amount, 'transfer')
        print(f'Transferred {amount} {origin.coins[token].ticker} from {origin.name} to {destination.name}')

    def transact(platform, token, amount, value, type):
        if type=='buy':
            if not platform.hasToken(token):
                import defi_tools as dft
                coin = Coin(coin=token, ticker=dft.geckoGetSymbol[token], price=dft.geckoPrice(token, 'usd'), holdings=amount)
                platform.add(coin)
            Transaction.add(platform, token, amount, 'buy')
            Transaction.add(platform, 'USD', value, 'sell')
            print(f'Bought {amount} {platform.coins[token].ticker}.')
            value = -value
        elif type=='sell':
            Transaction.add(platform, token, amount, 'sell')
            Transaction.add(platform, 'USD', value, 'buy')
            print(f'Sold {amount} {platform.coins[token].ticker}.')
            amount = -amount
        else:
            proceeds = 0
            amount = 0
            print('Type not specified. No updates.')    
        
        platform.update(token, amount)
        platform.update('USD', value)
    
    def add(platform, token, amount, t_type):
        import csv
        from datetime import datetime   
        now = datetime.now()
        platform.updatePrices()
        value = amount * platform.coins[token].price
        fields=[now, platform.name, platform.coins[token].ticker, amount, value, t_type]
        with open(r'transactions.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(fields)
        f.close()

class Calc():
    def avg(token, all=False):
        pass
        # import pandas as pd
        # df = pd.read_csv('transactions.csv', names=['timestamp', 'platform', 'token', 'amount', 'est_value', 'type'])
        # if all:
        #     token = df['tokens'].unique()
        #     t = 'All'
        # t = [token]
        # avgB = df[(df.token.isin(t))&(df.type == 'buy')]['est_value'].mean() 
        # avgS = df[(df.token.isin(t))&(df.type == 'sell')]['est_value'].mean()
        # profit = avgS - avgB 
        # print(f'{t}| average buy: {avgB}, average sell: {avgS}, profit: {profit} ({profit/avgB}%)' )

class Plot():
    def allocations():
        pass

    




        

