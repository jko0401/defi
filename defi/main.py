class Coin():
    def __init__(self, coin, ticker, price, holdings):
        self.name = coin
        self.ticker = ticker
        self.price = price
        self.holdings = holdings
        self.value = self.price * self.holdings
        self.stack = {}

    def update(self):
        import defi_tools as dft
        self.price = dft.geckoPrice(self.name, 'usd')
        return self


class Wallet():
    def __init__(self, name):
        self.name = name
        self.coins = {'USD':Coin('USD', 'USD', 1, 0)}
        self.value = 0

    def add(self, asset):
        self.coins[asset.name] = asset

    def updatePrices(self):
        for c in self.coins:
            if c == 'USD':
                pass
            else:
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

    def send(time, origin, token, amount, fee):
        import defi_tools as dft
        if not time:
            from datetime import datetime
            time = datetime.now()
        origin.update(token, -(amount+fee))
        basis = dft.geckoPriceAt(token, 'usd', time)
        cost = basis*(amount+fee)
        Transaction.add(time, origin, token, (amount+fee), basis, cost, 'send')
        print(f'Sent {amount} {origin.coins[token].ticker} from {origin.name}')

    def receive(time, destination, token, amount):    
        import defi_tools as dft
        if not time:
            from datetime import datetime
            time = datetime.now()
        if not destination.hasToken(token):
            if token == 'USD':
                coin = Coin(coin=token, ticker=token, price=1, holdings=amount)
            else:    
                import defi_tools as dft
                coin = Coin(coin=token, ticker=dft.geckoGetSymbol[token], price=dft.geckoPrice(token, 'usd'), holdings=amount)
            destination.add(coin)
        else:
            destination.update(token, amount)
        basis = dft.geckoPriceAt(token, 'usd', time)
        cost = basis*amount
        Transaction.add(time, destination, token, amount, basis, cost, 'receive')
        print(f'Received {amount} {token} at {destination.name}')

    def transfer(time, origin, destination, token, amount, fee):
        if not time:
            from datetime import datetime
            time = datetime.now()
        Transaction.send(time, origin, token, amount, fee)
        Transaction.receive(time, destination, token, amount)
        print(f'Transferred {amount} {origin.coins[token].ticker} from {origin.name} to {destination.name}')

    def transact(time, wallet, buy, sell, fee):
        import defi_tools as dft
        if not time:
            from datetime import datetime
            time = datetime.now()
        
        b_tk = buy[0]
        b_amt = buy[1]
        s_tk = sell[0]
        s_amt = sell[1]
        if not wallet.hasToken(b_tk):
            import defi_tools as dft
            coin = Coin(coin=b_tk, ticker=dft.geckoGetSymbol[b_tk], price=dft.geckoPrice(b_tk, 'usd'), holdings=b_amt)
            wallet.add(coin)
        basis = dft.geckoPriceAt(b_tk, 'usd', time)
        cost = basis*(b_amt+fee)
        Transaction.add(time, wallet, b_tk, b_amt, basis, cost, 'buy')
        basis = dft.geckoPriceAt(s_tk, 'usd', time)
        cost = basis*s_amt
        Transaction.add(time, wallet, s_tk, s_amt, basis,  cost, 'sell')
        print(f'Bought {b_amt} {wallet.coins[b_tk].ticker} with {s_amt} {wallet.coins[s_tk].ticker}.')

        wallet.update(b_tk, b_amt)
        wallet.update(s_tk, -s_amt)
    
    def add(time, wallet, token, amount, basis, cost, t_type):
        import csv
        fields=[time, wallet.name, wallet.coins[token].ticker, amount, basis, cost, t_type]
        with open(r'transactions.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(fields)
        f.close()

class Calc():
    def avg(token, all=False):
        pass
        # import pandas as pd
        # df = pd.read_csv('transactions.csv', names=['timestamp', 'wallet', 'token', 'amount', 'est_value', 'type'])
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

    




        

