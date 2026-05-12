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
import datetime
from dates_functions import *
import scipy.stats as ss
from scipy.interpolate import CubicSpline
from scipy.interpolate import interp1d
import math


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



#######################################################################
## Creation of Linear Market Data DataFrame and Interpolation Objects #
#######################################################################

def linearmktdata_func(eval_date, spot_rate, yield_curr1, yield_curr2,currpair_static_info_dict,interp_obj_boolean = True, time_axis_interp_method = 'both'):

    interp_object_rate1, interp_object_rate2, interp_object_forward_rate = None, None, None
    linearmktdata_interp_object_dict = {}
    linearmktdata_interp_object_dict['cubic'] = {}
    linearmktdata_interp_object_dict['linear'] = {}

    daycount_curr1 = currpair_static_info_dict['daycount_ccy1']
    daycount_curr2 = currpair_static_info_dict['daycount_ccy2']
    spot_days = currpair_static_info_dict['spot_days']
    currpair_rate_convention = currpair_static_info_dict['currpair_rate_conventions']
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




#######################################################################
## Creation of Volatility Cube &  Interpolation Objects #
#######################################################################

def volcube_func(eval_date, volcube_t,linearmktdata_df, interp_obj_boolean = True, time_axis_interp_method = 'both'):
    atm_variancetime, interp_object_ten_delta, interp_object_ten_delta_call, interp_object_twentyfive_delta_put, interp_object_twentyfive_delta_call = None, None, None, None, None
    volcube_interp_object_dict = {}
    volcube_interp_object_dict['cubic'] = {}
    volcube_interp_object_dict['linear'] = {}
    volcube_interp_object_dict['tail_details'] = {}

    volcube = volcube_t.reset_index()
    volcube['Expiry_Date'] = volcube.apply(lambda x: (linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'expiry_date']).values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube['Expiry_Days'] = volcube.apply(lambda x: linearmktdata_df.loc[linearmktdata_df['tenors'] == x['index'], 'expiry_date_nb_days'].values[0] if x['index'] in linearmktdata_df['tenors'].values else np.nan, axis=1)
    volcube.set_index('index', inplace=True)
    volcube = volcube[['Expiry_Date', 'Expiry_Days','10P', '25P', 'ATM', '25C', '10C']]
    expiry_date_ON = next_bus_day_ref(eval_date, 1)
    volcube.loc['ON', 'Expiry_Date'] = expiry_date_ON
    volcube.loc['ON', 'Expiry_Days'] = calendar_days(eval_date, expiry_date_ON)
    volcube.index.name = 'Tenor'

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
 
    return volcube, volcube_interp_object_dict


#######################################################################
## Interpolation of Linear Market Data #
#######################################################################
def linearmktdata_interp_func(eval_date, linearmktdata_df, linearmktdata_interp_object_dict, expiry = None, time_axis_interp_method = 'cubic'):
  
    interp_obj_linearmktdata = linearmktdata_interp_object_dict['cubic'] if time_axis_interp_method == 'cubic' else linearmktdata_interp_object_dict['linear'] if time_axis_interp_method == 'linear' else None
    std_tenors = linearmktdata_df['tenors']
    std_expiry_dates = linearmktdata_df['expiry_date']
    
    if expiry in std_tenors.values:
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
    
    rf = interp_rate1 * 0.01
    rd = interp_rate2 * 0.01
    Ft = interp_forward_rate
    Te = expiry_date_nb_days
    Td = value_date_nb_days

    return rf, rd, Ft, Te, Td

#######################################################################
## Interpolation of Smile Vol #
#######################################################################

def vol_interp_func(Ft, Strike, Te, Td, volcube_interp_object_dict, time_axis_interp_method = 'cubic'):
    
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
        if time_axis_interp_method == 'cubic':
            interp_atm_variance = float(volcube_interp_object_dict['cubic']['atm_variance_time'](expirydate_nb_days))**0.5
            interp_atm_vol = math.sqrt(interp_atm_variance / expirydate_nb_days)
            interp_ten_delta_put_smilespread = float(volcube_interp_object_dict['cubic']['10P'](expirydate_nb_days))
            interp_twentyfive_delta_put_smilespread = float(volcube_interp_object_dict['cubic']['25P'](expirydate_nb_days))
            interp_twentyfive_delta_call_smilespread = float(volcube_interp_object_dict['cubic']['25C'](expirydate_nb_days))
            interp_ten_delta_call_smilespread = float(volcube_interp_object_dict['cubic']['10C'](expirydate_nb_days))
        elif time_axis_interp_method == 'linear':
            interp_atm_variance = float(volcube_interp_object_dict['linear']['atm_variance_time'](expirydate_nb_days))**0.5
            interp_atm_vol = math.sqrt(interp_atm_variance / expirydate_nb_days)
            interp_ten_delta_put_smilespread = float(volcube_interp_object_dict['linear']['10P'](expirydate_nb_days))
            interp_twentyfive_delta_put_smilespread = float(volcube_interp_object_dict['linear']['25P'](expirydate_nb_days))
            interp_twentyfive_delta_call_smilespread = float(volcube_interp_object_dict['linear']['25C'](expirydate_nb_days))
            interp_ten_delta_call_smilespread = float(volcube_interp_object_dict['linear']['10C'](expirydate_nb_days))
        else:
            raise ValueError("No interpolation objects found in volcube_interp_object_dict")
        
    interp_ten_delta_put_vol = interp_atm_vol + interp_ten_delta_put_smilespread
    interp_twentyfive_delta_put_vol = interp_atm_vol + interp_twentyfive_delta_put_smilespread
    interp_twentyfive_delta_call_vol = interp_atm_vol + interp_twentyfive_delta_call_smilespread
    interp_ten_delta_call_vol = interp_atm_vol + interp_ten_delta_call_smilespread
    
    smilecurve = [interp_ten_delta_put_vol, interp_twentyfive_delta_put_vol, interp_atm_vol, interp_twentyfive_delta_call_vol, interp_ten_delta_call_vol]
    #smilecurve[:] = [vol / 100.0 for vol in smilecurve]
    putdeltas = [.10, .25, .50, .75, .90]

    sigma = smilecurve[2]

    cubic_spline_surface = CubicSpline(putdeltas, smilecurve)

    delta_vol = 1.00

    while (delta_vol > 0.001):
        
        ''' Need to use greeks = PriceGreeksConcise '''
        analytical_delta = analytical_put_delta(Ft, Strike, Te, Td, rf, sigma)
        delta = abs(analytical_delta) # To make the put delta scale always +ve to match with the put delta list

        derivative = cubic_spline_surface(delta + 0.01) - cubic_spline_surface(delta)/(0.01)
        new_delta = float(delta + (1/derivative) * (0 - cubic_spline_surface(delta))) 
        
        new_vol = float(cubic_spline_surface(new_delta))
        delta_vol = abs(new_vol - sigma)
        
        sigma = new_vol
    
    return sigma


#######################################################################
## Calculation of Price & Greeks for Vanilla Options #
#######################################################################
# option_details = ['Currpair', 'Expiry', 'Strike', 'CallPut', 'BuySell', 'Notional_For_Ccy']

def VanillaPriceGreeks(option_details, linearmktdata_df, interp_obj_linearmktdata, volcube_interp_object_dict, interp_method = 'cubic', greeks = 'OnlyDelta'):
    
    
    PricingDate = option_details['PricingDate']
    Currpair = option_details['Currpair']
    Expiry = option_details['Expiry']
    Strike = option_details['Strike']
    CallPut = option_details['CallPut']
    BuySell = option_details['BuySell']
    Notional_For_Ccy = option_details['Notional_For_Ccy']
    
    Spot, Ft, rf, rd, Te, Td = linearmktdata_interp_func(linearmktdata_df, interp_obj_linearmktdata, expiry_date=Expiry, time_axis_interp_method=interp_method)
    sigma = vol_interp_func(Ft, Strike, Te, Td, volcube_interp_object_dict, time_axis_interp_method = interp_method)

    d1, d2 = d1d2(Ft, Strike, Te, sigma)
    
    if (CallPut == 'Call'):
        value = math.exp(-rd * Td) * (Ft * N(d1) - Strike * N(d2))
        analytical_delta = math.exp(-rf * Td) * N(d1)
        analytical_rho_d = Strike * Td * math.exp(-rd * Td) * N(d2)
        analytical_rho_f = -Spot * Td * math.exp(-rf * Td) * N(d1)
        analytical_theta = (1/365) * (Spot * math.exp(-rf * Td) * dN(d1) * sigma / (2 * math.sqrt(Te)) - rd * Strike * math.exp(-rf * Td) * N(d2) + rf * Spot * math.exp(-rf * Td) * N(d1))

                
    if (CallPut == 'Put'):
        value = math.exp(-rd * Td) * (Strike * N(-d2) - Ft * N(-d1))
        analytical_delta = - math.exp(-rf * Td) * (1 - N(d1)) 
        analytical_rho_d = -Strike * Td * math.exp(-rd * Td) * N(-d2)
        analytical_rho_f = Spot * Td * math.exp(-rf * Td) * N(-d1)
        analytical_theta = (1/365) * (Spot * math.exp(-rf * Td) * dN(d1) * sigma / (2 * math.sqrt(Te)) + rd * Strike * math.exp(-rf * Td) * N(-d2) - rf * Spot * math.exp(-rf * Td) * N(-d1))
    
    ''' Common Analytical Greeks Calculations for Calls & Puts '''
    
    analytical_gamma = math.exp(-rf * Td) * dN(d1) / (Spot * sigma * math.sqrt(Te))
    analytical_vega = math.exp(-rf * Td) * Spot * math.sqrt(Te) * dN(d1) 
    
    analytical_vanna = math.exp(-rf * Td) * dN(d1) * d2 / sigma
    analytical_volga = math.exp(-rf * Td) * Spot * math.sqrt(Te) * dN(d1) * d1 * d2 / sigma
    
    if (BuySell == 'Sell'): 
        BuySell_multiplier = -1.0
    elif (BuySell == 'Buy'):
        BuySell_multiplier = 1.0
    
    
    ### for USDINR, USD is foreign currency and INR is the domestic currency
    ### for EURUSD, EUR is the foreign currency and USD is the domestic currency
    
    Notional_Dom_Ccy = Notional_For_Ccy * Strike
    
    premium_dom_pips = BuySell_multiplier * value                   
    premium_dom_perc = 100 * premium_dom_pips / Strike
    premium_for_perc = 100 * premium_dom_pips / Spot
    premium_for_pips = (premium_dom_pips / Spot) / Strike
    
    premium_dom_amount = 0.01 * premium_dom_perc * Notional_Dom_Ccy
    premium_for_amount =  0.01 * premium_for_perc * Notional_For_Ccy
#        
#        analytical_delta_dom_perc = analytical_delta
#        analytical_delta_for_perc = analytical_delta_dom_perc * (Strike / Spot)
#        analytical_delta_dom_amount = analytical_delta_dom_perc * Notional_Dom_Ccy
#        analytical_delta_for_amount = analytical_delta_for_perc * Notional_For_Ccy
#        
    analytical_delta_for_perc = BuySell_multiplier * analytical_delta * 100                    
    analytical_delta_dom_perc = 0.01 * analytical_delta_for_perc * (Spot / Strike) * 100
    analytical_delta_dom_amount = 0.01 *analytical_delta_dom_perc * Notional_Dom_Ccy
    analytical_delta_for_amount = 0.01 * analytical_delta_for_perc * Notional_For_Ccy
    
    analytical_gamma_1Notionalforeign_1percSpot = BuySell_multiplier * analytical_gamma * 0.01 * Spot         
    analytical_gamma_for_amount = analytical_gamma_1Notionalforeign_1percSpot * Notional_For_Ccy
    
    # earlier it was wrong, BS gives vega in domestic ccy, not in foreign currency
    #analytical_vega_1Notionalforeign_1percVol = analytical_vega * 0.0001
    analytical_vega_1Notionaldomestic_1percVol = BuySell_multiplier * analytical_vega * 0.01                
    analytical_vega_1Notionalforeign_1percVol = analytical_vega_1Notionaldomestic_1percVol / Spot
    
    analytical_vega_for_amount = analytical_vega_1Notionalforeign_1percVol * Notional_For_Ccy
    
    analytical_theta_for_amount = - BuySell_multiplier * analytical_theta * Notional_For_Ccy  / Spot        
    
    
    ''' Outputs in a dataframe '''
        
    output = pd.DataFrame(columns = ['Value'])
    
    output.loc['ContractDetails_#################'] = ''
    
    output.loc['CcyPair'] = Currpair
    output.loc['BuySell'] = BuySell
    output.loc['Horizon Date'] = PricingDate
    output.loc['Spot Date'] = spot_date
    output.loc['CallPut'] = CallPut
    output.loc['Maturity'] = ExpiryDate
    output.loc['Expiry Date'] = expiry_date
    output.loc['Delivery Date'] = delivery_date
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
    
    
    
    if (greeks == 'PriceGreeksConcise'):
        
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
        
    if (greeks == 'PriceGreeksDetails'):
        
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


# Price derived from spot move, delta, and vega, without re-interpolating the vol cube for each spot move iteration. This is a faster method to get an approximate price and delta for
#  small spot moves, but it may be less accurate for larger spot moves or when the vol surface is highly non-linear.
def VanillaPriceSimulated (option_details, linearmktdata_df, interp_obj_linearmktdata, volcube_interp_object_dict, interp_method = 'cubic', greeks = 'OnlyDelta'):
    pass

def