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
import importlib

from datetime import datetime, timedelta, date
from pandas.tseries.offsets import BDay

base_dir = os.environ.get('PROJECTS_NEW_HOME')
sys.path.append(base_dir + '\\utils\\')
sys.path.append(base_dir + '\\configs\\')


from utils.bbg_functions import xbbg_hist
if "utils.optionpricing_functions" in sys.modules:
    del sys.modules["utils.optionpricing_functions"]

from utils.optionpricing_functions import *
# importlib.reload(opt_funcs) 


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
    #eval_date = eval_dates[0]
    # eval_dates = eval_dates[:5]
    # eval_dates = ['2026-01-06']
    for eval_date in eval_dates:
        try:
            currpair_mktdata_dict[eval_date] = {}

            ################################################################
            # spot rate
            ################################################################

            try:
                spot_rate = spot_df.loc[eval_date, 'Spot']
            except Exception as e:
                spot_rate = spot_rate_prev
                print(f"Spot rate missing for {currpair} on {eval_date}, using previous value: {spot_rate_prev}")
            
            spot_rate_prev = spot_rate
            currpair_mktdata_dict[eval_date]['spot'] = spot_rate

            ################################################################
            #### Yield curves
            ################################################################
            
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
            
            yield_curr1_prev = yield_curr1
            yield_curr2_prev = yield_curr2

            ################################################################
            #### linearmktdata and linearmktdata_interp_object #######
            ################################################################
            
            try:
                linearmktdata_df, linearmktdata_interp_object_dict = linearmktdata_func(eval_date, spot_rate, yield_curr1, yield_curr2,currpair_static_info_dict,interp_obj_boolean = True, 
                                                                            time_axis_interp_method = 'both')
            except Exception as e:
                 print ('Error in generating linearmktdata_df, linearmktdata_interp_object_dict: ', e)
                 linearmktdata_df, linearmktdata_interp_object_dict =  None, None

            currpair_mktdata_dict[eval_date]['linearmktdata_df'] = linearmktdata_df
            currpair_mktdata_dict[eval_date]['linearmktdata_interp_object_dict'] = linearmktdata_interp_object_dict
 
            ################################################################
            #### volcube & volcube_interp_object ######################
            ################################################################
            
            volcube_t = (pd.concat([vol_10p_df.loc[eval_date], vol_25p_df.loc[eval_date], vol_atm_df.loc[eval_date], vol_25c_df.loc[eval_date], vol_10c_df.loc[eval_date]], axis=1))
            volcube_t.columns = ['10P', '25P', 'ATM', '25C', '10C']
            
            try:
                volcube = volcube_create_func(eval_date, volcube_t,linearmktdata_df,currpair_static_info_dict)
            except Exception as e:
                print ('Error in generating volcube: ', e)
                volcube = None
            try:
                volcube_interp_object_dict = volcube_create_interp_obj_func(volcube, interp_obj_boolean = True, time_axis_interp_method = 'both')
            except Exception as e:
                print ('Error in generating volcube_interp_object_dict: ', e)
                volcube_interp_object_dict = None
            
            currpair_mktdata_dict[eval_date]['volcube'] = volcube
            currpair_mktdata_dict[eval_date]['volcube_interp_object_dict'] = volcube_interp_object_dict

            ################################################################
            #### svi params and volcube implied strikes ####
            ################################################################

            try:
                svi_params_df,volcube_implied_strikes = svi_calibration_func(volcube)
            except Exception as e:
                print ('Error in generating svi_params_df,volcube_implied_strikes: ', e)
                svi_params_df,volcube_implied_strikes =  None, None

            currpair_mktdata_dict[eval_date]['svi_params_df'] = svi_params_df
            currpair_mktdata_dict[eval_date]['volcube_implied_strikes'] = volcube_implied_strikes

            ################################################################
            #### local vol surface ####
            ################################################################
            currpair_mktdata_dict_pricing_date = currpair_mktdata_dict[eval_date]
            option_details_dict = option_details_dict = {'Eval_Date': eval_date, 'Currpair': currpair, 'Expiry': None, 'Strike': None, 'CallPut': 'Call', 
                                                         'BuySell': 'Buy', 'Notional_For_Ccy': 1000000}
            try:
                interp_data_df, strikes = build_maturities_strikes(eval_date, volcube_implied_strikes, linearmktdata_df,linearmktdata_interp_object_dict,
                                                               linearmktdata_time_axis_interp_method='linear',all_strikes_boolean=False)
            except Exception as e:
                print ('Error in generating interp_data_df,strikes: ', e)
                interp_data_df, strikes =  None, None
            
            try:
                # local_vol_surface,expiry_years_array,strikes_array = dupire_local_vol_bivariate_spline_func(interp_data_df, strikes, option_details_dict, currpair_mktdata_dict_pricing_date, 
                #                                                                         smile_vol_model ='std_cubic_interp_vol_model', 
                #                                                                         volmktdata_time_axis_interp_method = 'linear', 
                #                                                                         price_greeks_concise_boolean = True)
                
                local_vol_surface,expiry_years_array,strikes_array = dupire_local_vol_bs_greeks_func(interp_data_df, strikes, option_details_dict, currpair_mktdata_dict_pricing_date, 
                                                                                        smile_vol_model ='std_cubic_interp_vol_model', 
                                                                                        volmktdata_time_axis_interp_method = 'linear')
            except Exception as e:
                print ('Error in generating interp_data_df,strikes: ', e)
                local_vol_surface,expiry_years_array,strikes_array = None, None, None
            
            currpair_mktdata_dict[eval_date]['local_vol_surface_expiry_strikes_arrays'] = [local_vol_surface,expiry_years_array,strikes_array]

            print(f"Processed {currpair} on {eval_date}")
            print('dimensions:', np.shape(local_vol_surface),len(expiry_years_array),len(strikes_array))
        except Exception as e:
            print(f"Error processing {currpair} on {eval_date}: {e}")
            continue
    

    with open(mktdata_dir/'fx_json'/f'{currpair}_mktdata_dict.json', 'w') as f:
        json.dump(currpair_mktdata_dict, f, default=str)
    
    with open(mktdata_dir/'fx_pickled'/f'{currpair}_mktdata_dict.pkl', 'wb') as f:
        pickle.dump(currpair_mktdata_dict, f)

