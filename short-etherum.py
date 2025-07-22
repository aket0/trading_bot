import requests
import time
import pandas as pd
import matplotlib.pyplot as plt

class TradingBot:
    def __init__(self, initial_balance):
        self.initial_balance = initial_balance
        self.balance = initial_balance  # Capital fictif en USD
        self.eth_balance = 0  # Quantité d'ETH détenue
        self.trade_history = []  # Historique des transactions
        self.net_worth_history = []  # Historique de la valeur nette

    def buy(self, price):
        if self.balance > 0:
            self.eth_balance = self.balance / price
            self.trade_history.append(("BUY", price, self.eth_balance))
            self.balance = 0
            print(f"Achat simulé : {self.eth_balance} ETH à {price} USD")

    def sell(self, price):
        if self.eth_balance > 0:
            self.balance = self.eth_balance * price
            self.trade_history.append(("SELL", price, self.balance))
            self.eth_balance = 0
            print(f"Vente simulée : {self.balance} USD à {price} USD")

    def short(self, price):
        if self.balance > 0:
            self.eth_balance = -(self.balance / price)  # Quantité négative d'ETH pour simuler un short
            self.trade_history.append(("SHORT", price, self.eth_balance))
            self.balance = 0
            print(f"Short simulé : {self.eth_balance} ETH à {price} USD")

    def cover(self, price):
        if self.eth_balance < 0:  # Si on est en position short
            self.balance = -self.eth_balance * price
            self.trade_history.append(("COVER", price, self.balance))
            self.eth_balance = 0
            print(f"Cover simulé : {self.balance} USD à {price} USD")

    def show_performance(self, current_price):
        net_worth = self.balance + (self.eth_balance * current_price)
        profit = net_worth - self.initial_balance
        self.net_worth_history.append(net_worth)
        print(f"\nPerformance actuelle :")
        print(f"Valeur nette : {net_worth:.2f} USD")
        print(f"Profit/Pertes : {profit:.2f} USD")
        print(f"Transactions totales : {len(self.trade_history)}")

    def plot_performance(self):
        plt.figure(figsize=(12, 6))
        plt.plot(self.net_worth_history, label="Valeur nette ($)", color="blue")
        plt.title("Évolution de la valeur nette au fil du temps")
        plt.xlabel("Itérations")
        plt.ylabel("Valeur nette en USD")
        plt.legend()
        plt.show()


def fetch_ohlcv(symbol='ETHUSDT', interval='1m', limit=100):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]


def simple_moving_average(data, period=14):
    return data['close'].rolling(window=period).mean()

def rsi(data, period=14):
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def trade_signal(data):
    data['SMA_50'] = simple_moving_average(data, 50)
    data['SMA_200'] = simple_moving_average(data, 200)
    data['RSI'] = rsi(data)
    last_row = data.iloc[-1]

    if last_row['SMA_50'] > last_row['SMA_200'] and last_row['RSI'] < 30:
        return 'BUY'
    elif last_row['SMA_50'] < last_row['SMA_200'] and last_row['RSI'] > 70:
        return 'SELL'
    elif last_row['SMA_50'] < last_row['SMA_200'] and last_row['RSI'] < 30:
        return 'SHORT'
    elif last_row['SMA_50'] > last_row['SMA_200'] and last_row['RSI'] > 70:
        return 'COVER'
    return 'HOLD'

def main():
    bot = TradingBot(initial_balance=1000)  # Capital fictif de 1000 USD
    symbol = 'ETHUSDT'
    interval = '1m'

    for _ in range(30):  # On limite à 30 itérations pour l'affichage du graphe
        data = fetch_ohlcv(symbol, interval)
        signal = trade_signal(data)
        price = data['close'].iloc[-1]

        if signal == 'BUY':
            bot.buy(price)
        elif signal == 'SELL':
            bot.sell(price)
        elif signal == 'SHORT':
            bot.short(price)
        elif signal == 'COVER':
            bot.cover(price)
        else:
            print('Aucune action. En attente du prochain signal...')

        bot.show_performance(price)

        time.sleep(60)  # Attendre une minute avant la prochaine itération

    bot.plot_performance()

if __name__ == '__main__':
    main()
