import requests
import time
import pandas as pd
import numpy as np
import inquirer  # Pour la sélection interactive

class TradingBot:
    def __init__(self, initial_balance):
        self.initial_balance = initial_balance
        self.balance = initial_balance  # Capital fictif en USD
        self.crypto_balance = 0  # Quantité de crypto détenue (générique)
        self.trade_history = []  # Historique des transactions
        self.net_worth_history = []  # Historique de la valeur nette

    def buy(self, price, iteration):
        if self.balance > 0:
            self.crypto_balance = self.balance / price
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

def fetch_ohlcv(symbol='ETHUSDT', interval='1m', limit=100):
    """Récupère les données OHLCV (Open, High, Low, Close, Volume) pour une paire donnée"""
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df[['timestamp', 'close']]

def rsi(data, period=14):  # RSI modifié à 14
    """Calcul du RSI (Relative Strength Index)"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(data, fast_period=12, slow_period=26, signal_period=9):  # MACD standard
    """Calcul du MACD"""
    fast_ema = data['close'].ewm(span=fast_period, adjust=False).mean()
    slow_ema = data['close'].ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return macd_line, signal_line

def ultra_aggressive_trade_signal(data):
    """Logique ultra agressive pour acheter et vendre"""
    data['RSI'] = rsi(data)
    data['MACD_Line'], data['Signal_Line'] = macd(data)

    last_row = data.iloc[-1]
    
    # Afficher les valeurs RSI et MACD dans le terminal pour mieux comprendre les conditions
    print(f"RSI: {last_row['RSI']:.2f}, MACD Line: {last_row['MACD_Line']:.2f}, Signal Line: {last_row['Signal_Line']:.2f}")

    # Signaux de trading très agressifs : entrée immédiate dès qu'un signal RSI ou MACD apparaît
    if last_row['RSI'] > 70 and last_row['MACD_Line'] < last_row['Signal_Line']:  # Surachat
        return 'SELL'
    elif last_row['RSI'] < 30 and last_row['MACD_Line'] > last_row['Signal_Line']:  # Survente
        return 'BUY'
    return 'HOLD'

def select_crypto():
    """Sélectionne une cryptomonnaie à trader via un menu interactif"""
    questions = [
        inquirer.List('crypto',
                      message="Choisissez la cryptomonnaie à trader",
                      choices=['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT', 'LTCUSDT', 'SOLUSDT', 'DOGEUSDT', 'SHIBUSDT'],
                      ),
    ]
    answers = inquirer.prompt(questions)
    return answers['crypto']

def main():
    """Fonction principale"""
    symbol = select_crypto()

    print(f"Vous avez sélectionné {symbol} pour le trading.")
    
    bot = TradingBot(initial_balance=1000)  
    interval = '1m'

    iteration = 0
    while True:  
        iteration += 1
        data = fetch_ohlcv(symbol, interval)
        signal = ultra_aggressive_trade_signal(data)
        price = data['close'].iloc[-1]

        print(f"\n--- Iteration {iteration} ---")
        print(f"Prix actuel : {price:.2f} USD")

        if signal == 'BUY':
            bot.buy(price, iteration)
        elif signal == 'SELL':
            bot.sell(price, iteration)
        else:
            print(f"[{iteration}] Aucune action. En attente du prochain signal...")

        bot.show_performance(price, iteration)
        time.sleep(5)  # Pause légèrement plus longue pour éviter les trades trop fréquents

if __name__ == '__main__':
    main()
