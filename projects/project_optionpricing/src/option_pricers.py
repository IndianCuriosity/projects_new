import pandas as pd
import numpy as np
from utils.optionpricing_functions import *
import os
from pathlib import Path
import pickle
import sys

base_dir = os.environ.get('PROJECTS_NEW_HOME')
sys.path.append(base_dir + '\\utils\\')
sys.path.append(base_dir + '\\configs\\')

if "utils.optionpricing_functions" in sys.modules:
    del sys.modules["utils.optionpricing_functions"]

from utils.optionpricing_functions import *

base_dir = os.environ.get('PROJECTS_NEW_HOME')
mktdata_dir = Path(base_dir + '\\data\\bbg_mktdata\\')



###############################################################################################################
########## Loading the
###############################################################################################################

currpair = 'EURUSD'
eval_date = '2026-01-06'

with open(mktdata_dir/'fx_pickled'/f'{currpair}_mktdata_dict.pkl', 'rb') as f:
    currpair_mktdata_dict = pickle.load(f)
currpair_mktdata_dict_pricing_date = currpair_mktdata_dict[eval_date]


### Linear Market Data
linearmktdata_df = currpair_mktdata_dict_pricing_date['linearmktdata_df']
linearmktdata_interp_object_dict = currpair_mktdata_dict_pricing_date['linearmktdata_interp_object_dict']

####################################################################################
################# Deal Details & creation of some objects ###################
####################################################################################

# Actually starts to price
option_details_dict = {'Eval_Date': eval_date, 'Currpair': currpair, 'Expiry': '2026-05-15', 'Strike': 1.19, 'CallPut': 'Call', 'BuySell': 'Buy', 'Notional_For_Ccy': 1000000.0}
eval_date = option_details_dict['Eval_Date']
expiry_list = [option_details_dict['Expiry']]


linearmktdata_time_axis_interp_method = 'linear'
volmktdata_time_axis_interp_method = 'linear'
smile_vol_model = 'svi_vol_model'
smile_vol_model = 'std_cubic_interp_vol_model'
price_greeks_concise_boolean = True

interp_data_df = linearmktdata_interp_expiry_list_func(eval_date, linearmktdata_df, linearmktdata_interp_object_dict, expiry_list = expiry_list, 
                                                       linearmktdata_time_axis_interp_method=linearmktdata_time_axis_interp_method)
Spot, Ft, rf, rd, Te, Td, De, Dd, Ds = interp_data_df.loc[option_details_dict['Expiry'],:]
mktdata_details_dict = {'Spot':Spot, 'Ft':Ft, 'rf':rf, 'rd':rd, 'Te':Te, 'Td':Td, 'De':De, 'Dd':Dd, 'Ds':Ds,'sigma': None, 'sigma_ATM': None}

####################################################################################
# Vanilla option pricer using Garman-Kohlhagen formula for FX options. 
####################################################################################

sigma, sigma_ATM = smile_vol_func(option_details_dict, mktdata_details_dict, currpair_mktdata_dict_pricing_date,smile_vol_model,volmktdata_time_axis_interp_method)

mktdata_details_dict['sigma'] = sigma
mktdata_details_dict['sigma_ATM'] = sigma_ATM

output = VanillaPriceGreeks_BS(option_details_dict, mktdata_details_dict,price_greeks_concise_boolean)
output.loc[['ATMVol_%','SmileVol_%','Premium_1stCcy_perc','Premium_2ndCcy_pips','Analytical_Delta_1stCcy_perc'],:]
print ('Premium_2ndCcy_pips',float(round(output.loc['Premium_2ndCcy_pips','Value'],6)))
####################################################################################
################# Pricing using Local volatility ###################
####################################################################################
loop_interp_method = "RegularGridInterpolator"
loop_interp_method =  "NumbaLoopBiLinearInterpolator"

n_paths=100000
n_steps=252
seed=42

local_vol_surface,expiry_years_array, strikes_array = currpair_mktdata_dict_pricing_date['local_vol_surface_expiry_strikes_arrays']
price = VanillaPriceGreeks_MC_Local_Vol(option_details_dict, mktdata_details_dict, local_vol_surface,expiry_years_array, strikes_array,loop_interp_method, n_paths,n_steps,seed)
print ('Premium_2ndCcy_pips',float(round(price,6)))


###############################################################################################################
# Digital option pricer using Garman-Kohlhagen formula for FX options. 
###############################################################################################################



###############################################################################################################
# One touch option pricer with Monte Carlo simulation.
###############################################################################################################





###############################################################################################################
# Knock-in, Knock-out option pricer with Monte Carlo simulation.
###############################################################################################################
