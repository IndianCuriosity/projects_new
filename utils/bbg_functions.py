import pdblp
import xbbg
import pandas as pd
import numpy as np
import copy

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

def xbbg_bdp_value_dates(tickers = ['EURUSD Curncy'], ref_dates =  [yesterday,today]):
    ref_dates_YYYYMMDD = [d.replace('-','') for d in ref_dates]
    fields = ['SETTLE_DT']

    for ref_date_YYYYMMDD, ref_date in zip(ref_dates_YYYYMMDD, ref_dates):
        df = xbbg.bdp(tickers=tickers,flds=fields, REFERENCE_DATE=ref_date_YYYYMMDD)
        df = df.to_pandas()
        df['ref_date'] = ref_date
        if ref_date == ref_dates[0]:
            df_master = copy.deepcopy(df)
        else:
            df_master = pd.concat([df_master, df], axis=0)
        print (ref_date)
    df_master.reset_index(drop=True, inplace=True)
    df_master = df_master.groupby(['ticker', 'ref_date'])[['value']].first()

    return df_master            
    
def xbbg_bdp_option_expiry_dates(tickers = ['EURUSD Curncy'], expiry_tenors = ['1M', '3M', '6M'], ref_dates =  [yesterday,today]):
    ref_dates_YYYYMMDD = [d.replace('-','') for d in ref_dates]
    fields = ["VOL_SURF_EXPIRY_OVR"]

    for ref_date_YYYYMMDD, ref_date in zip(ref_dates_YYYYMMDD, ref_dates):
        for expiry_tenor in expiry_tenors:
                
            df = xbbg.bdp(tickers=tickers,flds=fields, VOL_SURF_MTY_OVR=expiry_tenor, REFERENCE_DATE=ref_date_YYYYMMDD)
            df = df.to_pandas()
            df['ref_date'] = ref_date
            df['expiry_tenor'] = expiry_tenor
            if ref_date == ref_dates[0]:
                df_master = copy.deepcopy(df)
            else:
                df_master = pd.concat([df_master, df], axis=0)
            print (ref_date)

    df_master.reset_index(drop=True, inplace=True)
    df_master = df_master.groupby(['ticker', 'ref_date', 'expiry_tenor'])[['value']].first()

    return df_master            
    


