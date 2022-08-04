from kiteconnect import KiteConnect
from selenium import webdriver
import time 
import os 
import pandas as pd
import numpy as np
import datetime as dt
import numpy as np

access_token=open('access_token.txt','r').read()
token_path=r'C:\Users\meeta\.spyder-py3\detail.txt'
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


def bollBnd(DF,n):
    df=DF.copy()
    df['MA']=df['close'].rolling(n).mean()
    df['BB_2up']=df['MA']+2*df['MA'].std()
    df['BB_2dn']=df['MA']-2*df['MA'].rolling(n).std()
    df['BB_1up']=df['MA']+df['MA'].rolling(n).std()
    df['BB_1dn']=df['MA'] -df['MA'].rolling(n).std()
    
    df.dropna(inplace=True)
    return df

tickers=['ICICIBANK']



ohlc_dict ={}
for ticker in tickers:
    ohlc_dict[ticker]=fetchOHLC(ticker,'15minute',45)
    
for ticker in tickers:
    ohlc_dict[ticker]=bollBnd(ohlc_dict[ticker],20)
    

ticker_signal={}
ticker_ret={}
trade_count={}
trade_data={}
trade_exit={}
target =0
stoploss=0
trade_time={}

for ticker in tickers:
    trade_count[ticker]=0
    ticker_signal[ticker]=""
    ticker_ret[ticker]=[0,0,0]
    trade_data[ticker]={}
    trade_time[ticker]={}


for ticker in tickers:
    for i in range(3,len(ohlc_dict[ticker])):
        if ticker_signal[ticker] == "" :
            ticker_ret[ticker].append(0)
            
            if ohlc_dict[ticker]['close'][i-2] < ohlc_dict[ticker]['BB_1up'][i-2] and ohlc_dict[ticker]['close'][i-1] < ohlc_dict[ticker]['BB_1up'][i-1] and ohlc_dict[ticker]['close'][i] >= ohlc_dict[ticker]['BB_1up'][i]  and ohlc_dict[ticker]['close'][i] < ohlc_dict[ticker]['BB_2up'][i]:
               
                ticker_signal[ticker]='BUY'
                trade_count[ticker]+=1
                trade_data[ticker][trade_count[ticker]]=[ohlc_dict[ticker]['close'][i]]
                target = (20*ohlc_dict[ticker]['close'][i])/100 + ohlc_dict[ticker]['close'][i]
                trade_time[ticker][trade_count[ticker]]=[ohlc_dict[ticker].index[i]]
                
                stoploss =  ohlc_dict[ticker]['close'][i] - 10*(ohlc_dict[ticker]['close'][i])/100 
        elif ticker_signal[ticker]=='BUY':
            
            if ohlc_dict[ticker]['high'][i] >= target:
                ticker_signal[ticker]=""
                trade_data[ticker][trade_count[ticker]].append(target)
                trade_time[ticker][trade_count[ticker]].append([ohlc_dict[ticker].index[i]])
                
                trade_count[ticker]+=1
                ticker_ret[ticker].append(target/ohlc_dict[ticker]['close'][i]  -1)
            elif ohlc_dict[ticker]['low'][i] <= stoploss:
                ticker_signal[ticker]=""
                trade_data[ticker][trade_count[ticker]].append(stoploss)
                trade_time[ticker][trade_count[ticker]].append([ohlc_dict[ticker].index[i]])
                trade_count[ticker]+=1
                ticker_ret[ticker].append(stoploss/ohlc_dict[ticker]['close'][i]  -1)
                
            else :
                ticker_ret[ticker].append((ohlc_dict[ticker]['close'][i]/ohlc_dict[ticker]['close'][i-1])-1)
                
    if trade_count[ticker]%2 !=0:
        trade_data[ticker][trade_count[ticker]].append(ohlc_dict[ticker]['close'][i])
        trade_time[ticker][trade_count[ticker]].append([ohlc_dict[ticker].index[i]])
    ohlc_dict[ticker]['ret']=np.array(ticker_ret[ticker])
                
                  
               
for ticker in tickers:
    print(ticker,ohlc_dict[ticker]['ret'].mean())
            
          

trade_df={}
for ticker in tickers:
    trade_df[ticker]=pd.DataFrame(trade_data[ticker]).T 
    trade_df[ticker].columns=['trade_entry_pr','trade_exit_pr']
    trade_df[ticker]['return']=trade_df[ticker]['trade_exit_pr']/trade_df[ticker]['trade_entry_pr']
    time=pd.DataFrame(trade_time[ticker]).T
    time.columns=['entry_time','exit_time']
    
    trade_df[ticker]=time.join(trade_df[ticker])




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