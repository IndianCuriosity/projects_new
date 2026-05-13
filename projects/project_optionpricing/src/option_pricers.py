import pandas as pd
import numpy as np
from utils.optionpricing_functions import *
import os
from pathlib import Path
import pickle

base_dir = os.environ.get('PROJECTS_NEW_HOME')
mktdata_dir = Path(base_dir + '\\data\\bbg_mktdata\\')

###############################################################################################################
# Vanilla option pricer using Garman-Kohlhagen formula for FX options. The price is in domestic currency per unit of foreign currency.
###############################################################################################################

currpair = 'EURUSD'
with open(mktdata_dir/'fx_pickled'/f'{currpair}_mktdata_dict.pkl', 'rb') as f:
    currpair_mktdata_dict = pickle.load(f)

pricing_date = '2026-01-02'
currpair_mktdata_dict_pricing_date = currpair_mktdata_dict[pricing_date]

linearmktdata_df = currpair_mktdata_dict_pricing_date['linearmktdata_df']
linearmktdata_interp_object_dict = currpair_mktdata_dict_pricing_date['linearmktdata_interp_object_dict']
volcube_interp_object_dict = currpair_mktdata_dict_pricing_date['volcube_interp_object_dict']

time_axis_interp_method = 'cubic'
price_greeks_concise_boolean = True

option_details = {'PricingDate': pricing_date, 'Currpair': currpair, 'Expiry': '2026-01-21', 'Strike': 1.17, 'CallPut': 'Call', 'BuySell': 'Buy', 'Notional_For_Ccy': 1000000.0}

output = VanillaPriceGreeks(option_details, linearmktdata_df, linearmktdata_interp_object_dict, volcube_interp_object_dict, time_axis_interp_method = time_axis_interp_method, price_greeks_concise_boolean = price_greeks_concise_boolean)



###############################################################################################################
# Digital option pricer using Garman-Kohlhagen formula for FX options. 
###############################################################################################################



###############################################################################################################
# One touch option pricer with Monte Carlo simulation.
###############################################################################################################





###############################################################################################################
# Knock-in, Knock-out option pricer with Monte Carlo simulation.
###############################################################################################################
