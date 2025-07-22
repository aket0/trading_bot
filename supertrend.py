import requests
import time
import pandas as pd
import numpy as np
import inquirer  # Pour la sélection interactive

class TradingBot:
    def __init__(self, initial_balance, stop_loss_percent=0.02, take_profit_percent=0.05):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.crypto_balance = 0
        self.trade_history = []
        self.net_worth_history = []
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        self.buy_price = 0

    def buy(self, price, iteration):
        if self.balance > 0:
            self.crypto_balance = self.balance / price
            self.buy_price = price
            self.trade_history.append(("BUY", price, self.crypto_balance))
            self.balance = 0
            print(f"[{iteration}] Achat simulé : {self.crypto_balance:.4f} crypto à {price:.2f} USD")

    def sell(self, price, iteration):
        if self.crypto_balance > 0:
            self.balance = self.crypto_balance * price
            self.trade_history.append(("SELL", price, self.balance))
            self.crypto_balance = 0
            print(f"[{iteration}] Vente simulée : {self.balance:.2f} USD à {price:.2f} USD")

    def show_performance(self, current_price, iteration):
        net_worth = self.balance + (self.crypto_balance * current_price)
        profit = net_worth - self.initial_balance
        self.net_worth_history.append(net_worth)
        print(f"\nPerformance après itération {iteration}:")
        print(f"Valeur nette : {net_worth:.2f} USD")
        print(f"Profit/Pertes : {profit:.2f} USD")
        print(f"Transactions totales : {len(self.trade_history)}")

    def manage_risk(self, price, iteration):
        if self.crypto_balance > 0:
            stop_loss_price = self.buy_price * (1 - self.stop_loss_percent)
            take_profit_price = self.buy_price * (1 + self.take_profit_percent)

            if price <= stop_loss_price:
                print(f"[{iteration}] Stop-Loss atteint à {price:.2f} USD. Vente effectuée.")
                return 'SELL'
            elif price >= take_profit_price:
                print(f"[{iteration}] Take-Profit atteint à {price:.2f} USD. Vente effectuée.")
                return 'SELL'
        return 'HOLD'


def fetch_ohlcv(symbol='ETHUSDT', interval='1m', limit=100):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                     'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                                     'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
    return df[['timestamp', 'open', 'high', 'low', 'close']]


def supertrend(data, period=10, multiplier=3):
    atr = data['high'].rolling(window=period).max() - data['low'].rolling(window=period).min()
    hl2 = (data['high'] + data['low']) / 2
    basic_upper_band = hl2 + (multiplier * atr)
    basic_lower_band = hl2 - (multiplier * atr)
    
    supertrend = np.zeros(len(data))
    in_uptrend = True
    for i in range(1, len(data)):
        if data['close'][i] > basic_upper_band[i-1]:
            in_uptrend = True
        elif data['close'][i] < basic_lower_band[i-1]:
            in_uptrend = False

        supertrend[i] = basic_upper_band[i] if in_uptrend else basic_lower_band[i]
    
    return supertrend


def trade_signal(data):
    data['Supertrend'] = supertrend(data)
    last_row = data.iloc[-1]

    print(f"Supertrend: {last_row['Supertrend']:.2f}, Close: {last_row['close']:.2f}")

    if last_row['close'] > last_row['Supertrend']:
        return 'BUY'
    elif last_row['close'] < last_row['Supertrend']:
        return 'SELL'
    return 'HOLD'


def select_crypto():
    questions = [
        inquirer.List('crypto',
                      message="Choisissez la cryptomonnaie à trader",
                      choices=['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT', 'LTCUSDT', 'SOLUSDT', 'DOGEUSDT', 'SHIBUSDT'],
                      ),
    ]
    answers = inquirer.prompt(questions)
    return answers['crypto']


def main():
    symbol = select_crypto()
    print(f"Vous avez sélectionné {symbol} pour le trading.")
    
    bot = TradingBot(initial_balance=1000)
    interval = '1m'

    iteration = 0
    while True:
        iteration += 1
        data = fetch_ohlcv(symbol, interval)
        signal = trade_signal(data)
        price = data['close'].iloc[-1]

        print(f"\n--- Iteration {iteration} ---")
        print(f"Prix actuel : {price:.2f} USD")

        if signal == 'BUY':
            bot.buy(price, iteration)
        elif signal == 'SELL':
            bot.sell(price, iteration)
        else:
            print(f"[{iteration}] Aucune action. En attente du prochain signal...")

        action = bot.manage_risk(price, iteration)
        if action == 'SELL':
            bot.sell(price, iteration)

        bot.show_performance(price, iteration)
        time.sleep(1)

if __name__ == '__main__':
    main()
