from kiteconnect import KiteConnect
from selenium import webdriver
import time 
import os 
import pandas as pd
import numpy as np
import datetime as dt

access_token=open('access_token.txt','r').read()
token_path=r'C:\Users\abhinav\.spyder-py3\detail.txt'
key_secret = open(token_path,'r').read().split()
kite=KiteConnect(api_key=key_secret[0])

kite.set_access_token(access_token)

instrument_dump =kite.instruments('NSE')
instrument_df =pd.DataFrame(instrument_dump)
instrument_df.to_csv("NSE_Instruments_312.csv",index=False)

def instrumentLookup(instrument_df,symbol):
    return int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token)
    
    
def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval))
    data.set_index("date",inplace=True)
    return data


def macd(ohlc):
    df=ohlc.copy()
    df['12MA']=df['close'].ewm(span=12,min_periods=12).mean()
    df['26MA']=df['close'].ewm(span=26,min_periods=26).mean()
    df['macd']=df['12MA']-df['26MA']
    df['signal']=df['macd'].ewm(span=9,min_periods=9).mean()
    df.drop('12MA',axis=1)
    df.drop('26MA',axis=1)
    return df

def exp_avg (ohlc):
    df=ohlc.copy()
    df['3ema']=df['close'].ewm(span=3,min_periods=3).mean()
    df['6ema']=df['close'].ewm(span=6,min_periods=6).mean()
    df['9ema']=df['close'].ewm(span=9,min_periods=9).mean()
    return df

def rsi(ohlc):
    data=ohlc.copy()
    data['diff']=data['close'].diff(1)
    data['gain']=np.where(data['diff']>0 ,data['diff'],np.nan)
    data['loss']=np.where(data['diff']<0,data['diff'],np.nan)
    data['avg_gain']=data['gain'].rolling(14,min_periods=1).mean()
    data['avg_loss']=data['loss'].rolling(14,min_periods=1).mean()
    rs =abs(data['avg_gain']/data['avg_loss'])
    data['rsi']= 100 - (100/(1+rs))
    data=data.drop(['gain','loss','avg_loss','avg_gain'],axis=1)
    return data



def atr(DF):
    df=DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR']=df['TR'].rolling(14).mean()
    
    return df

atr
tickers=['ACC','TCS','INFY','SBIN','NTPC','HDFCBANK','ASIANPAINT','ICICIBANK','UPL',
        'SUNPHARMA']

def winRate(DF):
    df=DF['return']
    pos=df[df>1]
    neg=df[df<1]
    return (len(pos)/len(pos+neg))
def meanretpertrade(DF):
    df=DF['return']
    df_temp = (df-1).dropna()
    return df_temp[df_temp!=0].mean()

def meanretwintrade(DF):
    df=DF['return']
    df_temp =(df-1).dropna()
    return df_temp[df_temp>0].mean()

def meanretlosstrade(DF):
    df=DF['return']
    df_temp=(df-1).dropna()
    return df_temp[df_temp<0].mean()

ohlc_dict ={}
for ticker in tickers:
    ohlc_dict[ticker]=fetchOHLC(ticker,'5minute',35)


ticker_signal={}
ticker_ret={}
trade_count={}
trade_data={}


for ticker in tickers :
    ohlc_dict[ticker]['macd']=macd(ohlc_dict[ticker])['macd']
    ohlc_dict[ticker]['macd_signal']=macd(ohlc_dict[ticker])['signal']
    ohlc_dict[ticker]['ema9']= exp_avg(ohlc_dict[ticker])['9ema']
    ohlc_dict[ticker]['ema3']= exp_avg(ohlc_dict[ticker])['3ema']
    ohlc_dict[ticker]['rsi']=rsi(ohlc_dict[ticker])['rsi']
    ohlc_dict[ticker]['atr']=atr(ohlc_dict[ticker])['rsi']
    ohlc_dict[ticker].dropna(inplace=True)
    trade_count[ticker]=0
    ticker_signal[ticker]=""
    ticker_ret[ticker]=[0]
    trade_data[ticker]={}



ohlc_dict["ACC"]

ticker_signal["ACC"]
ticker_signal

for ticker in tickers:
    print('ashu ruko thoda going through :')
    for i in range(1,len(ohlc_dict[ticker])):
    
        if ticker_signal[ticker] == "" :
            
            
            ticker_ret[ticker].append(0)
            if ohlc_dict[ticker]['rsi'][i] >= 70 and ohlc_dict[ticker]['ema3'][i] > ohlc_dict[ticker]['ema9'][i]:
                ticker_signal[ticker]='BUY'
                trade_count[ticker]+=1
                trade_data[ticker][trade_count[ticker]]=[ohlc_dict[ticker]['close'][i]]
                
        elif ticker_signal[ticker]=="BUY":
            if ohlc_dict[ticker]['low'][i] < ohlc_dict[ticker]['close'][i-1]-ohlc_dict[ticker]['atr'][i-1] :
                ticker_signal[ticker]=""
                trade_data[ticker][trade_count[ticker]].append(ohlc_dict[ticker]['close'][i-1]-ohlc_dict[ticker]['atr'][i-1])
                trade_count[ticker]+=1
                ticker_ret[ticker].append(((ohlc_dict[ticker]['close'][i-1]-ohlc_dict[ticker]['atr'][i-1])/ohlc_dict[ticker]['close'][i-1])-1)
            else:
                 ticker_ret[ticker].append((ohlc_dict[ticker]['close'][i]/ohlc_dict[ticker]['close'][i-1])-1)
                 
    if trade_count[ticker]%2 !=0:
        trade_data[ticker][trade_count[ticker]].append(ohlc_dict[ticker]['close'][i])
    ohlc_dict[ticker]['ret']=np.array(ticker_ret[ticker])
            
for ticker in tickers:
    print(ticker, ohlc_dict[ticker]['ret'].mean())
    
trade_df={}
for ticker in tickers:
    trade_df[ticker]=pd.DataFrame(trade_data[ticker]).T 
    trade_df[ticker].columns=['trade_entry_pr','trade_exit_pr']
    trade_df[ticker]['return']=trade_df[ticker]['trade_exit_pr']/trade_df[ticker]['trade_entry_pr']

win_rate={}
mean_ret_pt={}
mean_ret_pwt={}
mean_ret_plt={}


for ticker in tickers:
    print('aPI for',ticker)
    win_rate[ticker]=winRate(trade_df[ticker])
    mean_ret_pt[ticker]=meanretpertrade(trade_df[ticker])
    mean_ret_pwt[ticker]=meanretwintrade(trade_df[ticker])
    mean_ret_plt[ticker]=meanretlosstrade(trade_df[ticker])
    
    
df=pd.DataFrame([win_rate,mean_ret_pt,mean_ret_pwt,mean_ret_plt,],index=['win rate','mean retuen per trade','mean per profit','mr per loss'])   

df.T


ticker=['ICICIBANK']