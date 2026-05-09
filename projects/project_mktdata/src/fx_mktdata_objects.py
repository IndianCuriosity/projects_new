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
import pickle

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


mktdata_dir = Path(base_dir + '\\data\\bbg_mktdata\\')

for currpair in currpairs:
    currpair_mktdata_dict = {}
    curr_1 = currpair[0:3]
    curr_2 = currpair[3:6]
    spot_df = pd.read_csv(mktdata_dir/'fx_spot_fwd'/f'{currpair}_spot.csv').set_index('Date')
    curr1_yield_df = pd.read_csv(mktdata_dir/'fx_implied_yield'/f'{curr_1}.csv').set_index('Date')
    curr2_yield_df = pd.read_csv(mktdata_dir/'fx_implied_yield'/f'{curr_2}.csv').set_index('Date')
    
    vol_atm_df = pd.read_csv(mktdata_dir/'fx_vol'/f'{currpair}_V.csv').set_index('Date')
    vol_25r_df = pd.read_csv(mktdata_dir/'fx_vol'/f'{currpair}_25R.csv').set_index('Date')
    vol_25b_df = pd.read_csv(mktdata_dir/'fx_vol'/f'{currpair}_25B.csv').set_index('Date')
    vol_10r_df = pd.read_csv(mktdata_dir/'fx_vol'/f'{currpair}_10R.csv').set_index('Date')
    vol_10b_df = pd.read_csv(mktdata_dir/'fx_vol'/f'{currpair}_10B.csv').set_index('Date')
    
    vol_25c_df = vol_atm_df + vol_25b_df + 0.5 * vol_25r_df
    vol_25p_df = vol_atm_df + vol_25b_df - 0.5 * vol_25r_df
    vol_10c_df = vol_atm_df + vol_10b_df + 0.5 * vol_10r_df
    vol_10p_df = vol_atm_df + vol_10b_df - 0.5 * vol_10r_df
    
    eval_dates = vol_atm_df.index
    
    for eval_date in eval_dates:
        try:
                
            currpair_mktdata_dict[eval_date] = {}
            vol_cube_date = (pd.concat([vol_10p_df.loc[eval_date], vol_25p_df.loc[eval_date], vol_atm_df.loc[eval_date], vol_25c_df.loc[eval_date], vol_10c_df.loc[eval_date]], axis=1))
            vol_cube_date.columns = ['10p', '25p', 'atm', '25c', '10c']
            currpair_mktdata_dict[eval_date]['vol_cube'] = vol_cube_date
            currpair_mktdata_dict[eval_date]['spot'] = spot_df.loc[eval_date, 'Spot']
            currpair_mktdata_dict[eval_date]['curr1_yield'] = curr1_yield_df.loc[eval_date]
            currpair_mktdata_dict[eval_date]['curr2_yield'] = curr2_yield_df.loc[eval_date]
        except Exception as e:
            print(f"Error processing {currpair} on {eval_date}: {e}")
            continue
    with open(mktdata_dir/'fx_json'/f'{currpair}_mktdata_dict.json', 'w') as f:
        json.dump(currpair_mktdata_dict, f, default=str)
    
    with open(mktdata_dir/'fx_pickled'/f'{currpair}_mktdata_dict.pkl', 'wb') as f:
        pickle.dump(currpair_mktdata_dict, f)


