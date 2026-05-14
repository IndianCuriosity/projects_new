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
# Vanilla option pricer using Garman-Kohlhagen formula for FX options. The price is in domestic currency per unit of foreign currency.
###############################################################################################################

currpair = 'EURUSD'
with open(mktdata_dir/'fx_pickled'/f'{currpair}_mktdata_dict.pkl', 'rb') as f:
    currpair_mktdata_dict = pickle.load(f)

eval_date = '2026-01-02'
currpair_mktdata_dict_pricing_date = currpair_mktdata_dict[eval_date]

linearmktdata_df = currpair_mktdata_dict_pricing_date['linearmktdata_df']
linearmktdata_interp_object_dict = currpair_mktdata_dict_pricing_date['linearmktdata_interp_object_dict']
# volcube = currpair_mktdata_dict_pricing_date['volcube']
# volcube_interp_object_dict = currpair_mktdata_dict_pricing_date['volcube_interp_object_dict']
# svi_params_df = currpair_mktdata_dict_pricing_date['svi_params_df']
# volcube_implied_strikes = currpair_mktdata_dict_pricing_date['volcube_implied_strikes']


linearmktdata_time_axis_interp_method = 'linear'
price_greeks_concise_boolean = True

volmktdata_time_axis_interp_method = 'linear'
smile_vol_model = 'svi_vol_model' # 'svi_vol_model, 'std_cubic_interp_vol_model'
#smile_vol_model = 'std_cubic_interp_vol_model'

# vol_details_dict = {}
# if smile_vol_model == 'std_cubic_interp_vol_model':
#     vol_details_dict['volcube_interp_object_dict'] = volcube_interp_object_dict
#     vol_details_dict['volmktdata_time_axis_interp_method'] = volmktdata_time_axis_interp_method
# elif smile_vol_model == 'svi_vol_model':
#     vol_details_dict['volcube'] = volcube
#     vol_details_dict['svi_params_df'] = svi_params_df

option_details_dict = {'Eval_Date': eval_date, 'Currpair': currpair, 'Expiry': '2026-01-21', 'Strike': 1.1719, 'CallPut': 'Call', 'BuySell': 'Buy', 'Notional_For_Ccy': 1000000.0}

interp_data_df = linearmktdata_interp_expiry_list_func(option_details_dict['Eval_Date'], linearmktdata_df, linearmktdata_interp_object_dict, expiry_list = [option_details_dict['Expiry']], linearmktdata_time_axis_interp_method=linearmktdata_time_axis_interp_method)
Spot, Ft, rf, rd, Te, Td, De, Dd, Ds = interp_data_df.loc[option_details_dict['Expiry'],:]

mktdata_details_dict = {'Spot':Spot, 'Ft':Ft, 'rf':rf, 'rd':rd, 'Te':Te, 'Td':Td, 'De':De, 'Dd':Dd, 'Ds':Ds,'sigma': None, 'sigma_ATM': None}
sigma, sigma_ATM = smile_vol_func(option_details_dict, mktdata_details_dict, currpair_mktdata_dict_pricing_date,smile_vol_model,volmktdata_time_axis_interp_method)

mktdata_details_dict['sigma'] = sigma
mktdata_details_dict['sigma_ATM'] = sigma_ATM

output = VanillaPriceGreeks_BS(option_details_dict, mktdata_details_dict,price_greeks_concise_boolean)

output.loc[['ATMVol_%','SmileVol_%','Premium_1stCcy_perc','Analytical_Delta_1stCcy_perc'],:]
#mktdata_details_dict 

###############################################################################################################
# Digital option pricer using Garman-Kohlhagen formula for FX options. 
###############################################################################################################



###############################################################################################################
# One touch option pricer with Monte Carlo simulation.
###############################################################################################################





###############################################################################################################
# Knock-in, Knock-out option pricer with Monte Carlo simulation.
###############################################################################################################
