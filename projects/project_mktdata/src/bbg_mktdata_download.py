import blpapi
import pdblp
import xbbg

import pandas as pd
from pathlib import Path
import numpy as np
import copy
import os
import configparser
import json
import sys
import importlib


from datetime import datetime, timedelta, date
from pandas.tseries.offsets import BDay

from utils.bbg_functions import xbbg_hist

base_dir = os.environ.get('PROJECTS_NEW_HOME')
sys.path.append(base_dir + '\\utils\\')
from bbg_functions import *

config = configparser.ConfigParser()
config.read(base_dir + '\\configs\\fx_config.ini')


### currpairs ####
g10_currpairs = [c.strip() for c in config['currpairs']['g10_currpairs'].split(',')]
asia_deliv_currpairs = [c.strip() for c in config['currpairs']['asia_deliv_currpairs'].split(',')]
asia_nd_currpairs = [c.strip() for c in config['currpairs']['asia_nd_currpairs'].split(',')]
aud_cross_currpairs = [c.strip() for c in config['currpairs']['aud_cross_currpairs'].split(',')]

currpairs = g10_currpairs + asia_deliv_currpairs + asia_nd_currpairs + aud_cross_currpairs
currpairs = list(set(currpairs))

### ccys ####
g10_ccys = [c.strip() for c in config['ccys']['g10_ccys'].split(',')]
asia_deliv_ccys = [c.strip() for c in config['ccys']['asia_deliv_ccys'].split(',')]
asia_nd_ccys = [c.strip() for c in config['ccys']['asia_nd_ccys'].split(',')]

### bbg_fwds ###
asia_ndf_tickers = config['bbg_fwds']['as']

tickers_bfix_tky3pm = [f'{ccy} T150 Curncy' for ccy in (g10_ccys + asia_deliv_ccys)]
tickers_bfix_ldn4pm = [f'{ccy} L160 Curncy' for ccy in (g10_ccys)]
tickers_bfix_ny10am = [f'{ccy} F100 Curncy' for ccy in (g10_ccys)]
tickers_fixings_asia_dict = {'INRRATE Index': 'INR','KOBRUSD Index': 'KRW','TRY11 Index': 'TWD','PHFRRATE Index': 'PHP','JISDOR Index': 'IDR'}

fixing_tickers = tickers_bfix_tky3pm + tickers_bfix_ldn4pm + tickers_bfix_ny10am + list(tickers_fixings_asia_dict.keys())
tickers_all_dict = {'bfix_tky3pm':tickers_bfix_tky3pm,'bfix_ldn4pm':tickers_bfix_ldn4pm,'bfix_ny10am':tickers_bfix_ny10am,'fixings_asia':list(tickers_fixings_asia_dict.keys())}

#### tenors_list
tenors_list = [c.strip() for c in config['tenors']['bbg_tenors_list'].split(',')]
tenors_points_list = [c.strip() for c in config['tenors']['bbg_poins_tenors_list'].split(',')]

#### bbg source
bbg_vol_sources = json.loads(config["bbg_sources"]["vol_source"])

### bbg points short names
points_short_names = json.loads(config["points_short_names"]["short_names"])

### bbg impl yields short names
#impl_yields_tickers_dict = json.loads(config["bbg_tickers"]["bbg_imp_yields"])

#### dates ##############

pricing_date = (datetime.today()).strftime('%Y-%m-%d')
pricing_date_time = (datetime.today()).strftime('%Y-%m-%d-%H-%M-%w')
pricing_date_ystday = (datetime.today()+ BDay(-1)).strftime('%Y-%m-%d')
pricing_date_tomorrow = (datetime.today()+ BDay(1)).strftime('%Y-%m-%d')

year, month, day, hour, min, day_num = pricing_date_time.split('-')

########################################################################################
# Fetching t-1 Fx vol data
########################################################################################

file_dir = Path(base_dir + '\\data\\bbg_mktdata\\fx_vol')

############# vol data
start_date = '2026-01-01'
end_date = '2026-04-30'

tickers = []
new_cols_list = ['currpair','vol_type','tenor','bbg_source']

vol_types = ['V','25R','25B','10R','10B']

ticker_details = {}

for currpair in currpairs:
    bbg_source = bbg_vol_sources['XXXYYY'] if currpair not in bbg_vol_sources.keys() else bbg_vol_sources[currpair]
    for vol_type in vol_types:
        for tenor in tenors_list:
            ticker = currpair + vol_type + tenor + ' ' + bbg_source + ' Curncy'
            tickers.append(ticker)
            ticker_details[ticker] = [currpair, vol_type, tenor, bbg_source]


df = xbbg_hist(tickers,['PX_LAST'],start_date, end_date)
df = pd.concat([df, pd.DataFrame(columns = new_cols_list)])
df = 0.01 * df # Convert from percentage to decimal
df = df.round(6)

if not df.empty:
    df[new_cols_list] = pd.DataFrame(
        [ticker_details[t] for t in df.index.get_level_values(0)],
        index=df.index,
        columns=new_cols_list,
    )


df.index.names = ['Ticker','Date']

for currpair in currpairs:
    df_currpair = df[df['currpair'] == currpair]
    for vol_type in vol_types:
        df_currpair_voltype = df_currpair[df_currpair['vol_type'] == vol_type]
        df_currpair_voltype_pivot = pd.DataFrame()
        df_currpair_voltype_pivot = pd.pivot_table(df_currpair_voltype,index=['currpair','Date'],columns='tenor',values='PX_LAST').reset_index()
        df_currpair_voltype_pivot.columns.name = None
        df_currpair_voltype_pivot = df_currpair_voltype_pivot[['Date'] + tenors_list]
        if not df_currpair_voltype_pivot.empty:
            df_currpair_voltype_pivot.to_csv(file_dir / f'{currpair}_{vol_type}.csv', index=False)



# #############  fx impl yields ##################

file_dir = Path(base_dir + '\\data\\bbg_mktdata\\fx_implied_yield')

start_date = '2026-01-01'
end_date = '2026-04-30'

tickers = []
new_cols_list = ['ccy','tenor']

tickers_details_dict = {
    "USD": {'1W': 'USOSFR1Z Curncy', '2W': 'USOSFR2Z Curncy', '1M': 'USOSFRA Curncy', '2M': 'USOSFRB Curncy', '3M': 'USOSFRC Curncy', '6M': 'USOSFRF Curncy', '9M': 'USOSFRI Curncy', '1Y': 'USOSFR1 Curncy'},
    "INR": {'1W': 'IRNI1W BGN Curncy', '2W': 'IRNI2W BGN Curncy', '1M': 'IRNI1M BGN Curncy', '2M': 'IRNI2M BGN Curncy', '3M': 'IRNI3M BGN Curncy', '6M': 'IRNI6M BGN Curncy', '9M': 'IRNI9M BGN Curncy', '1Y': 'IRNI12M BGN Curncy'},
    "KRW": {'1W': 'KWNI1W BGN Curncy', '2W': 'KWNI2W BGN Curncy', '1M': 'KWNI1M BGN Curncy', '2M': 'KWNI2M BGN Curncy', '3M': 'KWNI3M BGN Curncy', '6M': 'KWNI6M BGN Curncy', '9M': 'KWNI9M BGN Curncy', '1Y': 'KWNI12M BGN Curncy'},
    "TWD": {'1W': 'TRNI1W BGN Curncy', '2W': 'TRNI2W BGN Curncy', '1M': 'TRNI1M BGN Curncy', '2M': 'TRNI2M BGN Curncy', '3M': 'TRNI3M BGN Curncy', '6M': 'TRNI6M BGN Curncy', '9M': 'TRNI9M BGN Curncy', '1Y': 'TRNI12M BGN Curncy'},
    "IDR": {'1W': 'IHNI1W BGN Curncy', '2W': 'IHNI2W BGN Curncy', '1M': 'IHNI1M BGN Curncy', '2M': 'IHNI2M BGN Curncy', '3M': 'IHNI3M BGN Curncy', '6M': 'IHNI6M BGN Curncy', '9M': 'IHNI9M BGN Curncy', '1Y': 'IHNI12M BGN Curncy'},
    "PHP": {'1W': 'PPNI1W BGN Curncy', '2W': 'PPNI2W BGN Curncy', '1M': 'PPNI1M BGN Curncy', '2M': 'PPNI2M BGN Curncy', '3M': 'PPNI3M BGN Curncy', '6M': 'PPNI6M BGN Curncy', '9M': 'PPNI9M BGN Curncy', '1Y': 'PPNI12M BGN Curncy'},
    "THB": {'1W': 'TBOI1W BGN Curncy', '2W': 'TBOI2W BGN Curncy', '1M': 'TBOI1M BGN Curncy', '2M': 'TBOI2M BGN Curncy', '3M': 'TBOI3M BGN Curncy', '6M': 'TBOI6M BGN Curncy', '9M': 'TBOI9M BGN Curncy', '1Y': 'TBOI12M BGN Curncy'},
    "CNH": {'1W': 'CGI1W BGN Curncy', '2W': 'CGI2W BGN Curncy', '1M': 'CGI1M BGN Curncy', '2M': 'CGI2M BGN Curncy', '3M': 'CGI3M BGN Curncy', '6M': 'CGI6M BGN Curncy', '9M': 'CGI9M BGN Curncy', '1Y': 'CGI12M BGN Curncy'},
    "SGD": {'1W': 'SDI1W BGN Curncy', '2W': 'SDI2W BGN Curncy', '1M': 'SDI1M BGN Curncy', '2M': 'SDI2M BGN Curncy', '3M': 'SDI3M BGN Curncy', '6M': 'SDI6M BGN Curncy', '9M': 'SDI9M BGN Curncy', '1Y': 'SDI12M BGN Curncy'},
    "HKD": {'1W': 'HDI1W BGN Curncy', '2W': 'HDI2W BGN Curncy', '1M': 'HDI1M BGN Curncy', '2M': 'HDI2M BGN Curncy', '3M': 'HDI3M BGN Curncy', '6M': 'HDI6M BGN Curncy', '9M': 'HDI9M BGN Curncy', '1Y': 'HKD12M BGN Curncy'},
    "EUR": {'1W': 'EUI1W BGN Curncy', '2W': 'EUI2W BGN Curncy', '1M': 'EUI1M BGN Curncy', '2M': 'EUI2M BGN Curncy', '3M': 'EUI3M BGN Curncy', '6M': 'EUI6M BGN Curncy', '9M': 'EUI9M BGN Curncy', '1Y': 'EUI12M BGN Curncy'},
    "JPY": {'1W': 'JYI1W BGN Curncy', '2W': 'JYI2W BGN Curncy', '1M': 'JYI1M BGN Curncy', '2M': 'JYI2M BGN Curncy', '3M': 'JYI3M BGN Curncy', '6M': 'JYI6M BGN Curncy', '9M': 'JYI9M BGN Curncy', '1Y': 'JYI12M BGN Curncy'},
    "GBP": {'1W': 'BPI1W BGN Curncy', '2W': 'BPI2W BGN Curncy', '1M': 'BPI1M BGN Curncy', '2M': 'BPI2M BGN Curncy', '3M': 'BPI3M BGN Curncy', '6M': 'BPI6M BGN Curncy', '9M': 'BPI9M BGN Curncy', '1Y': 'BPI12M BGN Curncy'},
    "AUD": {'1W': 'ADI1W BGN Curncy', '2W': 'ADI2W BGN Curncy', '1M': 'ADI1M BGN Curncy', '2M': 'ADI2M BGN Curncy', '3M': 'ADI3M BGN Curncy', '6M': 'ADI6M BGN Curncy', '9M': 'ADI9M BGN Curncy', '1Y': 'ADI12M BGN Curncy'},
    "NZD": {'1W': 'NDI1W BGN Curncy', '2W': 'NDI2W BGN Curncy', '1M': 'NDI1M BGN Curncy', '2M': 'NDI2M BGN Curncy', '3M': 'NDI3M BGN Curncy', '6M': 'NDI6M BGN Curncy', '9M': 'NDI9M BGN Curncy', '1Y': 'NDI12M BGN Curncy'},
    "CHF": {'1W': 'SFI1W BGN Curncy', '2W': 'SFI2W BGN Curncy', '1M': 'SFI1M BGN Curncy', '2M': 'SFI2M BGN Curncy', '3M': 'SFI3M BGN Curncy', '6M': 'SFI6M BGN Curncy', '9M': 'SFI9M BGN Curncy', '1Y': 'SFI12M BGN Curncy'},
    "CAD": {'1W': 'CDI1W BGN Curncy', '2W': 'CDI2W BGN Curncy', '1M': 'CDI1M BGN Curncy', '2M': 'CDI2M BGN Curncy', '3M': 'CDI3M BGN Curncy', '6M': 'CDI6M BGN Curncy', '9M': 'CDI9M BGN Curncy', '1Y': 'CDI12M BGN Curncy'}
    }
tickers_details_df = (
    pd.DataFrame(tickers_details_dict)
    .stack()
    .reset_index()
)
tickers_details_df.columns = ['tenor', 'ccy', 'ticker']
tickers_details_df = tickers_details_df.set_index('ticker')[['ccy', 'tenor']]
ticker_details = tickers_details_df.to_dict(orient='index')
tickers = list(tickers_details_df.index)
ccys = list(set(tickers_details_df['ccy']))
tenors_yield_list = ['1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y']

df_main = xbbg_hist(tickers,['PX_LAST'],start_date, end_date)
df_main = pd.concat([df_main, pd.DataFrame(columns = new_cols_list)])
df_main = df_main.round(4)
df = copy.deepcopy(df_main)

if not df.empty:
    df[new_cols_list] = pd.DataFrame(
        [ticker_details[t] for t in df.index.get_level_values(0)],
        index=df.index,
        columns=new_cols_list,
    )

df.index.names = ['Ticker','Date']

for ccy in ccys:
    df_ccy = df[df['ccy'] == ccy]
    df_ccy_pivot = pd.pivot_table(df_ccy,index=['ccy','Date'],columns='tenor',values='PX_LAST').reset_index()
    df_ccy_pivot.columns.name = None
    df_ccy_pivot = df_ccy_pivot[['Date'] + tenors_yield_list]
    print(ccy, df_ccy_pivot)
    df_ccy_pivot.to_csv(file_dir / f'{ccy}.csv', index=False)


######################### #############################################
file_dir = Path(base_dir + '\\data\\bbg_mktdata\\fx_spot_fwd')

start_date = '2026-01-01'
end_date = '2026-04-30'
new_cols_list = ['currpair']
tickers = []


tickers_dict= {"USDINR": 'USDINR BGN Curncy',"USDKRW": 'USDKRW BGN Curncy',"USDTWD": 'USDTWD BGN Curncy',"USDIDR": 'USDIDR BGN Curncy',"USDPHP": 'USDPHP BGN Curncy',
"USDTHB": 'USDTHB BGN Curncy',"USDCNH": 'USDCNH BGN Curncy',"USDSGD": 'USDSGD BGN Curncy',"USDHKD": 'USDHKD BGN Curncy',"EURUSD": 'EURUSD BGN Curncy',"USDJPY": 'USDJPY BGN Curncy',
"GBPUSD": 'GBPUSD BGN Curncy',"AUDUSD": 'AUDUSD BGN Curncy',"NZDUSD": 'NZDUSD BGN Curncy',"USDCHF": 'USDCHF BGN Curncy',"USDCAD": 'USDCAD BGN Curncy', "EURAUD": 'EURAUD BGN Curncy', 
"GBPAUD": 'GBPAUD BGN Curncy', "AUDNZD": 'AUDNZD BGN Curncy', "AUDJPY": 'AUDJPY BGN Curncy', "AUDCAD": 'AUDCAD BGN Curncy'}

currpairs = list(tickers_dict.keys())
tickers = [tickers_dict[ccy] for ccy in currpairs]
ticker_details = {ticker: ccy for ccy, ticker in tickers_dict.items()}

df_main = xbbg_hist(tickers,['PX_LAST'],start_date, end_date)
df_main = pd.concat([df_main, pd.DataFrame(columns = new_cols_list)])
df_main = df_main.round(4)
df = copy.deepcopy(df_main)

if not df.empty:
    df[new_cols_list] = pd.DataFrame(
        [ticker_details[t] for t in df.index.get_level_values(0)],
        index=df.index,
        columns=new_cols_list,
    )

df.index.names = ['Ticker','Date']

for currpair in currpairs:
    df_currpair = df[df['currpair'] == currpair]
    df_currpair_pivot = pd.pivot_table(df_currpair,index=['currpair','Date'],values='PX_LAST').reset_index()
    df_currpair_pivot = (df_currpair_pivot.set_index('Date'))[['PX_LAST']]
    df_currpair_pivot.columns = ['Spot']

    print(currpair, df_currpair_pivot)
    df_currpair_pivot.to_csv(file_dir / f'{currpair}_spot.csv')

           


