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
from utils.optionpricing_functions import *

base_dir = os.environ.get('PROJECTS_NEW_HOME')
sys.path.append(base_dir + '\\utils\\')
sys.path.append(base_dir + '\\configs\\')


config = configparser.ConfigParser()
config.read(base_dir + '\\configs\\fx_config.ini')


### currpairs ####
g10_currpairs = [c.strip() for c in config['currpairs']['g10_currpairs'].split(',')]
asia_deliv_currpairs = [c.strip() for c in config['currpairs']['asia_deliv_currpairs'].split(',')]
asia_nd_currpairs = [c.strip() for c in config['currpairs']['asia_nd_currpairs'].split(',')]
aud_cross_currpairs = [c.strip() for c in config['currpairs']['aud_cross_currpairs'].split(',')]

currpairs = g10_currpairs + asia_deliv_currpairs + asia_nd_currpairs + aud_cross_currpairs
currpairs = list(set(currpairs))

# fx configs
tenors_calendar_days = pd.read_excel(base_dir + '\\configs\\configs.xlsx', sheet_name='TenorsCalendarDays', index_col=0)
currpair_rate_conventions = pd.read_excel(base_dir + '\\configs\\configs.xlsx', sheet_name='CurrPairRateConventions', index_col=0)
currpair_spot_days_conventions = pd.read_excel(base_dir + '\\configs\\configs.xlsx', sheet_name='CurrPairSpotDaysConventions', index_col=0)
curr_rate_conventions = pd.read_excel(base_dir + '\\configs\\configs.xlsx', sheet_name='CurrRateConventions', index_col=0)
swap_factors = pd.read_excel(base_dir + '\\configs\\configs.xlsx', sheet_name='SwapFactors', index_col=0)

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
    eval_dates = eval_dates[1:] # Removing the first date to avoid issues with missing previous day data for interpolation
    currpair_static_info_dict = {}

    currpair_static_info_dict['daycount_ccy1'] = curr_rate_conventions.loc[curr_1, 'DayCount']
    currpair_static_info_dict['daycount_ccy2'] = curr_rate_conventions.loc[curr_2, 'DayCount']
    currpair_static_info_dict['spot_days'] = currpair_spot_days_conventions.loc[currpair, 'SpotDays']
    #currpair_static_info_dict['currpair_rate_conventions'] = currpair_rate_conventions.loc[currpair, 'DayCount'] # May not be required
    currpair_static_info_dict['swap_factor'] = swap_factors.loc[currpair, 'SwapFactor']
    currpair_static_info_dict['point_move'] = swap_factors.loc[currpair, 'PointMove']
    currpair_static_info_dict['tenors_calendar_days'] = tenors_calendar_days

    currpair_mktdata_dict['static_info'] = currpair_static_info_dict


    interp_method = 'both'
    interp_obj_boolean = True

    for eval_date in eval_dates:
        try:
            currpair_mktdata_dict[eval_date] = {}

            # spot rate
            try:
                spot_rate = spot_df.loc[eval_date, 'Spot']
            except Exception as e:
                spot_rate = spot_rate_prev
                print(f"Spot rate missing for {currpair} on {eval_date}, using previous value: {spot_rate_prev}")
            
            currpair_mktdata_dict[eval_date]['spot'] = spot_rate

            #### linearmktdata & linearmktdata_interp_object
            try:
                yield_curr1 = curr1_yield_df.loc[eval_date]
            except Exception as e:
                yield_curr1 = yield_curr1_prev
                print(f"Yield curve data missing for {currpair} on {eval_date}, using previous value: {yield_curr1_prev}")
            
            try:
                yield_curr2 = curr2_yield_df.loc[eval_date]
            except Exception as e:
                yield_curr2 = yield_curr2_prev
                print(f"Yield curve data missing for {currpair} on {eval_date}, using previous value: {yield_curr2_prev}")
            
            
            if eval_date != eval_dates[0]:
                if yield_curr1.isna().any():
                    yield_curr1_diff_mean = (yield_curr1 - yield_curr1_prev).mean()
                    yield_curr1_diff = yield_curr1.diff().fillna(yield_curr1_diff_mean)
                    yield_curr1 = yield_curr1_prev + yield_curr1_diff

                if yield_curr2.isna().any():
                    yield_curr2_diff_mean = (yield_curr2 - yield_curr2_prev).mean()
                    yield_curr2_diff = yield_curr2.diff().fillna(yield_curr2_diff_mean)
                    yield_curr2 = yield_curr2_prev + yield_curr2_diff
                
            linearmktdata_df, linearmktdata_interp_object_dict = linearmktdata_func(eval_date, spot_rate, yield_curr1, yield_curr2,currpair_static_info_dict,interp_obj_boolean = True, 
                                                                            time_axis_interp_method = 'both')
            currpair_mktdata_dict[eval_date]['linearmktdata_df'] = linearmktdata_df
            currpair_mktdata_dict[eval_date]['linearmktdata_interp_object_dict'] = linearmktdata_interp_object_dict
 

            #### volcube & volcube_interp_object
            volcube_t = (pd.concat([vol_10p_df.loc[eval_date], vol_25p_df.loc[eval_date], vol_atm_df.loc[eval_date], vol_25c_df.loc[eval_date], vol_10c_df.loc[eval_date]], axis=1))
            volcube_t.columns = ['10P', '25P', 'ATM', '25C', '10C']
            volcube = volcube_create_func(eval_date, volcube_t,linearmktdata_df,currpair_static_info_dict)
            volcube_interp_object_dict = volcube_create_interp_obj_func(volcube, interp_obj_boolean = True, time_axis_interp_method = 'both')

            currpair_mktdata_dict[eval_date]['volcube'] = volcube
            currpair_mktdata_dict[eval_date]['volcube_interp_object_dict'] = volcube_interp_object_dict

            yield_curr1_prev = yield_curr1
            yield_curr2_prev = yield_curr2
            spot_rate_prev = spot_rate

            #print(f"Processed {currpair} on {eval_date}")
        except Exception as e:
            print(f"Error processing {currpair} on {eval_date}: {e}")
            continue
    

    with open(mktdata_dir/'fx_json'/f'{currpair}_mktdata_dict.json', 'w') as f:
        json.dump(currpair_mktdata_dict, f, default=str)
    
    with open(mktdata_dir/'fx_pickled'/f'{currpair}_mktdata_dict.pkl', 'wb') as f:
        pickle.dump(currpair_mktdata_dict, f)

