from numpy import swapaxes


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

    def add(self, asset):
        self.coins[asset.name] = asset

    def updatePrices(self):
        for c in self.coins:
            if c == 'usd':
                pass
            else:
                self.coins[c].update

    def totalValue(self, profit=False):
        Wallet.updatePrices(self)
        if profit:
            total = sum([a.value() for a in self.coins.values()])
        else:
            total = sum([a.value() for a in self.coins.values() if a.value() > 0])
        self.value = total
        print(f'Total Value: {total}. (Profit: {profit})')
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
        allocation = [float(values[v])/total if values[v] > 0 else 0 for v in values]
        return pd.DataFrame({'coin':holdings.keys(),'holdings':holdings.values(), 'value':values.values(), 'allocation':allocation})
    
    def pnl(self):
        Wallet.totalValue(self, True)

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

        if type == 'sell':
            cost = 0
        else:
            cost = basis*amount

        origin.update(token, -amount)
        Transaction.add(time, origin, token, amount, basis, cost, f_usd, type)
        print(f'Sent {amount} {origin.coins[token].ticker} from {origin.name}')

    def receive(time, destination, token, amount, fee, type='receive'):                
        f_tk = fee[0]
        f_amt = fee[1]
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
            f_usd = basis * f_amt
            basis += f_usd
        else:
            basis = 1
            f_usd = f_amt
        
        cost = basis*amount
        Transaction.add(time, destination, token, amount, basis, cost, 0, type)
        print(f'Received {amount} {destination.coins[token].ticker} at {destination.name}')


    def transfer(time, origin, destination, token, amount, fee):
        if not time:
            from datetime import datetime
            time = datetime.now()
        Transaction.send(time, origin, token, amount, fee, 'transfer')
        Transaction.receive(time, destination, token, amount, 'transfer')
        print(f'Transferred {amount} {origin.coins[token].ticker} from {origin.name} to {destination.name}')

    def transact(time, origin, destination, type):
        import defi_tools as dft
        from numpy import round
        if not time:
            from datetime import datetime
            time = datetime.now()
        
        if origin:
            ow, otk, oamt, of = origin
            if type == 'send':
                # origin: -token, destination: None, fee: otk
                if otk != 'usd':    
                    basis = dft.geckoPriceAt(otk, time)
                    f_usd = basis * of
                    basis += f_usd
                    value = basis * oamt
                else:
                    basis = 1
                    f_usd = of
                    value = oamt
                ow.update(otk, -oamt)
                Transaction.add(time, ow, otk, oamt, f_usd, basis, value, type)
                print(f'Sent {oamt} {ow.coins[otk].ticker} from {ow.name}. ${round(value,2)}.')
                print(f'[{ow.name}] {ow.coins[otk].ticker} Balance: {ow.coins[otk].holdings}')
            if type == 'withdraw':
                ow.update(otk, -oamt)
                Transaction.add(time, ow, otk, oamt, 0, 1, oamt, type)
                print(f'Withdrew {oamt} {ow.coins[otk].ticker} from {ow.name}. ${round(oamt,2)}.')
                print(f'[{ow.name}] {ow.coins[otk].ticker} Balance: {ow.coins[otk].holdings}')

        if destination:
            dw, dtk, damt, df = destination
            if not dw.hasToken(dtk):
                import defi_tools as dft
                coin = Coin(coin=dtk, ticker=dft.geckoGetSymbol(dtk), price=dft.geckoPriceAt(dtk, time), holdings=0)
                dw.add(coin)
            if type == 'receive' or type == 'deposit':
                # origin: None, destination: +token, fee: 0
                if dtk != 'usd':    
                    basis = dft.geckoPriceAt(dtk, time)
                    value = basis * damt
                else:
                    basis = 1
                    value = damt
                dw.update(dtk, damt)    
                Transaction.add(time, dw, dtk, damt, df, basis, value, type)
                print(f'Received {damt} {dw.coins[dtk].ticker} at {dw.name}. ${round(value,2)}.')
                print(f'[{dw.name}] {dw.coins[dtk].ticker} Balance: {dw.coins[dtk].holdings}')

        if origin and destination:
            if type == 'sell':
                # origin: -token, destination: +usd, fee: usd (alt-usd)
                basis = damt / oamt
                value = damt
                df = 0
                ot = 'sell-out'
                dt = 'sell-in'
                print(f'Sold {oamt} {ow.coins[otk].ticker} got {damt} {dw.coins[dtk].ticker}.')
            
            elif type == 'buy':
                # origin: -usd, destination: +token, fee: usd (usd-alt)
                basis = oamt / damt
                value = oamt
                of = 0
                ot = 'buy-out'
                dt = 'buy-in'
                print(f'Bought {damt} {dw.coins[dtk].ticker} with {oamt} {ow.coins[otk].ticker}.')

            elif type == 'trade':
                # origin: -token, destination: +token, fee: dtk (alt-alt)
                value = oamt * dft.geckoPriceAt(otk, time)
                basis = value / damt
                of = 0
                ot = 'trade-sell'
                dt = 'trade-buy'
                print(f'Traded {oamt} {ow.coins[otk].ticker} for {damt} {dw.coins[dtk].ticker}. Value: ${round(value,2)}.')

            elif type == 'transfer':
                # origin: -token, destination: +token, fee: 0. (Coinbase Transfers)
                if otk != 'usd':    
                    basis = dft.geckoPriceAt(otk, time)
                    value = basis * oamt
                else:
                    basis = 1
                    value = oamt
                of = df = 0
                ot = 'transfer-out'
                dt = 'transfer-in'
                print(f'Transferred {oamt} {ow.coins[otk].ticker} from {ow.name} to {dw.name}. ${round(value,2)}.')

            ow.update(otk, -oamt)
            Transaction.add(time, ow, otk, oamt, of, basis, value, ot)
            dw.update(dtk, damt)
            Transaction.add(time, dw, dtk, damt, df, basis, value, dt)
            print(f'[{ow.name}] {ow.coins[otk].ticker} Balance: {ow.coins[otk].holdings}')
            print(f'[{dw.name}] {dw.coins[dtk].ticker} Balance: {dw.coins[dtk].holdings}')
        

    # def transact(time, wallet, buy, sell, fee, type):
    #     import defi_tools as dft
    #     if not time:
    #         from datetime import datetime
    #         time = datetime.now()
    #     b_tk = buy[0]
    #     b_amt = buy[1]
    #     s_tk = sell[0]
    #     s_amt = sell[1]
    #     Transaction.send(time, wallet, s_tk, s_amt, fee, 'sell')
    #     Transaction.receive(time, wallet, b_tk, b_amt, fee, 'buy')
       
        
    #     if type == 'Sell':
    #         print(f'Sold {s_amt} {wallet.coins[s_tk].ticker} and made {b_amt} {wallet.coins[b_tk].ticker}.')
    #     elif type == 'Buy':
    #         print(f'Bought {b_amt} {wallet.coins[b_tk].ticker} with {s_amt} {wallet.coins[s_tk].ticker}.')
        
    #     print(f'{wallet.coins[b_tk].ticker} Balance: {wallet.coins[b_tk].holdings}')
    #     print(f'{wallet.coins[s_tk].ticker} Balance: {wallet.coins[s_tk].holdings}')
    
    def add(time, wallet, token, amount, fee, basis, value, t_type, profit=0):
        import csv
        fields=[time, wallet.name, wallet.coins[token].ticker, amount, basis, value, fee, profit, t_type]
        with open(r'transactions.csv', 'a', newline='') as f:
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

    




        

