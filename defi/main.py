class Coin():
    def __init__(self, coin, ticker, price, holdings):
        self.name = coin
        self.ticker = ticker
        self.price = price
        self.holdings = holdings

    def update(self):
        import defi_tools as dft
        self.price = dft.geckoPrice(self.name)[self.name]['usd']
        return self

    def value(self):
        return self.price * self.holdings


class Wallet():
    def __init__(self, name):
        self.name = name
        self.coins = {'usd':Coin('usd', 'USD', 1, 0)}
        self.value = 0
        self.transactions = {'date':[], 'token':[], 'amount':[], 'basis': [], 'cost':[], 'type':[], 'profit':[]}

    def add(self, asset):
        self.coins[asset.name] = asset

    def addtxn(self, time, token, amount, basis, cost, fee, type, profit=0):
        self.transactions['date'].append(time)
        self.transactions['token'].append(token)
        self.transactions['amount'].append(amount)
        self.transactions['basis'].append(basis)     
        self.transactions['cost'].append(cost)
        self.transactions['type'].append(type)
        self.transactions['profit'].append(profit)

    def updatePrices(self):
        for c in self.coins:
            if c == 'usd':
                pass
            else:
                self.coins[c].update

    def totalValue(self):
        Wallet.updatePrices(self)
        # assets = [a for a in self.coins.values()]
        # total = sum([c.value for c in assets])
        total = sum([a.value() for a in self.coins.values()])
        self.value = total
        print(f'Total Value: {total}')
        return total
        
    def tokens(self, token):
        try:
            return self.coins[token].holdings
        except NameError:
            print('Coin not in portfolio.')

    def hasToken(self, token):
        try:
            return self.coins[token]
        except KeyError:
            return None

    def update(self, token, amount, overwrite=False):
        if overwrite:
            self.coins[token].holdings = amount
        else:    
            self.coins[token].holdings += amount

    def getHoldings(self):
        return {self.coins[k].ticker:self.coins[k].holdings for k in self.coins if self.coins[k].holdings!=0}

    def getValues(self):
        Wallet.updatePrices(self)
        return {self.coins[k].ticker:self.coins[k].value() for k in self.coins if self.coins[k].holdings!=0}

    def show(self):
        import pandas as pd
        holdings = Wallet.getHoldings(self)
        values = Wallet.getValues(self)
        total = self.value
        if total == 0:
            total = Wallet.totalValue(self)
        allocation = [float(values[v])/total for v in values if v > 0]
        return pd.DataFrame({'coin':holdings.keys(),'holdings':holdings.values(), 'value':values.values(), 'allocation':allocation})

class Transaction():

    def send(time, origin, token, amount, fee, type='send'):
        f_tk = fee[0]
        f_amt = fee[1]
        import defi_tools as dft
        if not time:
            from datetime import datetime
            time = datetime.now()
        
        if token != 'usd':    
            basis = dft.geckoPriceAt(token, time)
            f_usd = basis * f_amt
            basis += f_usd
        else:
            basis = 1
            f_usd = f_amt

        cost = basis*amount
        
        origin.update(token, -amount)
        Transaction.add(time, origin, token, amount, basis, cost, f_usd, type)
        print(f'Sent {amount} {origin.coins[token].ticker} from {origin.name}')

    def receive(time, destination, token, amount, type='receive'):                
        import defi_tools as dft
        if not time:
            from datetime import datetime
            time = datetime.now()
        if not destination.hasToken(token):
            import defi_tools as dft
            coin = Coin(coin=token, ticker=dft.geckoGetSymbol(token), price=dft.geckoPriceAt(token, time), holdings=amount)
            destination.add(coin)
        else:
            destination.update(token, amount)
        
        if token != 'usd':    
            basis = dft.geckoPriceAt(token, time)
        else:
            basis = 1
        
        cost = basis*amount
        Transaction.add(time, destination, token, amount, basis, cost, 0, type)
        print(f'Received {amount} {token} at {destination.name}')

    def transfer(time, origin, destination, token, amount, fee):
        if not time:
            from datetime import datetime
            time = datetime.now()
        Transaction.send(time, origin, token, amount, fee)
        Transaction.receive(time, destination, token, amount)
        print(f'Transferred {amount} {origin.coins[token].ticker} from {origin.name} to {destination.name}')

    def transact(time, wallet, buy, sell, fee, type):
        import defi_tools as dft
        if not time:
            from datetime import datetime
            time = datetime.now()
        b_tk = buy[0]
        b_amt = buy[1]
        s_tk = sell[0]
        s_amt = sell[1]
        Transaction.send(time, wallet, s_tk, s_amt, fee, 'sell')
        Transaction.receive(time, wallet, b_tk, b_amt, 'buy')
        
        # if not wallet.hasToken(b_tk):
        #     import defi_tools as dft
        #     coin = Coin(coin=b_tk, ticker=dft.geckoGetSymbol(b_tk), price=dft.geckoPriceAt(b_tk, time), holdings=0)
        #     wallet.add(coin)
        
        # if b_tk != 'usd':    
        #     basis = dft.geckoPriceAt(b_tk, time)
        # else:
        #     basis = 1
        # if f_tk != 'usd':
        #     f_usd = dft.geckoPriceAt(f_tk, time) * f_amt
        
        # cost = (basis*b_amt)+f_amt
        # Transaction.add(time, wallet, buy[0], b_amt, basis, cost, 'buy')
        
        # if s_tk != 'usd':    
        #     basis = dft.geckoPriceAt(s_tk, time)
        # else:
        #     basis = 1
        
        # cost = basis*s_amt
        # Transaction.add(time, wallet, sell[0], s_amt, basis,  cost, 'sell')

        # wallet.update(b_tk, b_amt)
        # wallet.update(s_tk, -s_amt)
        if type == 'Buy':
            print(f'Bought {b_amt} {wallet.coins[b_tk].ticker} with {s_amt} {wallet.coins[s_tk].ticker}.')
        elif type == 'Sell':
            print(f'Sold {s_amt} {wallet.coins[s_tk].ticker} and made {b_amt} {wallet.coins[b_tk].ticker}.')
        print(f'{wallet.coins[b_tk].ticker} Balance: {wallet.coins[b_tk].holdings}')
        print(f'{wallet.coins[s_tk].ticker} Balance: {wallet.coins[s_tk].holdings}')
    
    def add(time, wallet, token, amount, basis, cost, fee, t_type, profit=0):
        wallet.addtxn(time, token, amount, basis, cost, fee, t_type, profit)
        import csv
        fields=[time, wallet.name, wallet.coins[token].ticker, amount, basis, cost, fee, t_type]
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

    




        

