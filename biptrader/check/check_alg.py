""" check_alg :
    3/31/2022 8:04 AM
    ...
"""
__author__ = "Adel Ramezani <adramazany@gmail.com>"

import numpy as np
import pandas as pd
import talib as ta

from biptrader.check.pattern_recognition import CandlestickPattern


class CheckTradeAlgorithm:

    def __init__(self,df=None,INVESTMENT_AMOUNT_DOLLARS=100,price_column="Close",date_column="Date"):
        self.df = df
        self.INVESTMENT_AMOUNT_DOLLARS=INVESTMENT_AMOUNT_DOLLARS
        self.price_column = price_column
        self.date_column = date_column
        self.calculation_mode = "single_hold" # single_hold | waterfall_hold | expo_waterfall_hold
        self.waterfall_hold_pct = 0.1
        self.expo_waterfall_hold_rate = 1.5

    def signal(self,fn_recommendation):
        df = self.df
        counter =0
        for i,row in df.iterrows():
            if counter>0:
                ticker_df_before_date = df[df.Date<=row[self.date_column]]
                signal = fn_recommendation(ticker_df_before_date)
                df._set_value(i,"signal",signal)
            counter+=1

    def calculate_profit(self):
        if self.calculation_mode=="waterfall_hold":
            self._calculate_waterfall_profit()
        elif self.calculation_mode=="expo_waterfall_hold":
            self._calculate_expo_waterfall_profit()
        else:
            self._calculate_single_profit()

    def _calculate_single_profit(self):
        if not "revenue" in self.df.columns or not "profit" in self.df.columns :
            self.df=self.df.assign(revenue=[None]*len(self.df),profit=[None]*len(self.df))

        counter =0
        df = self.df

        HOLDING_QUANTITY=None
        for i,row in df.iterrows():
            if counter>0:
                current_price = float(row[self.price_column])
                if row["signal"]=="BUY" and not HOLDING_QUANTITY:
                    HOLDING_QUANTITY = round(self.INVESTMENT_AMOUNT_DOLLARS/current_price,5)
                    df._set_value(i,"revenue",-self.INVESTMENT_AMOUNT_DOLLARS)
                    df._set_value(i,"profit",0)
                elif row["signal"]=="SELL" and HOLDING_QUANTITY:
                    revenue = HOLDING_QUANTITY*current_price
                    profit=revenue-self.INVESTMENT_AMOUNT_DOLLARS
                    df._set_value(i,"revenue",revenue)
                    df._set_value(i,"profit",profit)
                    self.INVESTMENT_AMOUNT_DOLLARS=revenue
                    HOLDING_QUANTITY=None
            counter+=1

    def _calculate_waterfall_profit(self):
        pass

    def _calculate_expo_waterfall_profit(self):
        pass

    def get_revenue(self):
        return self.df["revenue"].sum() if "revenue" in self.df.columns else 0

    def get_profit(self):
        return self.df[self.df.signal=="SELL"]["profit"].sum() if "signal" in self.df.columns else 0

    def get_buy_signal_count(self):
        return len(self.df[self.df.signal=="BUY"]) if "signal" in self.df.columns else 0

    def get_sell_signal_count(self):
        return len(self.df[self.df.signal=="SELL"]) if "signal" in self.df.columns else 0

    def get_summary(self):
        return "{revenue:%f,profit:%f,remain:%f,buy_signal_count:%i,sell_signal_count:%i}"\
               %(self.get_revenue(),self.get_profit(),self.INVESTMENT_AMOUNT_DOLLARS
                 ,self.get_buy_signal_count(),self.get_sell_signal_count())


    def get_technical_indicators(self):
        df = self.df
        # Technical Analysis
        SMA_FAST = 50
        SMA_SLOW = 200
        RSI_PERIOD = 14
        RSI_AVG_PERIOD = 15
        MACD_FAST = 12
        MACD_SLOW = 26
        MACD_SIGNAL = 9
        STOCH_K = 14
        STOCH_D = 3
        SIGNAL_TOL = 3
        Y_AXIS_SIZE = 12

        analysis = pd.DataFrame(index = df.index)
        analysis["Date"]=self.df["Date"]
        # macd, signal, hist = ta.MACD(df['close'], fastperiod = 12, slowperiod = 26, signalperiod = 9)
        analysis['sma_f'] = df["Close"].rolling(SMA_FAST).mean()  # pd.rolling_mean(df.Close, SMA_FAST)  # module 'pandas' has no attribute 'rolling_mean'
        analysis['sma_s'] = df["Close"].rolling(SMA_SLOW).mean()  # pd.rolling_mean(df.Close, SMA_SLOW)
        analysis['rsi'] =   ta.RSI(df.Close.to_numpy(), RSI_PERIOD)  # ta.RSI(df.Close.as_matrix(), RSI_PERIOD) # AttributeError: 'Series' object has no attribute 'as_matrix'
        analysis['sma_r'] = analysis['rsi'].rolling(RSI_AVG_PERIOD).mean()  # pd.rolling_mean(analysis.rsi, RSI_AVG_PERIOD) # check shift
        analysis['macd'], analysis['macdSignal'], analysis['macdHist'] = ta.MACD(df.Close.to_numpy(), fastperiod=MACD_FAST, slowperiod=MACD_SLOW, signalperiod=MACD_SIGNAL) # ta.MACD(df.Close.as_matrix(), fastperiod=MACD_FAST, slowperiod=MACD_SLOW, signalperiod=MACD_SIGNAL)
        analysis['stoch_k'], analysis['stoch_d'] = ta.STOCH(df.High.to_numpy(), df.Low.to_numpy(), df.Close.to_numpy(), slowk_period=STOCH_K, slowd_period=STOCH_D) # ta.STOCH(df.High.as_matrix(), df.Low.as_matrix(), df.Close.as_matrix(), slowk_period=STOCH_K, slowd_period=STOCH_D)

        analysis['wma_m'] = ta.WMA(df.Close.to_numpy(),timeperiod=30)
        analysis['wma_f'] = ta.WMA(df.Close.to_numpy(),timeperiod=20)
        analysis['wma_s'] = ta.WMA(df.Close.to_numpy(),timeperiod=50)

        analysis['sma'] = np.where(analysis.sma_f > analysis.sma_s, 1, 0)
        analysis['macd_test'] = np.where((analysis.macd > analysis.macdSignal), 1, 0)
        analysis['stoch_k_test'] = np.where((analysis.stoch_k < 50) & (analysis.stoch_k > analysis.stoch_k.shift(1)), 1, 0)
        analysis['rsi_test'] = np.where((analysis.rsi < 50) & (analysis.rsi > analysis.rsi.shift(1)), 1, 0)

        # print(analysis.to_string())
        return analysis

    def get_patterns(self):
        df = self.df
        cp = CandlestickPattern()
        patterns = cp.pattern_recognition(df)
        return cp.pattern_match(patterns)


