import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pandas.tseries.offsets import BDay

import pandas as pd
from datetime import datetime
from pandas.tseries.offsets import CustomBusinessDay
from dateutil.relativedelta import relativedelta


# Calculate the previous business day from today's date

def prev_bus_day(number_of_business_days):
    
    today = pd.datetime.today()
    prev_bus_day = today - BDay(number_of_business_days)
    prev_bus_day = prev_bus_day.strftime('%Y-%m-%d')
    
    return prev_bus_day

def next_bus_day(number_of_business_days):
    
    today = pd.datetime.today()
    next_bus_day = today + BDay(number_of_business_days)
    next_bus_day = next_bus_day.strftime('%Y-%m-%d')
    
    return next_bus_day

def prev_bus_day_ref(refdate, number_of_business_days):
    
    # to convert to datetime object : strptime
    refdate = datetime.strptime(refdate,'%Y-%m-%d')
    prev_bus_day = refdate - BDay(number_of_business_days)
    # to convert back to string object :: strftime
    prev_bus_day = prev_bus_day.strftime('%Y-%m-%d')
    
    return prev_bus_day

def next_bus_day_ref(refdate, number_of_business_days):
    
    refdate = datetime.strptime(refdate,'%Y-%m-%d')
    next_bus_day = refdate + BDay(number_of_business_days)
    next_bus_day = next_bus_day.strftime('%Y-%m-%d')
    
    return next_bus_day

def next_calendar_day_ref(refdate, number_of_calendar_days):
    
    refdate = datetime.strptime(refdate,'%Y-%m-%d')
    next_calendar_day = refdate + timedelta(days = number_of_calendar_days)
    next_calendar_day = next_calendar_day.strftime('%Y-%m-%d')
    
    return next_calendar_day


def business_days(refdate1, refdate2):
    # refdate1 should always be greater or equal to refdate2
    refdate1 = datetime.strptime(refdate1,'%Y-%m-%d')
    refdate2 = datetime.strptime(refdate2,'%Y-%m-%d')
    if (refdate1 >= refdate2):
        return 0
    else:
        count = 0
        while (refdate1 < refdate2):     
            refdate1 = refdate1 + BDay(1)
            count = count + 1
        return count

def calendar_days(refdate1, refdate2):
    # refdate1 should always be less or equal to refdate2
    refdate1 = datetime.strptime(refdate1,'%Y-%m-%d')
    refdate2 = datetime.strptime(refdate2,'%Y-%m-%d')
    
    if (refdate1 >= refdate2):
        return 0
    else:
        count = 0
        while (refdate1 < refdate2):     
            refdate1 = refdate1 + timedelta(days = 1)
            count = count + 1
        return count

        
def business_dates_between_two_dates(refdate1, refdate2):
    
    dates_list = []
    dates_list.append(refdate1)
    refdate = refdate1
    while (refdate < refdate2):
        refdate = next_bus_day_ref(refdate, 1)
        dates_list.append(refdate)
    
    return dates_list

def business_dates_for_x_business_days(refdate, number_of_business_days):
    
    
    dates_list = []
    dates_list.append(refdate)
    count = 1
    while (refdate):
        refdate = next_bus_day_ref(refdate, 1)
        dates_list.append(refdate)
        count = count + 1
        if count >= number_of_business_days:
            break
        
    return dates_list


def business_dates_from_YYYY_MM_DD_to_YYYYMMDD(dates_in_list):
    
    dates_out_list = []
    for horizon_date in dates_in_list:
        refdate = datetime.strptime(horizon_date,'%Y-%m-%d')
        refdate = refdate.strftime('%Y%m%d')
        dates_out_list.append(refdate)
    
    return dates_out_list

def business_dates_from_MMDDYYYY_to_YYYY_MM_DD(dates_in_list):
    
    dates_out_list = []
    for horizon_date in dates_in_list:
        refdate = datetime.strptime(horizon_date,'%m%d%Y')
        refdate = refdate.strftime('%Y-%m-%d')
        dates_out_list.append(refdate)
    
    return dates_out_list

def bucketed_tenor(refdate1, refdate2):
    
    #refdate1 = datetime.strptime(refdate1,'%Y-%m-%d')
    #refdate2 = datetime.strptime(refdate2,'%Y-%m-%d')
    nb_of_busdays = business_days(refdate1, refdate2)
    
    config_filepath = config['paths']['config_filepath']
    config_filename = config['filenames']['SwapFactors']
    sheetname = 'TenorsBusinessDays'
    tenorsbusinessdaysdata = pd.read_excel(config_filepath + config_filename, sheet_name = sheetname)
    
    # drop 2w for now, temporary
    tenorsbusinessdaysdata = (tenorsbusinessdaysdata.drop([1])).reset_index(drop = True)
    
    bkted_tenor = None
    
    if (nb_of_busdays > 0):
            
        for tenor_num, tenor in enumerate((tenorsbusinessdaysdata['StdTenors']).head(-1)):
            tenor_days = tenorsbusinessdaysdata.loc[tenor_num,'BusinessDays']
            next_tenor_days = tenorsbusinessdaysdata.loc[(tenor_num + 1),'BusinessDays']
            
            # temp one commented for now, use 2w later
            '''
            if ((nb_of_busdays <= tenor_days) and (tenor == '1W')):
                bkted_tenor = tenor
                break
            elif ((nb_of_busdays <= tenor_days) and (tenor == '2W')):
                bkted_tenor = tenor
                break
            elif ((nb_of_busdays <= 0.5 * (tenor_days + next_tenor_days))):
                bkted_tenor = tenor
                break
            '''
            if ((nb_of_busdays <=  0.5 * (tenor_days + next_tenor_days)) and (tenor == '1W')):
                bkted_tenor = tenor
                break
            elif ((nb_of_busdays <= 0.5 * (tenor_days + next_tenor_days))):
                bkted_tenor = tenor
                break
            
    return bkted_tenor


def bucketed_tenor_cdr_days(refdate1, refdate2):
    
    #refdate1 = datetime.strptime(refdate1,'%Y-%m-%d')
    #refdate2 = datetime.strptime(refdate2,'%Y-%m-%d')
    nb_of_cdrdays = calendar_days(refdate1, refdate2) + 1
    
    config_filepath = config['paths']['config_filepath']
    config_filename = config['filenames']['SwapFactors']
    sheetname = 'TenorsCalendarDays'
    tenorscalendardaysdata = pd.read_excel(config_filepath + config_filename, sheet_name = sheetname)
    
    # drop 2w for now, temporary
    #tenorscalendardaysdata = (tenorscalendardaysdata.drop([1])).reset_index(drop = True)
    
    bkted_tenor = None
    
    if (nb_of_cdrdays > 0):
            
        for tenor_num, tenor in enumerate((tenorscalendardaysdata['StdTenors']).head(-1)):
            tenor_days = tenorscalendardaysdata.loc[tenor_num,'CalendarDays']
            next_tenor_days = tenorscalendardaysdata.loc[(tenor_num + 1),'CalendarDays']
            
            #print (tenor_num, tenor, tenor_days, next_tenor_days)
            # temp one commented for now, use 2w later
            '''
            if ((nb_of_busdays <= tenor_days) and (tenor == '1W')):
                bkted_tenor = tenor
                break
            elif ((nb_of_busdays <= tenor_days) and (tenor == '2W')):
                bkted_tenor = tenor
                break
            elif ((nb_of_busdays <= 0.5 * (tenor_days + next_tenor_days))):
                bkted_tenor = tenor
                break
            '''
            
            if (tenor == 'SN'):
                if (nb_of_cdrdays <= tenor_days):
                    bkted_tenor = tenor
                    #print ('first if', bkted_tenor)
                    break
                else:
                    continue
            
            
            if (tenor == '1W'):    
                if (nb_of_cdrdays <= tenor_days):
                    bkted_tenor = tenor
                    #print ('2nd if', bkted_tenor)
                    break
                else:
                    continue
                
            if (((nb_of_cdrdays <= tenor_days) or (nb_of_cdrdays <=  0.5 * (tenor_days + next_tenor_days))) and (tenor == '2W')):
                bkted_tenor = tenor
                #print ('3rd if', bkted_tenor)
                break
            elif ((nb_of_cdrdays <= 0.5 * (tenor_days + next_tenor_days))):
                bkted_tenor = tenor
                #print ('4th if', bkted_tenor)
                break
            
    return bkted_tenor


def bucketed_tenor_cdr_days_based_on_tenors(refdate1, refdate2, tenors):
    
    nb_of_cdrdays = calendar_days(refdate1, refdate2) + 1
    
    config_filepath = config['paths']['config_filepath']
    config_filename = config['filenames']['SwapFactors']
    sheetname = 'TenorsCalendarDays'
    tenorscalendardaysdata = pd.read_excel(config_filepath + config_filename, sheet_name = sheetname)
    
    tenorscalendardaysdata = tenorscalendardaysdata[(tenorscalendardaysdata['StdTenors'].isin(tenors))]
    tenorscalendardaysdata = tenorscalendardaysdata.reset_index(drop = True)
    
    first_tenor = list(tenorscalendardaysdata['StdTenors'])[0]
    last_tenor = list(tenorscalendardaysdata['StdTenors'])[-1]
    
    bkted_tenor = None
    
    if (nb_of_cdrdays > 0):
            
        for tenor_num, tenor in enumerate(tenorscalendardaysdata['StdTenors']):
            tenor_days = tenorscalendardaysdata.loc[tenor_num,'CalendarDays']
            
            if (tenor != last_tenor):    
                next_tenor_days = tenorscalendardaysdata.loc[(tenor_num + 1),'CalendarDays']
            
            
            if (tenor == first_tenor):
                if (nb_of_cdrdays <= tenor_days):
                    bkted_tenor = tenor
                    #print ('first if', bkted_tenor)
                    break
                else:
                    continue
            
            if (nb_of_cdrdays <=  0.5 * (tenor_days + next_tenor_days)):
                bkted_tenor = tenor
                #print ('2nd if', bkted_tenor)
                break
            
            
            if (tenor == last_tenor):    
                if (nb_of_cdrdays >= tenor_days):
                    bkted_tenor = tenor
                    #print ('3rd if', bkted_tenor)
                    break
                else:
                    continue
                
            
            
    return bkted_tenor



    
def business_dates(calendar, filepath, filename):
    
    ccys = [['US', 'USD'], ['CA', 'CAD'], ['EU', 'EUR'], ['JN', 'JPY'], ['SZ','CHF'],
                  ['GB', 'GBP'], ['AU', 'AUD'], ['NZ', 'NZD'], ['IN', 'IND'], ['CH','CNY'],
                  ['SK', 'KRW'], ['TA', 'TWD'], ['SI', 'SGD'], ['MA', 'MYR'], ['ID','IDR'],
                  ['PH', 'PHP'], ['TH', 'THB'], ['HK', 'HKD']]
    
    ccys_keys = [ccys[i][0] for i,value in enumerate(ccys)]
    ccys_values = [ccys[i][1] for i,value in enumerate(ccys)]
    
    
    non_business_dates_all = pd.read_excel(filepath + filename)
    
    


def cdr_weekends(refdate, number_of_days):
    cdr = []
    #print (refdate)
    for i in list(range(0, number_of_days)):
        
        refdate = datetime.strptime(refdate,'%Y-%m-%d')
        
        weekno = refdate.weekday()
        
        if (weekno == 5 or weekno == 6):
            cdr.append(refdate.strftime('%Y-%m-%d'))
        
        refdate = refdate + relativedelta(days = 1)
        refdate = refdate.strftime('%Y-%m-%d')
    return cdr

    
        

def bus_day_ref_shifter_with_calendar(refdate, number_of_business_days, calendar_ctry1, calendar_ctry2, shifter):
    
    data_filepath_calendar = config['paths']['data_filepath_calendar'] + config['paths_sub']['bbgcalendar']
        
    filename_calendar = config['filenames']['Calendar']
    calendar_table = pd.read_csv(data_filepath_calendar + filename_calendar, index_col = 0)
        
    # Specific calendar 
    calendar_country1 = calendar_table[calendar_ctry1].tolist()
    calendar_country2 = calendar_table[calendar_ctry2].tolist()
    
    calendar_country = calendar_country1 + calendar_country2
    
    calendar_country = [x for x in calendar_country if str(x) != 'nan']
    calendar_country = list(set(calendar_country))
    
    cdr_satsun  = cdr_weekends(refdate, 3650)
    
    refdate = datetime.strptime(refdate,'%Y-%m-%d')

    # formatting the calendar dates if the data format is different
    # check the notepad ++ of the calendar data
    
    '''
    
    calendar_country_formatted = []
    for hol_date in calendar_country:
    
        hol_date_formatted = datetime.strptime(hol_date,'%m/%d/%Y')
        hol_date_formatted = hol_date_formatted.strftime('%Y-%m-%d')
        calendar_country_formatted.append(hol_date_formatted)    
    '''
    # when formatting is not needed
    
    calendar_country_formatted = calendar_country
    
    calendar_country_formatted = calendar_country_formatted + cdr_satsun
    
    OneCustomBD = CustomBusinessDay(holidays = calendar_country_formatted)
    
    nextprevbusday = refdate
    
    for k in list(range(0, number_of_business_days)):
        if (shifter == 'forward'):
            nextprevbusday = nextprevbusday + OneCustomBD
        elif( shifter == 'backward'):
            nextprevbusday = nextprevbusday - OneCustomBD
        
        
    nextprevbusday = nextprevbusday.strftime('%Y-%m-%d')

    return nextprevbusday





def tenor_ref_shifter_with_calendar(refdate, tenor, calendar_ctry1, calendar_ctry2):
    
    
    data_filepath_calendar = config['paths']['data_filepath_calendar'] + config['paths_sub']['bbgcalendar']
        
    filename_calendar = config['filenames']['Calendar']
    calendar_table = pd.read_csv(data_filepath_calendar + filename_calendar, index_col = 0)
        
    # Specific calendar 
    calendar_country1 = calendar_table[calendar_ctry1].tolist()
    calendar_country2 = calendar_table[calendar_ctry2].tolist()
    
    calendar_country = calendar_country1 + calendar_country2
    
    calendar_country = [x for x in calendar_country if str(x) != 'nan']
    calendar_country = list(set(calendar_country))
    
    
    # Adding weekends to the specific calendar
    cdr_satsun  = cdr_weekends(refdate, 3650)
    
    refdate = datetime.strptime(refdate,'%Y-%m-%d')
    
    
    # formatting the calendar dates if the data format is different
    # check the notepad ++ of the calendar data
    
    '''
    
    calendar_country_formatted = []
    for hol_date in calendar_country:
    
        hol_date_formatted = datetime.strptime(hol_date,'%m/%d/%Y')
        hol_date_formatted = hol_date_formatted.strftime('%Y-%m-%d')
        calendar_country_formatted.append(hol_date_formatted)    
    '''
    # when formatting is not needed
    
    calendar_country_formatted = calendar_country
    
    calendar_country_formatted = calendar_country_formatted + cdr_satsun
    
    # building calendar custom calendar
    OneCustomBD = CustomBusinessDay(holidays = calendar_country_formatted)
    
    # actual tenor date depending on the input, 7BD, 3M, 2Y
    if ('Y' in tenor):
        num_years = int(tenor.replace('Y',""))
        tenordate = refdate + relativedelta(years = num_years)
    elif ('M' in tenor):
        num_months = int(tenor.replace('M',""))
        tenordate = refdate + relativedelta(months = num_months)
    elif ('W' in tenor):
        num_weeks = int(tenor.replace('W',""))
        tenordate = refdate + relativedelta(weeks = num_weeks)    
    elif ('D' in tenor):
        num_days = int(tenor.replace('D',""))
        tenordate = refdate + relativedelta(days = num_days)
    
    tenordate = tenordate.strftime('%Y-%m-%d')
    
    # making sure that the tenor date falls on the business date.
    
    if (tenordate in calendar_country_formatted):
        tenordate = datetime.strptime(tenordate, '%Y-%m-%d')
        tenordate = tenordate + OneCustomBD
        tenordate = tenordate.strftime('%Y-%m-%d')
        
    
    return tenordate
        
        
    
    
def settle_dates_list(pricing_date, currpair, tenors):
    
    # if we directly get from settle_dates values from bloomberg or else calculate
    
    config_filepath = config['paths']['config_filepath']
    config_filename = config['filenames']['SwapFactors']
    spotdaystable = pd.read_excel(config_filepath + config_filename, sheet_name = 'BBGSpotConventions')
    spotdays = int(spotdaystable.loc[spotdaystable['CurrPairs'] == currpair, 'SpotDays'])
        
    
    
    try:
        data_filepath_settledays = config['paths']['data_filepath_fx'] + config['paths_sub']['settledates_future']    
        filename = currpair + '_settledates.csv'
        
        settledays_table = pd.read_csv(data_filepath_settledays + filename, index_col = 0)
        settledays_table = (settledays_table.loc[pricing_date]).reset_index()
        
        settledays_table['Tenor'] =  settledays_table['index']
        settledays_table['cdr_days'] = settledays_table[pricing_date] 
        del settledays_table['index']
        del settledays_table[pricing_date]
        settledays_table = settledays_table.set_index('Tenor')
        settledays_table['deliv_date'] = [next_calendar_day_ref(pricing_date, cdr_days) for cdr_days in settledays_table['cdr_days']]
        
        settledays_table_tenors = list(settledays_table.index)
        common_tenors = list(set(settledays_table_tenors) & set(tenors))
        uncommon_tenors = list(set(tenors) - set(common_tenors))
        
        # only when settle dates files dont have some tenors
        if (uncommon_tenors != []):
            settledays_table = settledays_table.reindex(settledays_table.index.union(uncommon_tenors), axis=0)
            
            for uncommon_tenor in uncommon_tenors:
                if (uncommon_tenor == 'SPOT'):
                    settledays_table.loc['SPOT', 'deliv_date'] = bus_day_ref_shifter_with_calendar(pricing_date, spotdays, currpair[0:3], currpair[3:6], 'forward')
                    spot_date = settledays_table.loc['SPOT', 'deliv_date']
                    settledays_table.loc['SPOT', 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc['SPOT', 'deliv_date'])
                elif (uncommon_tenor == 'SN'):
                    spot_date = settledays_table.loc['SPOT', 'deliv_date']
                    settledays_table.loc['SN', 'deliv_date'] = bus_day_ref_shifter_with_calendar(spot_date, 1, currpair[0:3], currpair[3:6], 'forward')
                    settledays_table.loc['SN', 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc['SN', 'deliv_date'])
                elif (uncommon_tenor == 'ON'):
                    spot_date = settledays_table.loc['SPOT', 'deliv_date']
                    settledays_table.loc['ON', 'deliv_date'] = bus_day_ref_shifter_with_calendar(spot_date, 1, currpair[0:3], currpair[3:6], 'forward')
                    settledays_table.loc['ON', 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc['ON', 'deliv_date'])
                else:
                    spot_date = settledays_table.loc['SPOT', 'deliv_date']
                    settledays_table.loc[uncommon_tenor, 'deliv_date'] = tenor_ref_shifter_with_calendar(spot_date, uncommon_tenor, currpair[0:3], currpair[3:6])
                    settledays_table.loc[uncommon_tenor, 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc[uncommon_tenor, 'deliv_date'])
        
        settledays_table = settledays_table.reindex(tenors)
        
        print ("try")
    # only when the pricing_date is not there in settledate file
    except:
        
        print ("except")
        settledays_table = pd.DataFrame(index = tenors,columns = ['cdr_days', 'deliv_date', 'fixing_date','cdr_days_fixing'])
        settledays_table.loc['SPOT', 'deliv_date'] = bus_day_ref_shifter_with_calendar(pricing_date, spotdays, currpair[0:3], currpair[3:6], 'forward')
        spot_date = settledays_table.loc['SPOT', 'deliv_date']
        settledays_table.loc['SPOT', 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc['SPOT', 'deliv_date'])
        
        settledays_table.loc['SN', 'deliv_date'] = bus_day_ref_shifter_with_calendar(spot_date, 1, currpair[0:3], currpair[3:6], 'forward')
        #spotnext_date = settledays_table.loc['SN', 'deliv_date']
        settledays_table.loc['SN', 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc['SN', 'deliv_date'])
        
        settledays_table.loc['ON', 'deliv_date'] = bus_day_ref_shifter_with_calendar(spot_date, 1, currpair[0:3], currpair[3:6], 'forward')
        #spotnext_date = settledays_table.loc['SN', 'deliv_date']
        settledays_table.loc['ON', 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc['ON', 'deliv_date'])
        
        
        #tenors_exclspot = tenors[1:]
        tenors_exclspot_spotnext = copy.deepcopy(tenors)
        
        if ('SPOT' in tenors):    
            tenors_exclspot_spotnext.remove('SPOT')
        
        if ('SN' in tenors):    
            tenors_exclspot_spotnext.remove('SN')
        
        
        for tenor in tenors_exclspot_spotnext:
            settledays_table.loc[tenor, 'deliv_date'] = tenor_ref_shifter_with_calendar(spot_date, tenor, currpair[0:3], currpair[3:6])
            settledays_table.loc[tenor, 'cdr_days'] = calendar_days(pricing_date, settledays_table.loc[tenor, 'deliv_date'])
        
    finally:
        #print (settledays_table)
        
        settledays_table['fixing_date'] = [bus_day_ref_shifter_with_calendar(deliv_date, spotdays, currpair[0:3], currpair[3:6], 'backward') for deliv_date in settledays_table['deliv_date']]
        for tenor in tenors:
            settledays_table.loc[tenor, 'cdr_days_fixing'] = calendar_days(pricing_date, settledays_table.loc[tenor, 'fixing_date'])
        
        # specifically for spot and SN days
        settledays_table.loc['SPOT','fixing_date'] =  pricing_date
        spot_date = settledays_table.loc['SPOT','fixing_date']
        
        settledays_table.loc['SN','fixing_date'] =  bus_day_ref_shifter_with_calendar(spot_date, 1, currpair[0:3], currpair[3:6], 'forward')
        settledays_table.loc['SPOT', 'cdr_days_fixing'] = calendar_days(pricing_date, settledays_table.loc['SPOT', 'fixing_date'])
        settledays_table.loc['SN', 'cdr_days_fixing'] = calendar_days(pricing_date, settledays_table.loc['SN', 'fixing_date'])
        
        settledays_table = settledays_table.reindex(tenors)
        
    return settledays_table
