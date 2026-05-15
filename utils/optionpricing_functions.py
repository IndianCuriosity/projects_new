###########################################################################################################################
# This module contains functions for option pricing, including the Black-Scholes formula and implied volatility calculations.
# Real FX desks often use:

# Delta space interpolation
# Premium-adjusted delta
# Forward delta
# Spot delta
# Sticky delta or sticky strike rules

# Then calibrate:

# SVI
# SABR
# Vanna-Volga
# spline
# cubic
# arbitrage constraints
# settlement convention

###########################################################################################################################

import pandas as pd
import numpy as np
from numba import njit, prange
import datetime
import os, sys
base_dir = os.environ.get('PROJECTS_NEW_HOME')
sys.path.append(base_dir + '\\utils\\')
sys.path.append(base_dir + '\\configs\\')
from dates_functions import *
import scipy.stats as ss
from scipy.interpolate import CubicSpline
from scipy.interpolate import interp1d
from scipy.interpolate import RectBivariateSpline # Smooth interpolation of C(T,K) and derivatives
from scipy.interpolate import RegularGridInterpolator # Monte Carlo
from scipy.interpolate import griddata
from scipy.optimize import brentq
from scipy.optimize import least_squares
import math
import copy


############################################################################################################################################################################
## Creation of Linear Market Data DataFrame and Interpolation Objects # ( Used only for creation of interp_objects and saved for later use in option pricer functions)
############################################################################################################################################################################

def linearmktdata_func(eval_date, spot_rate, yield_curr1, yield_curr2,currpair_static_info_dict,interp_obj_boolean = True, time_axis_interp_method = 'both'):

    interp_object_rate1, interp_object_rate2, interp_object_forward_rate = None, None, None
    linearmktdata_interp_object_dict = {}
    linearmktdata_interp_object_dict['cubic'] = {}
    linearmktdata_interp_object_dict['linear'] = {}

    daycount_curr1 = currpair_static_info_dict['daycount_ccy1']
    daycount_curr2 = currpair_static_info_dict['daycount_ccy2']
    spot_days = currpair_static_info_dict['spot_days']
    #currpair_rate_convention = currpair_static_info_dict['currpair_rate_conventions']
    swap_factor = currpair_static_info_dict['swap_factor']
    point_move = currpair_static_info_dict['point_move']
    tenors_calendar_days = currpair_static_info_dict['tenors_calendar_days']


    tenors1 = yield_curr1.index
    tenors2 = yield_curr2.index
    tenors = [item for item in tenors1 if item in tenors2]

    spot_date_datetime = pd.to_datetime(eval_date) + BDay(spot_days)
    spot_date = datetime.strftime(spot_date_datetime, '%Y-%m-%d')
    spot_date_nb_days = calendar_days(eval_date, spot_date)
    eval_date_datetime = pd.to_datetime(eval_date)

    linearmktdata_df = pd.DataFrame(columns = ['tenors','value_date', 'value_date_nb_days','expiry_date', 'expiry_date_nb_days', 'rate1', 'rate2', 'cap_factor1', 
                                                               'cap_factor2', 'discount_factor1', 'discount_factor2','forward_rate'])
    linearmktdata_df['tenors'] = ['SPOT'] + tenors
    linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'value_date_nb_days'] = spot_date_nb_days

    linearmktdata_df['value_date_nb_days'] = linearmktdata_df.apply(lambda x: (spot_date_nb_days + tenors_calendar_days.loc[x['tenors'], 'CalendarDays']) if x['tenors'] in tenors
                                                                     else x['value_date_nb_days'], axis=1)
    linearmktdata_df['value_date'] = eval_date_datetime + pd.to_timedelta(linearmktdata_df['value_date_nb_days'], unit='D')
    linearmktdata_df['value_date'] = linearmktdata_df['value_date'].dt.strftime('%Y-%m-%d')    

    linearmktdata_df['expiry_date'] = linearmktdata_df['value_date'].apply(lambda x: prev_bus_day_ref(x,2))
    linearmktdata_df['expiry_date_nb_days'] = linearmktdata_df['expiry_date'].apply(lambda x: calendar_days(eval_date, x))

    linearmktdata_df['rate1'] = yield_curr1
    linearmktdata_df['rate2'] = yield_curr2

    linearmktdata_df['rate1'] = linearmktdata_df.apply(lambda x: yield_curr1[x['tenors']] if x['tenors'] in tenors else np.nan, axis=1)
    linearmktdata_df['rate2'] = linearmktdata_df.apply(lambda x: yield_curr2[x['tenors']] if x['tenors'] in tenors else np.nan, axis=1)
    linearmktdata_df['rate1'] = linearmktdata_df['rate1'].bfill()
    linearmktdata_df['rate2'] = linearmktdata_df['rate2'].bfill()

    linearmktdata_df['cap_factor1'] = 1+(linearmktdata_df['value_date_nb_days'] / daycount_curr1) * linearmktdata_df['rate1'] / 100
    linearmktdata_df['cap_factor2'] = 1+(linearmktdata_df['value_date_nb_days'] / daycount_curr2) * linearmktdata_df['rate2'] / 100
    linearmktdata_df['discount_factor1'] = 1 / linearmktdata_df['cap_factor1']
    linearmktdata_df['discount_factor2'] = 1 / linearmktdata_df['cap_factor2']
    discount_factor1_from_spot_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'discount_factor1'].iloc[0]
    discount_factor2_from_spot_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'discount_factor2'].iloc[0]

    discounted_spot_rate = spot_rate * discount_factor2_from_spot_date / discount_factor1_from_spot_date

    linearmktdata_df['forward_rate'] = discounted_spot_rate * linearmktdata_df['cap_factor2'] / linearmktdata_df['cap_factor1']

    if interp_obj_boolean:
        if time_axis_interp_method in ['cubic','both']:
            interp_object_rate1 = CubicSpline(linearmktdata_df['value_date_nb_days'], linearmktdata_df['rate1'], extrapolate=True)
            interp_object_rate2 = CubicSpline(linearmktdata_df['value_date_nb_days'], linearmktdata_df['rate2'], extrapolate=True)
            interp_object_forward_rate = CubicSpline(linearmktdata_df['value_date_nb_days'], linearmktdata_df['forward_rate'], extrapolate=True)
            linearmktdata_interp_object_dict['cubic'] = {'rate1': interp_object_rate1, 'rate2': interp_object_rate2, 'forward_rate': interp_object_forward_rate}
        if time_axis_interp_method in ['linear','both']:
            interp_object_rate1 = interp1d(linearmktdata_df['value_date_nb_days'], linearmktdata_df['rate1'], fill_value='extrapolate')
            interp_object_rate2 = interp1d(linearmktdata_df['value_date_nb_days'], linearmktdata_df['rate2'], fill_value='extrapolate')
            interp_object_forward_rate = interp1d(linearmktdata_df['value_date_nb_days'], linearmktdata_df['forward_rate'], fill_value='extrapolate')
            linearmktdata_interp_object_dict['linear'] = {'rate1': interp_object_rate1, 'rate2': interp_object_rate2, 'forward_rate': interp_object_forward_rate}
    
    return linearmktdata_df, linearmktdata_interp_object_dict




############################################################################################################################################################################
## Creation of Volatility Cube &  Interpolation Objects # ( Used only for creation of interp_objects and saved for later use in option pricer functions)
############################################################################################################################################################################

def volcube_create_func(eval_date, volcube_t,linearmktdata_df,currpair_static_info_dict):
    
    daycount_curr1 = currpair_static_info_dict['daycount_ccy1']
    daycount_curr2 = currpair_static_info_dict['daycount_ccy2']
    spot_days = currpair_static_info_dict['spot_days']

    volcube = volcube_t.reset_index()
    volcube['Expiry_Date'] = volcube.apply(lambda x: (linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'expiry_date']).values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube['Expiry_Days'] = volcube.apply(lambda x: linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'expiry_date_nb_days'].values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube['Value_Date'] = volcube.apply(lambda x: (linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'value_date']).values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube['Value_Days'] = volcube.apply(lambda x: linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'value_date_nb_days'].values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube['Rate1'] = volcube.apply(lambda x: linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'rate1'].values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube['Rate2'] = volcube.apply(lambda x: linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'rate2'].values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube['Forward_Rate'] = volcube.apply(lambda x: linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'forward_rate'].values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)

    volcube['Rate1'] = volcube['Rate1'].bfill()
    volcube['Rate2'] = volcube['Rate2'].bfill()

    volcube.set_index('index', inplace=True)
    
    expiry_date_ON = next_bus_day_ref(eval_date, 1)
    volcube.loc['ON', 'Expiry_Date'] = expiry_date_ON
    volcube.loc['ON', 'Expiry_Days'] = calendar_days(eval_date, expiry_date_ON)

    value_date_ON = next_bus_day_ref(expiry_date_ON, spot_days)
    volcube.loc['ON', 'Value_Date'] = value_date_ON
    volcube.loc['ON', 'Value_Days'] = calendar_days(eval_date, value_date_ON)

    # ON forward rate
    discount_factor1_from_spot_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'discount_factor1'].iloc[0]
    discount_factor2_from_spot_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'discount_factor2'].iloc[0]
    spot_rate = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'forward_rate'].iloc[0]
    discounted_spot_rate = spot_rate * discount_factor2_from_spot_date / discount_factor1_from_spot_date
    cap_factor1_ON = 1+ (volcube.loc['ON', 'Value_Days']/ daycount_curr1) * volcube.loc['ON', 'Rate1'] / 100
    cap_factor2_ON = 1+ (volcube.loc['ON', 'Value_Days']/ daycount_curr2) * volcube.loc['ON', 'Rate2'] / 100
    volcube.loc['ON', 'Forward_Rate']  = discounted_spot_rate * cap_factor2_ON / cap_factor1_ON

    volcube.index.name = 'Tenor'

    return volcube



def volcube_create_interp_obj_func(volcube, interp_obj_boolean = True, time_axis_interp_method = 'both'):
    atm_variancetime, interp_object_ten_delta, interp_object_ten_delta_call, interp_object_twentyfive_delta_put, interp_object_twentyfive_delta_call = None, None, None, None, None
    volcube_interp_object_dict = {}
    volcube_interp_object_dict['cubic'] = {}
    volcube_interp_object_dict['linear'] = {}
    volcube_interp_object_dict['tail_details'] = {}

    if interp_obj_boolean:
        atm_vols = list(volcube['ATM'])                                                                                        
        nb_expiry_days = list(volcube['Expiry_Days'])

        volcube_interp_object_dict['tail_details']['flatvol1'] = atm_vols[0]
        volcube_interp_object_dict['tail_details']['flatvol2'] = atm_vols[-1]
        volcube_interp_object_dict['tail_details']['nb_expiry_days1'] = nb_expiry_days[0]
        volcube_interp_object_dict['tail_details']['nb_expiry_days2'] = nb_expiry_days[-1]

        atm_variancetime = [a*b*c for a,b,c in zip(atm_vols,atm_vols,nb_expiry_days)]

        ten_delta_put_smilespreads = list(volcube['10P'] - volcube['ATM'])
        twentyfive_delta_put_smilespreads = list(volcube['25P'] - volcube['ATM'])
        twentyfive_delta_call_smilespreads = list(volcube['25C'] - volcube['ATM'])
        ten_delta_call_smilespreads = list(volcube['10C'] - volcube['ATM'])
        
        volcube_interp_object_dict['tail_details']['ten_delta_put_smilespreads1'] = ten_delta_put_smilespreads[0]
        volcube_interp_object_dict['tail_details']['ten_delta_put_smilespreads2'] = ten_delta_put_smilespreads[-1]
        
        volcube_interp_object_dict['tail_details']['twentyfive_delta_put_smilespreads1'] = twentyfive_delta_put_smilespreads[0]
        volcube_interp_object_dict['tail_details']['twentyfive_delta_put_smilespreads2'] = twentyfive_delta_put_smilespreads[-1]
        
        volcube_interp_object_dict['tail_details']['twentyfive_delta_call_smilespreads1'] = twentyfive_delta_call_smilespreads[0]
        volcube_interp_object_dict['tail_details']['twentyfive_delta_call_smilespreads2'] = twentyfive_delta_call_smilespreads[-1]
        
        volcube_interp_object_dict['tail_details']['ten_delta_call_smilespreads1'] = ten_delta_call_smilespreads[0]
        volcube_interp_object_dict['tail_details']['ten_delta_call_smilespreads2'] = ten_delta_call_smilespreads[-1]

        if time_axis_interp_method in ['cubic', 'both']:
            interp_object_atm_variance_time = CubicSpline(nb_expiry_days, atm_variancetime, extrapolate=True)
            interp_object_ten_delta = CubicSpline(nb_expiry_days, ten_delta_put_smilespreads, extrapolate=True)
            interp_object_twentyfive_delta_put = CubicSpline(nb_expiry_days, twentyfive_delta_put_smilespreads, extrapolate=True)
            interp_object_twentyfive_delta_call = CubicSpline(nb_expiry_days, twentyfive_delta_call_smilespreads, extrapolate=True)
            interp_object_ten_delta_call = CubicSpline(nb_expiry_days, ten_delta_call_smilespreads, extrapolate=True)
            volcube_interp_object_dict['cubic'] = {'atm_variance_time': interp_object_atm_variance_time, '10P': interp_object_ten_delta, '10C': interp_object_ten_delta_call, 
                                                   '25P': interp_object_twentyfive_delta_put,'25C': interp_object_twentyfive_delta_call}
        if time_axis_interp_method in ['linear', 'both']:         
            interp_object_atm_variance_time = interp1d(nb_expiry_days, atm_variancetime, fill_value='extrapolate')
            interp_object_ten_delta = interp1d(nb_expiry_days, ten_delta_put_smilespreads, fill_value='extrapolate')
            interp_object_twentyfive_delta_put = interp1d(nb_expiry_days, twentyfive_delta_put_smilespreads, fill_value='extrapolate')
            interp_object_twentyfive_delta_call = interp1d(nb_expiry_days, twentyfive_delta_call_smilespreads, fill_value='extrapolate')
            interp_object_ten_delta_call = interp1d(nb_expiry_days, ten_delta_call_smilespreads, fill_value='extrapolate')
            volcube_interp_object_dict['linear'] = {'atm_variance_time': interp_object_atm_variance_time, '10P': interp_object_ten_delta, '10C': interp_object_ten_delta_call, 
                                                    '25P': interp_object_twentyfive_delta_put,'25C': interp_object_twentyfive_delta_call}
 
    return volcube_interp_object_dict


############################################################################################################################################################################
## Calculation of SVI (Stochastic Volatility Inspired) parmeters from market data
############################################################################################################################################################################

def svi_calibration_func(volcube):

    volcube_implied_strikes = copy.deepcopy(volcube)
    volcube_implied_log_moneyness = copy.deepcopy(volcube)
    
    currpair_convention_days = 365

    put_delta_dict = {'10P': -0.10, '25P': -0.25, 'ATM': -0.5, '25C': -0.75, '10C': -0.90}
    delta_keys = list(put_delta_dict.keys())
    volcube_vol = volcube[delta_keys]
    volcube_vol_from_svi_params = copy.deepcopy(volcube_vol)
    volcube_vol_from_svi_params[delta_keys] = np.nan

    tenors = list(volcube.index)
    for tenor in tenors:
        Te = volcube.loc[tenor,'Expiry_Days'] / currpair_convention_days
        Td = volcube.loc[tenor,'Value_Days'] / currpair_convention_days
        rf = volcube.loc[tenor,'Rate1'] / 100
        Ft = volcube.loc[tenor,'Forward_Rate']
        option_type = 'put'
        for col, put_delta in put_delta_dict.items():
            vol = volcube.loc[tenor, col]
            K = strike_from_spot_delta(Ft, Te, Td, vol, rf, put_delta, option_type)
            volcube_implied_strikes.loc[tenor, col] = K

    volcube_implied_log_moneyness[delta_keys] = volcube_implied_strikes[delta_keys].div(volcube_implied_strikes['Forward_Rate'], axis=0)
    volcube_implied_log_moneyness = np.log(volcube_implied_log_moneyness[delta_keys])

    ############ actual sv calibration per tenor #######################
    
    svi_params_df = pd.DataFrame(index=tenors, columns = ['a', 'b', 'rho', 'm', 'sigma'])
    x0 = [0.05, 0.2, -0.3, 0.0, 0.1] # initial values a, b, rho, m, sigma
    bounds = (
        [-np.inf, 0, -0.999, -np.inf, 1e-4],
        [ np.inf, np.inf,  0.999,  np.inf, np.inf])
    
    for tenor in tenors:
        k = np.array(volcube_implied_log_moneyness.loc[tenor,:])
        vol_mkt = np.array(volcube[delta_keys].loc[tenor,:])

        res = least_squares(residuals, x0, bounds=bounds, args=(k, vol_mkt))
        a, b, rho, m, sigma = res.x
        svi_params_df.loc[tenor,:] = a, b, rho, m, sigma

        # to check the calibration accuracy
        # volcube_vol_from_svi_params.loc[tenor,:] = volcube_implied_log_moneyness.loc[tenor,:].apply(lambda x: svi_raw(x, a, b, rho, m, sigma))
        # volcube_vol_diff = volcube_vol_from_svi_params - volcube_vol

    return svi_params_df, volcube_implied_strikes



############################################################################################################################################################################
## Local Vol Model (No Parameters)
############################################################################################################################################################################

#### Building the grid of maturities and surface over which the call prices and local vol will be calculated
def build_maturities_strikes(eval_date, volcube_implied_strikes, linearmktdata_df,linearmktdata_interp_object_dict,linearmktdata_time_axis_interp_method='linear', all_strikes_boolean=True):
    nb_steps = 50
    bin_must = 20
    bin_others = 8

    delta_cols = ['10P','25P','ATM','25C','10C']
    delta_cols_atm_25 = ['25P','ATM','25C']
    strikes = sorted((volcube_implied_strikes[delta_cols]).values.flatten())
    strikes = [float(round(x,4)) for x in strikes]
    if not (all_strikes_boolean):
        
        # optimize otherwise too many strikes
        strikes_must = sorted((volcube_implied_strikes[delta_cols_atm_25]).values.flatten())
        strikes_must = [float(round(x,4)) for x in strikes_must]

        strikes_others = list(set(strikes) - set(strikes_must))

        df_must = pd.DataFrame({"numbers": strikes_must})
        df_must["bin"] = pd.cut(df_must["numbers"], bins=bin_must)
        sparse_avg_must = df_must.groupby("bin", observed=True)["numbers"].mean().tolist()

        df_others = pd.DataFrame({"numbers": strikes_others})
        df_others["bin"] = pd.cut(df_others["numbers"], bins=bin_others)
        sparse_avg_others = df_others.groupby("bin", observed=True)["numbers"].mean().tolist()

        strikes = sparse_avg_must + sparse_avg_others
        strikes = [float(round(x,4)) for x in strikes]
        strikes = list(set(strikes))
        strikes.sort()
        
    std_expiry_dates = list(volcube_implied_strikes['Expiry_Date'])
    expiry_date1, expiry_date2 = std_expiry_dates[0], std_expiry_dates[-1]

    expiry_dates = business_dates_between_two_dates(expiry_date1,expiry_date2)
    indices = np.linspace(0, len(expiry_dates) - 1, nb_steps, dtype=int)
    
    expiry_dates_equally_spaced = [expiry_dates[i] for i in indices] # try to be equally spaced business days

    interp_data_df = linearmktdata_interp_expiry_list_func(eval_date, linearmktdata_df, linearmktdata_interp_object_dict, expiry_list = expiry_dates_equally_spaced, linearmktdata_time_axis_interp_method=linearmktdata_time_axis_interp_method)

    return interp_data_df, strikes


####### Building the 2 dimensional call price surface ########
def build_call_surface(interp_data_df, strikes, option_details_dict, currpair_mktdata_dict_pricing_date, smile_vol_model ='std_cubic_interp_vol_model', 
                       volmktdata_time_axis_interp_method = 'linear', price_greeks_concise_boolean = True):
    """
    Build call price surface C(K,T) from implied vol surface.

    vol_surface shape: len(expiry_dates) x len(strikes)
    """
    option_details_dict['CallPut'] = 'Call' # should always be Call
    expiry_dates = list(interp_data_df['De'])
    call_prices_surface = np.zeros((len(expiry_dates),len(strikes)))
    count = 0
    for i, expiry_date in enumerate(expiry_dates):
        for j, Strike in enumerate(strikes):
            #print (count, i,j,Strike, expiry_date)
            option_details_dict['Strike'] = Strike
            option_details_dict['Expiry'] = expiry_date

            Spot, Ft, rf, rd, Te, Td, De, Dd, Ds = interp_data_df.loc[expiry_date,:]

            mktdata_details_dict = {'Spot':Spot, 'Ft':Ft, 'rf':rf, 'rd':rd, 'Te':Te, 'Td':Td, 'De':De, 'Dd':Dd, 'Ds':Ds,'sigma': None, 'sigma_ATM': None}
            sigma, sigma_ATM = smile_vol_func(option_details_dict, mktdata_details_dict, currpair_mktdata_dict_pricing_date,smile_vol_model,volmktdata_time_axis_interp_method)
            print (sigma)
            mktdata_details_dict['sigma'] = sigma
            mktdata_details_dict['sigma_ATM'] = sigma_ATM

            output = VanillaPriceGreeks_BS(option_details_dict, mktdata_details_dict,price_greeks_concise_boolean)
            
            call_prices_surface[i, j] = output.loc['Premium_2ndCcy_pips','Value'] # will be used in dC/dK, need to be same units
            count = count + 1
            #print (count, i,j,Strike, expiry_date)

    return call_prices_surface




##### Building the 2 dimensional local vol surface (using RectBivariateSpline #####
##############################################################################################
def dupire_local_vol_bivariate_spline_func(interp_data_df, strikes, option_details_dict, currpair_mktdata_dict_pricing_date, smile_vol_model ='std_cubic_interp_vol_model', 
                       volmktdata_time_axis_interp_method = 'linear', price_greeks_concise_boolean = True):
    """
    Computes Dupire local volatility surface.

    Dupire FX formula:

    sigma_loc^2(K,T) =
        [dC/dT + (rd-rf) K dC/dK + rf C]
        /
        [0.5 K^2 d2C/dK2]
    """
    expiry_days = list(interp_data_df['Te'])
 
    expiry_years_array = np.asarray(expiry_days)/365
    strikes_array = np.asarray(strikes)
    expiry_dates = list(interp_data_df['De'])

    call_prices_surface = build_call_surface(interp_data_df, strikes, option_details_dict, currpair_mktdata_dict_pricing_date, smile_vol_model =smile_vol_model, 
                                      volmktdata_time_axis_interp_method = volmktdata_time_axis_interp_method, price_greeks_concise_boolean = price_greeks_concise_boolean)

    # Smooth interpolation of C(T,K)
    spline = RectBivariateSpline(
        expiry_years_array,
        strikes_array,
        call_prices_surface,
        kx=3,
        ky=3
    )

    local_vol_surface = np.zeros_like(call_prices_surface)

    for i, (Te_years, expiry_date) in enumerate(zip(expiry_years_array, expiry_dates)):
        for j, K in enumerate(strikes_array):
            # print (i,j,Te_years, expiry_date,K)

            Spot, Ft, rf, rd, Te, Td, De, Dd, Ds = interp_data_df.loc[expiry_date,:]

            C = float(spline(Te_years, K, dx=0, dy=0))
            dC_dT = float(spline(Te_years, K, dx=1, dy=0))
            dC_dK = float(spline(Te_years, K, dx=0, dy=1))
            d2C_dK2 = float(spline(Te_years, K, dx=0, dy=2))

            # C = spline(Te_years, K, dx=0, dy=0)[0, 0]
            # dC_dT = spline(Te_years, K, dx=1, dy=0)[0, 0]
            # dC_dK = spline(Te_years, K, dx=0, dy=1)[0, 0]
            # d2C_dK2 = spline(Te_years, K, dx=0, dy=2)[0, 0]

            numerator = dC_dT + (rd - rf) * K * dC_dK + rf * C
            denominator = 0.5 * K**2 * d2C_dK2

            local_var = numerator / denominator

            if local_var > 0 and np.isfinite(local_var):
                local_vol_surface[i, j] = np.sqrt(local_var)
            else:
                local_vol_surface[i, j] = np.nan

    return local_vol_surface, expiry_years_array,strikes_array



##### Building the 2 dimensional local vol surface (using BS Greeks #####
##############################################################################################

def analytical_gk_derivatives(S, K, T, rd, rf, sigma):
    """Calculates exact analytical derivatives for Garman-Kohlhagen option surfaces."""
    if T <= 0:
        return 0.0, 0.0, 0.0, 0.0
        
    d1 = (np.log(S / K) + (rd - rf + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # 1. Exact Call Price (C)
    C = S * np.exp(-rf * T) * ss.norm.cdf(d1) - K * np.exp(-rd * T) * ss.norm.cdf(d2)
    
    # 2. Exact Dual Delta (dC_dK)
    dC_dK = -np.exp(-rd * T) * ss.norm.cdf(d2)
    
    # 3. Exact Dual Gamma (d2C_dK2)
    d2C_dK2 = (np.exp(-rd * T) * ss.norm.pdf(d2)) / (K * sigma * np.sqrt(T))
    
    # 4. Exact Dual Theta / Price derivative w.r.t Maturity (dC_dT)
    term1 = (S * np.exp(-rf * T) * ss.norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
    term2 = rf * S * np.exp(-rf * T) * ss.norm.cdf(d1)
    term3 = rd * K * np.exp(-rd * T) * ss.norm.cdf(d2)
    dC_dT = term1 - term2 + term3
    
    return C, dC_dT, dC_dK, d2C_dK2



def dupire_local_vol_bs_greeks_func(interp_data_df, strikes, option_details_dict, currpair_mktdata_dict_pricing_date, smile_vol_model ='std_cubic_interp_vol_model', 
                       volmktdata_time_axis_interp_method = 'linear'):
    """
    Computes Dupire local volatility surface.

    Dupire FX formula:

    sigma_loc^2(K,T) =
        [dC/dT + (rd-rf) K dC/dK + rf C]
        /
        [0.5 K^2 d2C/dK2]
    """
    expiry_days = list(interp_data_df['Te'])
 
    expiry_years_array = np.asarray(expiry_days)/365
    strikes_array = np.asarray(strikes)
    expiry_dates = list(interp_data_df['De'])
    smile_vol_model ='std_cubic_interp_vol_model'
    volmktdata_time_axis_interp_method = 'linear'

    local_vol_surface = np.zeros((len(expiry_years_array),len(strikes_array)))
    # FLAT_VOL = 0.05

    for i, (Te_years, expiry_date) in enumerate(zip(expiry_years_array, expiry_dates)):
        for j, K in enumerate(strikes_array):
            # print (i,j,Te_years, expiry_date,K)
            
            option_details_dict['Expiry'] = expiry_date
            option_details_dict['Strike'] = K

            Spot, Ft, rf, rd, Te, Td, De, Dd, Ds = interp_data_df.loc[expiry_date,:]
            mktdata_details_dict = {'Spot':float(Spot), 'Ft':Ft, 'rf':rf, 'rd':rd, 'Te':Te, 'Td':Td, 'De':De, 'Dd':Dd, 'Ds':Ds,'sigma': None, 'sigma_ATM': None}

            sigma, sigma_ATM = smile_vol_func(option_details_dict, mktdata_details_dict, currpair_mktdata_dict_pricing_date,smile_vol_model,volmktdata_time_axis_interp_method)

            C, dC_dT, dC_dK, d2C_dK2 = analytical_gk_derivatives(Spot, K, Te_years, rd, rf, sigma)

           
            numerator = dC_dT + (rd - rf) * K * dC_dK + rf * C
            denominator = 0.5 * K**2 * d2C_dK2

            local_var = numerator / denominator

            if local_var > 1e-12 and np.isfinite(local_var):
                local_vol_surface[i, j] = np.sqrt(local_var)
            else:
                local_vol_surface[i, j] = np.nan

    return local_vol_surface, expiry_years_array,strikes_array




############################################################################################################################################################################
############################################################################################################################################################################
############################################################################################################################################################################

############################################################################################
# Density functions and d1d2 functions for Black-Scholes-Merton formula
############################################################################################
def N(d):
    ''' Cumulative density function of standard normal random variable x'''
    return ss.norm.cdf(d)

def dN(x):
    ''' Probability density function of standard normal random variable x'''
    return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)
  
def d1d2(Ft, K, Te, sigma):
    ''' Black Scholes-Merton d1 function'''
    d1 = (math.log(Ft / K) +  (0.5 * sigma * sigma) * Te) /(sigma * math.sqrt(Te))
    d2 = d1 - sigma * math.sqrt(Te)
    
    return d1, d2

def analytical_put_delta(Ft, Strike, Te, Td, rf, sigma):
    d1, d2 = d1d2(Ft, Strike, Te, sigma)
    analytical_delta = - math.exp(rf * Td) * (1 - N(d1))
    return analytical_delta

def analytical_call_delta(Ft, Strike, Te, Td, rf, sigma):
    d1, d2 = d1d2(Ft, Strike, Te, sigma)
    analytical_delta = math.exp(rf * Td) * N(d1)
    return analytical_delta

############################################################################################
# imply strike from spot delta, forward delta, premium-adjusted forward delta
############################################################################################

def strike_from_spot_delta(Ft, Te,Td, vol, rf, spot_delta, option_type):
    """
    premium-unadjusted spot delta
    rf: foreign interest rate
    """

    df_f = np.exp(-rf * Td)

    if option_type == "call":
        d1 = ss.norm.ppf(spot_delta / df_f)
    elif option_type == "put":
        d1 = -ss.norm.ppf(-spot_delta / df_f)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    K = Ft * np.exp(-d1 * vol * np.sqrt(Te) + 0.5 * vol**2 * Te)
    return K


def strike_from_forward_delta(Ft, Te,Td, vol, forward_delta, option_type):
    """
    delta: call delta positive, put delta negative
    option_type: "call" or "put"
    """

    if option_type == "call":
        d1 = ss.norm.ppf(forward_delta)
    elif option_type == "put":
        d1 = ss.norm.ppf(forward_delta + 1.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    K = Ft * np.exp(-d1 * vol * np.sqrt(Te) + 0.5 * vol**2 * Te)
    return K

def strike_from_premium_adjusted_forward_delta(Ft, Te, vol, delta, option_type):
    """
    Premium-adjusted forward delta inversion.
    delta: call positive, put negative
    """

    sqrtT = np.sqrt(Te)

    def d1(K):
        return (np.log(Ft / K) + 0.5 * vol**2 * Te) / (vol * sqrtT)

    def d2(K):
        return d1(K) - vol * sqrtT

    def pa_delta(K):
        if option_type == "call":
            return (K / Ft) * ss.norm.cdf(d2(K))
        elif option_type == "put":
            return -(K / Ft) * ss.norm.cdf(-d2(K))
        else:
            raise ValueError("option_type must be 'call' or 'put'")

    def objective(K):
        return pa_delta(K) - delta

    return brentq(objective, 0.01 * Ft, 5.0 * Ft)


############################################################################################################################################################################
## Interpolation of Linear Market Data #
############################################################################################################################################################################
def linearmktdata_interp_func(eval_date, linearmktdata_df, linearmktdata_interp_object_dict, expiry = None, linearmktdata_time_axis_interp_method = 'cubic'):
  
    interp_obj_linearmktdata = linearmktdata_interp_object_dict['cubic'] if linearmktdata_time_axis_interp_method == 'cubic' else linearmktdata_interp_object_dict['linear'] if linearmktdata_time_axis_interp_method == 'linear' else None
    std_tenors = list(linearmktdata_df['tenors'])
    std_expiry_dates = list(linearmktdata_df['expiry_date'])
    spot_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'value_date'].values[0]

    if expiry in std_tenors:
        expiry_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'expiry_date'].values[0]
        interp_rate1 = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'rate1'].values[0]
        interp_rate2 = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'rate2'].values[0]
        interp_forward_rate = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'forward_rate'].values[0]
        expiry_date_nb_days = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'expiry_date_nb_days'].values[0]                                                                                                                                                                                   
        value_date_nb_days = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'value_date_nb_days'].values[0]
        return interp_rate1, interp_rate2, interp_forward_rate
    
    elif expiry in std_expiry_dates:
        expiry_date = expiry
        interp_rate1 = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'rate1'].values[0]
        interp_rate2 = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'rate2'].values[0]
        interp_forward_rate = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'forward_rate'].values[0]
        expiry_date_nb_days = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'expiry_date_nb_days'].values[0]
        value_date_nb_days = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'value_date_nb_days'].values[0]
        return interp_rate1, interp_rate2, interp_forward_rate
    else:
        if len(expiry) == 10: # 2026-01-01 format
            expiry_date = expiry
            value_date = next_bus_day_ref(expiry_date, 2)
            value_date_nb_days = calendar_days(eval_date, value_date)
            interp_rate1 = float(interp_obj_linearmktdata['rate1'](value_date_nb_days))
            interp_rate2 = float(interp_obj_linearmktdata['rate2'](value_date_nb_days))
            interp_forward_rate = float(interp_obj_linearmktdata['forward_rate'](value_date_nb_days))
            expiry_date_nb_days = calendar_days(eval_date, expiry_date)
    
    Spot = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'forward_rate'].values[0]
    rf = interp_rate1 * 0.01
    rd = interp_rate2 * 0.01
    Ft = interp_forward_rate
    Te = expiry_date_nb_days
    Td = value_date_nb_days
    De = expiry_date
    Dd = value_date
    Ds = spot_date

    return Spot, Ft, rf, rd, Te, Td, De, Dd, Ds

def linearmktdata_interp_expiry_list_func(eval_date, linearmktdata_df, linearmktdata_interp_object_dict, expiry_list = None, linearmktdata_time_axis_interp_method = 'cubic'):
  
    interp_obj_linearmktdata = linearmktdata_interp_object_dict['cubic'] if linearmktdata_time_axis_interp_method == 'cubic' else linearmktdata_interp_object_dict['linear'] if linearmktdata_time_axis_interp_method == 'linear' else None
    std_tenors = list(linearmktdata_df['tenors'])
    std_expiry_dates = list(linearmktdata_df['expiry_date'])
    spot_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'value_date'].values[0]
    Spot = linearmktdata_df.loc[linearmktdata_df['tenors'] == 'SPOT', 'forward_rate'].values[0]
    
    interp_data_df = pd.DataFrame(index = expiry_list, columns = ['Spot', 'Ft', 'rf', 'rd', 'Te', 'Td', 'De', 'Dd', 'Ds'])

    for expiry in expiry_list:
            
        if expiry in std_tenors: # expiry in format '1M", "3M"
            expiry_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'expiry_date'].values[0]
            value_date = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'value_date'].values[0]
            expiry_date_nb_days = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'expiry_date_nb_days'].values[0]                                                                                                                                                                                   
            value_date_nb_days = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'value_date_nb_days'].values[0]
            
            interp_rate1 = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'rate1'].values[0]
            interp_rate2 = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'rate2'].values[0]
            interp_forward_rate = linearmktdata_df.loc[linearmktdata_df['tenors'] == expiry, 'forward_rate'].values[0]
            
            #return interp_rate1, interp_rate2, interp_forward_rate
        
        elif expiry in std_expiry_dates: # expiry in format '2016-01-02'
            expiry_date = expiry
            value_date = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'value_date'].values[0]
            expiry_date_nb_days = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'expiry_date_nb_days'].values[0]
            value_date_nb_days = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'value_date_nb_days'].values[0]
            
            interp_rate1 = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'rate1'].values[0]
            interp_rate2 = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'rate2'].values[0]
            interp_forward_rate = linearmktdata_df.loc[linearmktdata_df['expiry_date'] == expiry, 'forward_rate'].values[0]

            #return interp_rate1, interp_rate2, interp_forward_rate
        else:
            if len(expiry) == 10: # 2026-01-01 format
                expiry_date = expiry
                value_date = next_bus_day_ref(expiry_date, 2)
                value_date_nb_days = calendar_days(eval_date, value_date)
                interp_rate1 = float(interp_obj_linearmktdata['rate1'](value_date_nb_days))
                interp_rate2 = float(interp_obj_linearmktdata['rate2'](value_date_nb_days))
                interp_forward_rate = float(interp_obj_linearmktdata['forward_rate'](value_date_nb_days))
                expiry_date_nb_days = calendar_days(eval_date, expiry_date)
        
        interp_data_df.loc[expiry,:] = [Spot,interp_forward_rate,interp_rate1 * 0.01,interp_rate2 * 0.01,expiry_date_nb_days,value_date_nb_days,expiry_date,value_date,spot_date]
    
    return interp_data_df

############################################################################################################################################################################
## SVI Calibration Functions # ( Not used in the current version of the code, but can be used for future extension to SVI implied volatility surface construction and interpolation)


# | Parameter | Meaning          | Trading intuition             |
# | --------- | ---------------- | ----------------------------- |
# | **a**     | Vertical level   | Overall variance level        |
# | **b**     | Slope / scale    | Strength of smile             |
# | **ρ**     | Skew (-1 to +1)  | Left/right skew (RR)          |
# | **m**     | Horizontal shift | Smile center (where ATM sits) |
# | **σ**     | Curvature        | How “fat” the wings are       |

# | k ::  ln(K/F) or (K /F - 1): log-moneyness or strike moneyness

# example d
# k = np.array([-0.2, -0.1, 0.0, 0.1, 0.2]) # ln(K/F) or (K /F - 1): log-moneyness or strike moneyness
# vol_mkt = np.array([0.09, 0.07, 0.06, 0.065, 0.08])
# x0 = [0.05, 0.2, -0.3, 0.0, 0.1]
# bounds = ([-np.inf, 0, -0.999, -np.inf, 1e-4],[ np.inf, np.inf,  0.999,  np.inf, np.inf])

# res = least_squares(residuals, x0, bounds=bounds, args=(k, vol_mkt))
# params = res.x
# a, b, rho, m, sigma = res.x 
############################################################################################################################################################################

def svi_raw(k, a, b, rho, m, sigma):
    return a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))

def residuals(params, k, vol_mkt):
    return svi_raw(k, *params) - vol_mkt


############################################################################################################################################################################
## Interpolation of Smile Vol using Standard Cubic Interpolation Method
############################################################################################################################################################################

def std_cubic_interp_vol_model_func(Ft, Strike, Te, Td, rf, volcube_interp_object_dict, volmktdata_time_axis_interp_method = 'linear'):
    
    expirydate_nb_days = Te

    nb_expiry_days1 = volcube_interp_object_dict['tail_details']['nb_expiry_days1']
    nb_expiry_days2 = volcube_interp_object_dict['tail_details']['nb_expiry_days2']

    if (expirydate_nb_days < nb_expiry_days1):
        interp_atm_vol = volcube_interp_object_dict['tail_details']['flatvol1']
        interp_ten_delta_put_smilespread = volcube_interp_object_dict['tail_details']['ten_delta_put_smilespreads1']
        interp_twentyfive_delta_put_smilespread = volcube_interp_object_dict['tail_details']['twentyfive_delta_put_smilespreads1']
        interp_twentyfive_delta_call_smilespread = volcube_interp_object_dict['tail_details']['twentyfive_delta_call_smilespreads1']
        interp_ten_delta_call_smilespread = volcube_interp_object_dict['tail_details']['ten_delta_call_smilespreads1']
    elif (expirydate_nb_days > nb_expiry_days2):
        interp_atm_vol = volcube_interp_object_dict['tail_details']['flatvol2']
        interp_ten_delta_put_smilespread = volcube_interp_object_dict['tail_details']['ten_delta_put_smilespreads2']
        interp_twentyfive_delta_put_smilespread = volcube_interp_object_dict['tail_details']['twentyfive_delta_put_smilespreads2']
        interp_twentyfive_delta_call_smilespread = volcube_interp_object_dict['tail_details']['twentyfive_delta_call_smilespreads2']
        interp_ten_delta_call_smilespread = volcube_interp_object_dict['tail_details']['ten_delta_call_smilespreads2']
    else: 
        interp_obj_volcube = volcube_interp_object_dict['cubic'] if volmktdata_time_axis_interp_method == 'cubic' else volcube_interp_object_dict['linear'] if volmktdata_time_axis_interp_method == 'linear' else None   
        
        interp_atm_variance = float(interp_obj_volcube['atm_variance_time'](expirydate_nb_days))
        interp_atm_vol = math.sqrt(interp_atm_variance / expirydate_nb_days)
        interp_ten_delta_put_smilespread = float(interp_obj_volcube['10P'](expirydate_nb_days))
        interp_twentyfive_delta_put_smilespread = float(interp_obj_volcube['25P'](expirydate_nb_days))
        interp_twentyfive_delta_call_smilespread = float(interp_obj_volcube['25C'](expirydate_nb_days))
        interp_ten_delta_call_smilespread = float(interp_obj_volcube['10C'](expirydate_nb_days))

        
    interp_ten_delta_put_vol = interp_atm_vol + interp_ten_delta_put_smilespread
    interp_twentyfive_delta_put_vol = interp_atm_vol + interp_twentyfive_delta_put_smilespread
    interp_twentyfive_delta_call_vol = interp_atm_vol + interp_twentyfive_delta_call_smilespread
    interp_ten_delta_call_vol = interp_atm_vol + interp_ten_delta_call_smilespread
    
    smilecurve = [interp_ten_delta_put_vol, interp_twentyfive_delta_put_vol, interp_atm_vol, interp_twentyfive_delta_call_vol, interp_ten_delta_call_vol]
    #smilecurve[:] = [vol / 100.0 for vol in smilecurve]
    putdeltas = [.10, .25, .50, .75, .90]

    sigma = smilecurve[2] # sigma to start the iteration is the ATM vol
    sigma_ATM = smilecurve[2]

    Te = Te / 365
    Td = Td / 365

    #smile_interp_method = 'newton_raphson'
    smile_interp_method = 'brentq_optimize'
    

    ##########################################################################
    # Newton Raphson Method ( with extrapolation True and delta bounds 0 & 1)
    ###########################################################################

    if smile_interp_method == 'newton_raphson':
            
        #cubic_spline_surface = CubicSpline(putdeltas, smilecurve)
        cubic_spline_surface = CubicSpline(putdeltas, smilecurve, extrapolate=True)
        
        delta_vol = 1.00
        count = 0
        h = 0.0001
        

        delta_lb = 1e-4
        delta_ub = 1-1e-4
        while (delta_vol > 0.001):
            
            analytical_delta = analytical_put_delta(Ft, Strike, Te, Td, rf, sigma)
            
            # delta calculation from analytical function
            delta_calculated = abs(analytical_delta) # To make the put delta scale always +ve to match with the put delta list
            delta = np.clip(delta_calculated, delta_lb, delta_ub)

            #delta_plus_h = np.clip(delta + h, 0.10, 0.90)
            delta_plus_h = np.clip(delta + h, delta_lb, delta_ub)

            # derivative calculation
            derivative_calculated = (cubic_spline_surface(delta_plus_h) - cubic_spline_surface(delta)) / h 
            if derivative_calculated == 0:
                derivative = 1e-6
            else:
                derivative = copy.deepcopy(derivative_calculated)

            # new delta calculation from delta and derivative
            new_delta_calculated = float(delta - (cubic_spline_surface(delta) / derivative))
            #new_delta = np.clip(new_delta_calculated, 0.10, 0.90)
            new_delta = np.clip(new_delta_calculated, delta_lb, delta_ub)
            

            # new vol calculation and delta_vol calculation to check convergence later 
            new_vol = float(cubic_spline_surface(new_delta))
            delta_vol = abs(new_vol - sigma)
            sigma_earlier = copy.deepcopy(sigma)

            sigma = new_vol
            count += 1

            output_dict = {'count': count,
                        'Ft': float(round(Ft,6)),
                        'Strike': Strike,
                        'Td': Td,
                        'Te': Te,
                        'rf': rf,
                        'analytical_delta': float(round(analytical_delta,6)),
                        'delta_calculated': float(round(delta_calculated,6)),
                        'delta': float(round(delta,6)),
                        'derivative_calculated': float(round(derivative_calculated,6)),
                        'derivative': float(round(derivative,6)),
                        'new_delta_calculated': float(round(new_delta_calculated,6)),
                        'new_delta': float(round(new_delta,6)),
                        'new_vol': float(round(new_vol,6)),
                        'sigma_earlier': float(round(sigma_earlier,6)),
                        'delta_vol': float(round(delta_vol,6)),
                        'sigma': float(round(sigma,6))
                        }
            if count == 50000:
                print("Warning: smile vol iteration did not converge.")
                print (output_dict)
                break
    
    
    ##########################################################################
    # Optimized Implementation using brentq
            # Using a robust root-finding algorithm from scipy.optimize completely eliminates the need for manual derivative approximations, prevents out-of-bounds 
                # extrapolation, and guarantees convergence if a root exists.
            # In implied volatility mapping, you want to find a volatility (\(\sigma \)) such that the absolute delta generated by your pricing model matches the 
                # delta derived from your volatility smile curve spline.
            # Guaranteed Convergence: As long as one boundary results in a negative value and the other results in a positive value (a sign change), 
                # brentq will always locate the root.
            # Strict Boundary Control: The parameters a=0.01 and b=1.00 explicitly prevent the solver from testing negative volatilities or infinite values that crash your pricing model.
    # Flat Extrapolation ( if your pricing model becomes unstable or erratic when evaluating extreme deep-tail risks.)
            # delta_lb = 0.10 & delta_ub = 0.90 for Flat exterpolation beyond 0.10 & 0.90 delta points
            # cubic_spline_surface = CubicSpline(putdeltas, smilecurve)
            # This approach clamps the volatility flat at the edge values if the option becomes deeply in-the-money or out-of-the-money. A delta of 0.05 will 
            # safely inherit the 0.10 delta volatility.

    # Linear Extrapolation to 0 and 1 Boundaries ( if you are pricing wing options (deep OTM/ITM) and need a continuous skew slope.)
            # delta_lb = 1e-4 & delta_ub = 1-1e-4 for Linear extrapolation beyond 0.10 & 0.90 delta points
            # cubic_spline_surface = CubicSpline(putdeltas, smilecurve, extrapolation = True)
            # If you want the volatility smile to naturally slope upward or downward all the way out to the boundaries, configure CubicSpline to allow boundary extrapolation,
            # but strictly clamp the input variable to the theoretical bounds of [0.0, 1.0].
    ###########################################################################

    if smile_interp_method == 'brentq_optimize':
            
        cubic_spline_surface = CubicSpline(putdeltas, smilecurve, extrapolate = True)
        #cubic_spline_surface = CubicSpline(putdeltas, smilecurve, extrapolate=True)
        
        delta_lb = 1e-4
        delta_ub = 1-1e-4

        def vol_solv_objective(sigma_guess):

            # delta calculation from analytical function
            analytical_delta = analytical_put_delta(Ft, Strike, Te, Td, rf, sigma_guess)
            delta_calculated = abs(analytical_delta) 
            delta = np.clip(delta_calculated, delta_lb, delta_ub) 

            new_vol = float(cubic_spline_surface(delta))
            new_vol = max(new_vol, 0.005) 

            return new_vol - sigma_guess
        
        try:
            sigma = brentq(vol_solv_objective, a=0.01, b=1.00, xtol=1e-5) # between 1% and 100%
        except ValueError as e:
            print(f"Optimization failed: {e}")
        
    
    return sigma, sigma_ATM




############################################################################################################################################################################
## Interpolation of Smile Vol using SVI Parameters
############################################################################################################################################################################

def svi_vol_model_func(Ft, Strike, Te, volcube, svi_params_df):
    # vol_log_moneyness_ladder = (np.log(Strike / volcube['Forward_Rate'])).to_frame()
    # interp_vol_ladder = copy.deepcopy(vol_log_moneyness_ladder)
    # interp_vol_ladder.columns = ['Smile_Vol']
    
    vol_log_moneyness = np.log(Strike / Ft)
    interp_vol_ladder = copy.deepcopy(volcube[['ATM','Expiry_Days']])
    interp_vol_ladder[['Smile','Smile_TimeVariance','ATM_TimeVariance']] = ''
    interp_vol_ladder = interp_vol_ladder[['Smile','ATM','Expiry_Days','Smile_TimeVariance','ATM_TimeVariance']]

    tenors = list(interp_vol_ladder.index)

    for tenor in tenors:
        a, b, rho, m, sigma = svi_params_df.loc[tenor,:]
        #interp_vol_ladder.loc[tenor] = svi_raw(vol_log_moneyness_ladder.loc[tenor,'Forward_Rate'], a, b, rho, m, sigma)
        interp_vol_ladder.loc[tenor,'Smile'] = svi_raw(vol_log_moneyness, a, b, rho, m, sigma)
        
    interp_vol_ladder['Smile_TimeVariance'] = interp_vol_ladder['Smile'] * interp_vol_ladder['Smile'] * interp_vol_ladder['Expiry_Days']
    interp_vol_ladder['ATM_TimeVariance'] = interp_vol_ladder['ATM'] * interp_vol_ladder['ATM'] * interp_vol_ladder['Expiry_Days']
    
    nb_expiry_days = np.array(interp_vol_ladder['Expiry_Days'])
    smile_time_variance = np.array(interp_vol_ladder['Smile_TimeVariance'])
    atm_time_variance = np.array(interp_vol_ladder['ATM_TimeVariance'])
    
    interp_object_smile_time_variance = interp1d(nb_expiry_days, smile_time_variance, fill_value='extrapolate')
    interp_object_atm_time_variance = interp1d(nb_expiry_days, atm_time_variance, fill_value='extrapolate')

    sigma = np.sqrt(interp_object_smile_time_variance(Te)/Te)
    sigma_ATM = np.sqrt(interp_object_atm_time_variance(Te)/Te)
  
    return sigma, sigma_ATM

def smile_vol_func(option_details_dict, mktdata_details_dict, currpair_mktdata_dict_pricing_date,smile_vol_model = 'std_cubic_interp_vol_model',volmktdata_time_axis_interp_method = 'linear'):
    Strike = option_details_dict['Strike']
    Ft = mktdata_details_dict['Ft']
    Te = mktdata_details_dict['Te']
    Td = mktdata_details_dict['Td']
    rf = mktdata_details_dict['rf']
    
    if smile_vol_model == 'std_cubic_interp_vol_model':
        volcube_interp_object_dict = currpair_mktdata_dict_pricing_date['volcube_interp_object_dict']
        volmktdata_time_axis_interp_method = volmktdata_time_axis_interp_method
        sigma, sigma_ATM = std_cubic_interp_vol_model_func(Ft, Strike, Te, Td, rf, volcube_interp_object_dict, volmktdata_time_axis_interp_method = volmktdata_time_axis_interp_method)

    elif smile_vol_model == 'svi_vol_model':
        svi_params_df = currpair_mktdata_dict_pricing_date['svi_params_df']
        volcube = currpair_mktdata_dict_pricing_date['volcube']
        sigma, sigma_ATM = svi_vol_model_func(Ft, Strike, Te, volcube, svi_params_df)
    
    return sigma, sigma_ATM



############################################################################################################################################################################    
## Calculation of Price & Greeks for Vanilla Options ( Closed form Black Scholes)
############################################################################################################################################################################

# option_details_dict = {'Eval_Date': '2026-01-02', 'Currpair': 'EURUSD', 'Expiry': '2026-01-21', 'Strike': 1.17, 'CallPut': 'Call', 'BuySell': 'Buy', 'Notional_For_Ccy': 1000000.0}

#def VanillaPriceGreeks_BS(option_details_dict, linearmktdata_df, linearmktdata_interp_object_dict, vol_details_dict, smile_vol_model, price_greeks_concise_boolean = True, linearmktdata_time_axis_interp_method='linear'):
    
def VanillaPriceGreeks_BS(option_details_dict, mktdata_details_dict,price_greeks_concise_boolean = True):

    EvalDate = option_details_dict['Eval_Date']
    Currpair = option_details_dict['Currpair']
    Expiry = option_details_dict['Expiry']
    Strike = option_details_dict['Strike']
    CallPut = option_details_dict['CallPut']
    BuySell = option_details_dict['BuySell']
    Notional_For_Ccy = option_details_dict['Notional_For_Ccy']
    currpair_convention_days = 365

    if (BuySell == 'Sell'): 
        BuySell_multiplier = -1.0
    elif (BuySell == 'Buy'):
        BuySell_multiplier = 1.0
    
    Spot, Ft, Te, Td,rf, rd = mktdata_details_dict['Spot'], mktdata_details_dict['Ft'], mktdata_details_dict['Te'], mktdata_details_dict['Td'], mktdata_details_dict['rf'],mktdata_details_dict['rd']
    Ds, De, Dd, sigma, sigma_ATM = mktdata_details_dict['Ds'], mktdata_details_dict['De'], mktdata_details_dict['Dd'], mktdata_details_dict['sigma'], mktdata_details_dict['sigma_ATM']

    # converting days to yearly fractional for black scholes input
    Te = Te / currpair_convention_days
    Td = Td / currpair_convention_days

    d1, d2 = d1d2(Ft, Strike, Te, sigma)
    
    if (CallPut == 'Call'):
        if (Te > 0):
            value = math.exp(-rd * Td) * (Ft * N(d1) - Strike * N(d2))
            analytical_delta = math.exp(-rf * Td) * N(d1)
            analytical_rho_d = Strike * Td * math.exp(-rd * Td) * N(d2)
            analytical_rho_f = -Spot * Td * math.exp(-rf * Td) * N(d1)
            analytical_theta = (1/365) * (Spot * math.exp(-rf * Td) * dN(d1) * sigma / (2 * math.sqrt(Te)) - rd * Strike * math.exp(-rf * Td) * N(d2) + rf * Spot * math.exp(-rf * Td) * N(d1))
        else:
            value = max(0, Ft - Strike)
            analytical_delta = math.exp(-rf * Td) if Ft > Strike else 0
            analytical_rho_d = Strike * Td * math.exp(-rd * Td) if Ft > Strike else 0
            analytical_rho_f = -Spot * Td * math.exp(-rf * Td) if Ft > Strike else 0
            analytical_theta = 0
            
    if (CallPut == 'Put'):
        if (Te > 0):
            value = math.exp(-rd * Td) * (Strike * N(-d2) - Ft * N(-d1))
            analytical_delta = - math.exp(-rf * Td) * (1 - N(d1)) 
            analytical_rho_d = -Strike * Td * math.exp(-rd * Td) * N(-d2)
            analytical_rho_f = Spot * Td * math.exp(-rf * Td) * N(-d1)
            analytical_theta = (1/365) * (Spot * math.exp(-rf * Td) * dN(d1) * sigma / (2 * math.sqrt(Te)) + rd * Strike * math.exp(-rf * Td) * N(-d2) - rf * Spot * math.exp(-rf * Td) * N(-d1))
        else:
            value = max(0, Strike - Ft)
            analytical_delta = -math.exp(-rf * Td) if Ft < Strike else 0
            analytical_rho_d = -Strike * Td * math.exp(-rd * Td) if Ft < Strike else 0
            analytical_rho_f = Spot * Td * math.exp(-rf * Td) if Ft < Strike else 0
            analytical_theta = 0
    
    ''' Common Analytical Greeks Calculations for Calls & Puts '''
    
    if (Te > 0):
        analytical_gamma = math.exp(-rf * Td) * dN(d1) / (Spot * sigma * math.sqrt(Te))
        analytical_vega = math.exp(-rf * Td) * Spot * math.sqrt(Te) * dN(d1) 
        
        analytical_vanna = math.exp(-rf * Td) * dN(d1) * d2 / sigma
        analytical_volga = math.exp(-rf * Td) * Spot * math.sqrt(Te) * dN(d1) * d1 * d2 / sigma
    else:
        analytical_gamma = 0
        analytical_vega = 0
        analytical_vanna = 0
        analytical_volga = 0
    
    
    ### for USDINR, USD is foreign currency and INR is the domestic currency
    ### for EURUSD, EUR is the foreign currency and USD is the domestic currency
    
    Notional_Dom_Ccy = Notional_For_Ccy * Strike
    
    premium_dom_pips = BuySell_multiplier * value                   
    premium_dom_perc = 100 * premium_dom_pips / Strike
    premium_for_perc = 100 * premium_dom_pips / Spot
    premium_for_pips = (premium_dom_pips / Spot) / Strike
    
    premium_dom_amount = 0.01 * premium_dom_perc * Notional_Dom_Ccy
    premium_for_amount =  0.01 * premium_for_perc * Notional_For_Ccy

    analytical_delta_for_perc = BuySell_multiplier * analytical_delta * 100                    
    analytical_delta_dom_perc = 0.01 * analytical_delta_for_perc * (Spot / Strike) * 100
    analytical_delta_dom_amount = 0.01 *analytical_delta_dom_perc * Notional_Dom_Ccy
    analytical_delta_for_amount = 0.01 * analytical_delta_for_perc * Notional_For_Ccy
    
    analytical_gamma_1Notionalforeign_1percSpot = BuySell_multiplier * analytical_gamma * 0.01 * Spot         
    analytical_gamma_for_amount = analytical_gamma_1Notionalforeign_1percSpot * Notional_For_Ccy
    
    analytical_vega_1Notionaldomestic_1percVol = BuySell_multiplier * analytical_vega * 0.01                
    analytical_vega_1Notionalforeign_1percVol = analytical_vega_1Notionaldomestic_1percVol / Spot
    
    analytical_vega_for_amount = analytical_vega_1Notionalforeign_1percVol * Notional_For_Ccy
    analytical_theta_for_amount = - BuySell_multiplier * analytical_theta * Notional_For_Ccy  / Spot        
    
    
    ''' Outputs in a dataframe '''
        
    output = pd.DataFrame(columns = ['Value'])
    
    output.loc['ContractDetails_#################'] = ''
    
    output.loc['CcyPair'] = Currpair
    output.loc['BuySell'] = BuySell
    output.loc['Horizon Date'] = EvalDate
    output.loc['Spot Date'] = Ds
    output.loc['CallPut'] = CallPut
    output.loc['Maturity'] = De
    output.loc['Expiry Date'] = De
    output.loc['Delivery Date'] = Dd
    #output.loc['Cut'] = Cut
    output.loc['Strike'] = Strike
    output.loc['Notional_1stCcy'] = Notional_For_Ccy
    output.loc['Notional_2ndCcy'] = Notional_Dom_Ccy
    #output.loc['Notional_1stCcy'] = "{:,}".format(Notional_For_Ccy)
    #output.loc['Notional_2ndCcy'] = "{:,}".format(int(Notional_Dom_Ccy))
    
    
    output.loc['MarketData_######################'] = ''
    output.loc['Spot'] = Spot
    output.loc['Swap Points'] =Ft - Spot
    output.loc['Forward'] = Ft
    
    output.loc['ATMVol_%'] = sigma_ATM * 100
    output.loc['SmileVol_%'] = sigma * 100
    output.loc['rd_%_2ndCcy'] = rd * 100
    output.loc['rf_%_1stCcy'] = rf * 100
    
    
    
    if (price_greeks_concise_boolean):
        
        output.loc['Premium_pips_perc_amount_##########################'] = ''
        output.loc['Premium_2ndCcy_pips'] = premium_dom_pips
        output.loc['Premium_1stCcy_perc'] = premium_for_perc
        output.loc['Premium_1stCcy_amount'] = round(premium_for_amount,2)
        
        output.loc['Analytical_Greeks_1stCcy_perc_amount_##############'] = ''
        output.loc['Analytical_Delta_1stCcy_perc'] = round(analytical_delta_for_perc,4)
        output.loc['Analytical_Delta_1stCcy_amount'] = int(analytical_delta_for_amount)
        output.loc['Analytical_Gamma_1stCcy_amount'] = int(analytical_gamma_for_amount)
        output.loc['Analytical_Vega_1stCcy_amount'] = int(analytical_vega_for_amount)
        output.loc['Analytical_Theta_1stCcy_amount'] = int(analytical_theta_for_amount)
        
    else :
        
        output.loc['Price_AnalyticalGreeks'] = ''
        output.loc['Premium_for_perc'] = premium_for_perc
        
        output.loc['Price_pips_perc_amount'] = ''
        
        output.loc['Notional_For_Ccy'] = Notional_For_Ccy
        output.loc['Notional_Dom_Ccy'] = Notional_Dom_Ccy
        output.loc['premium_dom_pips'] = premium_dom_pips # changed here
        output.loc['premium_dom_perc'] = premium_dom_perc 
        output.loc['premium_for_pips'] = premium_for_pips
        output.loc['premium_for_perc'] = premium_for_perc
        
        output.loc['premium_dom_amount'] = premium_dom_amount
        output.loc['premium_for_amount'] = premium_for_amount
        
        
        output.loc['Analytical_Delta_dom_for_perc_amount'] = ''
        
        output.loc['analytical_delta_dom_perc'] = analytical_delta_dom_perc
        output.loc['analytical_delta_for_perc'] = analytical_delta_for_perc
        output.loc['analytical_delta_dom_amount'] = analytical_delta_dom_amount
        output.loc['analytical_delta_for_amount'] = analytical_delta_for_amount
        
        output.loc['Analytical_Greeks_for_amount_###################'] = ''
        output.loc['analytical_delta_1stCcy_amount'] = "{:,}".format(int(analytical_delta_for_amount))
        output.loc['analytical_gamma_1stCcy_amount'] = "{:,}".format(int(analytical_gamma_for_amount))
        output.loc['analytical_vega_1stCcy_amount'] = "{:,}".format(int(analytical_vega_for_amount))
        
    return output






############################################################################################################################################################################    
## Calculation of Price & Greeks for Vanilla Options (Monte Carlo ) using local volatility model
############################################################################################################################################################################

##### repairing the local vol surface : filling the NaN values with good predicted data ######################
def local_vol_surface_repair_func(local_vol_surface,expiry_years_array,strikes_array):
        
    # Your starting data shapes
    # x: 1D array of shape (M,)
    # y: 1D array of shape (N,)
    # z: 2D array of shape (M, N) containing scattered NaNs

    # 1. Expand the 1D axes into 2D coordinate grids matching your Z matrix shape
    X, Y = np.meshgrid(expiry_years_array, strikes_array, indexing='ij')

    # 2. Extract ONLY the valid coordinates where Z is not a NaN
    valid_mask = ~np.isnan(local_vol_surface)

    # 3. Flatten coordinates and values to create structural pairs for griddata
    known_points = np.column_stack((X[valid_mask], Y[valid_mask]))
    known_values = local_vol_surface[valid_mask]

    # 4. Use the complete unflattened grid coordinate maps as target query points
    # griddata handles the 2D matrix shape requirements natively for target outputs
    repaired_z = griddata(
        points=known_points, 
        values=known_values, 
        xi=(X, Y), 
        method='linear' # Options: 'linear', 'nearest', 'cubic'
    )

    # 5. Fix edge-cases: any boundary NaN missed by 'linear' can be swept with 'nearest'
    if np.isnan(repaired_z).any():
        edge_fill = griddata(known_points, known_values, (X, Y), method='nearest')
        repaired_z[np.isnan(repaired_z)] = edge_fill[np.isnan(repaired_z)]

    local_vol_surface_repaired = copy.deepcopy(repaired_z)

    return local_vol_surface_repaired


##### Method 1 : Using RegularGridInterpolator : Slower method ######################
#################################################################################################

def generating_final_S_using_RegularGridInterpolator(Spot,Te,rd,rf,local_vol_surface_repaired,expiry_years_array,strikes_array,n_paths,n_steps,seed):

    # Interpolator expects points as (time, spot)
    lv_interp = RegularGridInterpolator(
        points=(expiry_years_array, strikes_array),
        values=local_vol_surface_repaired,
        bounds_error=False,
        fill_value=None,
        method = 'linear'
    )

    dt = Te / n_steps
    sqrt_dt = np.sqrt(dt)

    # running the Monte Carlo 
    rng = np.random.default_rng(seed)

    min_strike = strikes_array[0]
    max_strike = strikes_array[-1]

    # Antithetic Variates Implementation to crush random noise
    half_paths = n_paths // 2

    S = np.full(n_paths, Spot, dtype=float)

    for step in range(n_steps):
        #t = min((step + 1) * dt, expiry_years_array[-1])
        t = min(step * dt, expiry_years_array[-1])

        clipped_S = np.clip(S, min_strike, max_strike)

        query_points = np.column_stack([np.full(n_paths, t), clipped_S])
        sigma = lv_interp(query_points)
        #print('sigma',sigma)
        # Basic safety cleaning
        sigma = np.where(np.isfinite(sigma), sigma, 0.0)
        sigma = np.maximum(sigma, 1e-6)

        #Z = rng.standard_normal(n_paths)
        # Symmetric Antithetic Gaussian Shocks
        epsilon = rng.standard_normal(half_paths)
        Z = np.concatenate([epsilon, -epsilon])

        # Log-Euler scheme
        S *= np.exp((rd - rf - 0.5 * sigma**2) * dt + sigma * sqrt_dt * Z)
        
    print('Completed Step: ', step)
    return S


##### Method 2 : Using numba library : Faster method ######################
#################################################################################################

@njit(fastmath=True)
def bilinear_interp_2d(x_grid, y_grid, values, x, y):
    """Blazing fast 2D linear interpolation compiled directly to machine code."""
    # Find binary search slots on the grid (like np.searchsorted)
    i = np.searchsorted(x_grid, x) - 1
    i = max(0, min(i, len(x_grid) - 2))
    
    j = np.searchsorted(y_grid, y) - 1
    j = max(0, min(j, len(y_grid) - 2))
    
    x0, x1 = x_grid[i], x_grid[i+1]
    y0, y1 = y_grid[j], y_grid[j+1]
    
    # Weight factors
    fx = (x - x0) / (x1 - x0)
    fy = (y - y0) / (y1 - y0)
    
    # 4 corners
    v00 = values[i, j]
    v10 = values[i+1, j]
    v01 = values[i, j+1]
    v11 = values[i+1, j+1]
    
    # Interpolate
    return (1 - fx) * (1 - fy) * v00 + fx * (1 - fy) * v10 + (1 - fx) * fy * v01 + fx * fy * v11

@njit(parallel=True, fastmath=True)
def generating_final_S_using_NumbaLoopBiLinearInterpolator(Spot, Te, rd, rf, local_vol_surface_repaired, expiry_years_array, strikes_array, n_paths, n_steps, seed):
    """
    The entire Monte Carlo time-stepping engine.
    Generates random shocks internally using parallel threading.
    """
    # 1. Initialize random seed inside Numba (thread-safe setup)
    np.random.seed(seed)
    
    dt = Te / n_steps
    sqrt_dt = np.sqrt(dt)
    
    min_strike = strikes_array[0]
    max_strike = strikes_array[-1]
    
    # Initialize asset trajectories
    S = np.full(n_paths, Spot, dtype=np.float64)
    half_paths = n_paths // 2

    for step in range(n_steps):
        t = min(step * dt, expiry_years_array[-1])
        
        # 2. Generate Antithetic Shocks on-the-fly inside Numba
        # Allocate half the array size for random generation
        epsilon = np.random.standard_normal(half_paths)
        
        # Manually create the mirrored antithetic array to avoid Python overhead
        Z = np.empty(n_paths, dtype=np.float64)
        for p in prange(half_paths):
            Z[p] = epsilon[p]
            Z[p + half_paths] = -epsilon[p]
            
        # 3. Propagate all paths in parallel across CPU cores
        for p in prange(n_paths):
            current_S = S[p]
            clipped_S = max(min_strike, min(current_S, max_strike))
            
            # Fetch volatility from local vol surface
            sigma = bilinear_interp_2d(expiry_years_array, strikes_array, local_vol_surface_repaired, t, clipped_S)
            if sigma < 1e-5:
                sigma = 1e-5
                
            # Log-Euler update step
            S[p] = current_S * np.exp((rd - rf - 0.5 * sigma**2) * dt + sigma * sqrt_dt * Z[p])
            
    return S



#### pricing the Vanilla using different methods #######################
    # loop_interp_method :: "NumbaLoopBiLinearInterpolator", "RegularGridInterpolator"

#######################################################################################################################
def VanillaPriceGreeks_MC_Local_Vol(option_details_dict, mktdata_details_dict, local_vol_surface,expiry_years_array, strikes_array,loop_interp_method,n_paths=100_000,n_steps=252,seed=42):

    """
    European option pricing using Monte Carlo under local volatility.

    local_vol_surface shape:
        len(maturities) x len(strikes)

    maturities:
        grid of times in years, e.g. [0.25, 0.5, 1.0, 2.0]

    strikes:
        grid of spot/strike levels, e.g. [0.90, 1.00, 1.10, 1.20]

    local_vol_surface:
        Dupire local vol surface sigma_loc(T, S)
    """


    EvalDate = option_details_dict['Eval_Date']
    Currpair = option_details_dict['Currpair']
    Expiry = option_details_dict['Expiry']
    Strike = option_details_dict['Strike']
    CallPut = option_details_dict['CallPut']
    BuySell = option_details_dict['BuySell']
    Notional_For_Ccy = option_details_dict['Notional_For_Ccy']
    currpair_convention_days = 365

    if (BuySell == 'Sell'): 
        BuySell_multiplier = -1.0
    elif (BuySell == 'Buy'):
        BuySell_multiplier = 1.0
    
    Spot, Ft, Te, Td,rf, rd = mktdata_details_dict['Spot'], mktdata_details_dict['Ft'], mktdata_details_dict['Te'], mktdata_details_dict['Td'], mktdata_details_dict['rf'],mktdata_details_dict['rd']
    Ds, De, Dd, sigma_bs_implied, sigma_ATM = mktdata_details_dict['Ds'], mktdata_details_dict['De'], mktdata_details_dict['Dd'], mktdata_details_dict['sigma'], mktdata_details_dict['sigma_ATM']
    Spot = float(Spot)

    Te = Te / currpair_convention_days
    Td = Td / currpair_convention_days
    

    # filling the NaN values with good predicted data
    local_vol_surface_repaired = local_vol_surface_repair_func(local_vol_surface,expiry_years_array,strikes_array)

    # generating final S vector 
    if loop_interp_method == 'RegularGridInterpolator': # running this second time or more takes the same time

        S = generating_final_S_using_RegularGridInterpolator(Spot, Te, rd, rf, local_vol_surface_repaired,expiry_years_array,strikes_array,n_paths,n_steps,seed)

    elif loop_interp_method == 'NumbaLoopBiLinearInterpolator': # running this second time or more is much faster

        S = generating_final_S_using_NumbaLoopBiLinearInterpolator(Spot, Te, rd, rf, local_vol_surface_repaired, expiry_years_array, strikes_array, n_paths, n_steps, seed)

    if CallPut == "Call":
        payoff = np.maximum(S - Strike, 0.0)
    elif CallPut == "Put":
        payoff = np.maximum(Strike - S, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    price = np.exp(-rd * Td) * np.mean(payoff)
    #stderr = np.exp(-rd * Td) * np.std(payoff) / np.sqrt(n_paths)
    print (price)
    return price










######################################################################################################################################################################

# Price derived from spot move, delta, and vega, without re-interpolating the vol cube for each spot move iteration. This is a faster method to get an approximate price and delta for
#  small spot moves, but it may be less accurate for larger spot moves or when the vol surface is highly non-linear.
def VanillaPriceSimulated (option_details, linearmktdata_df, interp_obj_linearmktdata, volcube_interp_object_dict, interp_method = 'cubic', greeks = 'OnlyDelta'):
    pass

#########################################################################################################################################################################
