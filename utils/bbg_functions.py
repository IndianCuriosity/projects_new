import pdblp
import xbbg
import pandas as pd
import numpy as np

from datetime import datetime, timedelta, date 
from pandas.tseries.offsets import BDay

today = (datetime.today()).strftime('%Y-%m-%d')
yesterday = (datetime.today()+ BDay(-1)).strftime('%Y-%m-%d')

""" 

con = pdblp.BCon(debug=False, port = 8194, timeout=2000)
con.start()
def pdblp_hist(tickers = ['EURUSD Curncy'], fields = ['LAST_PRICE'], start_date = yesterday, end_date = yesterday):

    df = con.bdh(tickers=tickers,flds=fields, start_date=start_date.replace('-',''),end_date=end_date.replace('-',''))
    df = df.columns.droplevel(1)
    df.columns = fields

    return df
 """
def xbbg_hist(tickers = ['EURUSD Curncy'], fields = ['LAST_PRICE'], start_date = yesterday, end_date = yesterday):

    df = xbbg.bdh(tickers=tickers,flds=fields, start_date=start_date,end_date=end_date)
    df = df.to_pandas()
    df = df.pivot_table(index=['ticker','date'], columns='field', values='value')

    return df