# -*- coding: utf-8 -*-
# Script published by Hochschule Mannheim - Mannheim University of Applied Sciences - Germany: https://www.hs-mannheim.de/
"""
A module that contains auxillary functions that support the processing of the 
read in input data for the calculation. 

Methods
-------
add_row :
    Check and adapt given case of flexibility measure and append reformatted
    row to data frame.
check_and_adapt_dsm : 
    The given case of a flexibility measure is checked for plausibility and 
    adapted, if required.
fillna_dict : 
    Replace 'NaN' values in a dictionary with 0.

@author: Nadine Gabrek
"""
import pandas as pd 
from math import isnan

def add_row(row:pd.Series,df:pd.DataFrame,scope:str,maximization:str,
            load_change:str)-> pd.DataFrame :
    
    """Check and adapt given case of flexibility measure and append reformatted
    row to data frame.  
    
    This method checks the given specific case of an energy flexibility measure
    and adapts it, if required. The row is reformatted, such that it only contains
    relevant data for the further calculation, and is appended to a new data frame.
    
    Parameters
    ----------
    row : pandas.Series
        The data of a flexibility measure. 
    df : pandas.DataFrame
        New data frame to which the adapted and reformatted case of the 
        flexibility measure is append to. 
    scope : str
        Can take the values 'potential' or 'perspective' to select the specific 
        case of the flexibility measure.
    maximization : str
        Can take the values 'power' or 'retrieval duration' to select the 
        specific case of the flexibility measure. 
    load_change : str
        Can take the values 'load increase' or 'load reduction' to select the 
        specific case of the flexibility measure. 
        
    Returns
    -------
    pandas.DataFrame
        Updated data frame with the defined specific case of the flexibility
        measure. 
    
    """
    #check if the values of string inputs are valid
    valid_scope = {'potential','perspective'}
    valid_maximization = {'power','retrieval duration'}
    valid_load_change = {'load increase','load reduction'}
    if (scope not in valid_scope) or (maximization not in valid_maximization) or (load_change not in valid_load_change):
        raise ValueError('add_row: scope, maximization, or load change is not valid.')
    
    #define variables to access required case of the flexibility measure from row
    scope_row = 'Potential' if scope == 'potential' else 'Perspektive'
    max_row = 'maxLeistung' if maximization =='power' else 'maxAbrufdauer'
    load_change_row = 'LE' if load_change == 'load increase' else 'LV'
     
    #create new row
    new_row = {'TP':row['TP'], 'name':row['Name'], 'scope':scope, 'maximization':maximization, 
               'load change':load_change, 'power':float(row[f'{scope_row}_{max_row}_{load_change_row}_Leistung [kW]']), 
               'retrieval duration':float(row[f'{scope_row}_{max_row}_{load_change_row}_Abrufdauer [h]']),
               'activation duration':float(row[f'{scope_row}_{max_row}_{load_change_row}_Aktivierungsdauer [s]'])/3600,
               'catch-up time':float(row[f'{scope_row}_{max_row}_{load_change_row}_Nachholzeit [h]']), 
               'retrieval frequency':int(row[f'{scope_row}_{max_row}_{load_change_row}_Abrufhäufigkeit [1/a]'])}
    
    #check case of flexibility measure and adapt if required
    checked_row = check_and_adapt_dsm(new_row)
    
    #add new row to data frame 
    df.loc[len(df)] = checked_row
    
    #return updated data frame 
    return df

def check_and_adapt_dsm(row:dict) -> dict :
    
    """The given case of a flexibility measure is checked for plausibility and 
    adapted, if required.
    
    The duration of one retrieval cycle, consisting of the activation duration, 
    retrieval duration and catch-up time, is checked and potentially adapted
    to fit the quater-hourly resolution of the times series of electricity prices
    and emission factors (emf). Changes in the durations require the adaption 
    of the flexible power and retrieval frequency.
    
    Parameters
    ----------
    row : dict
        The data of a specific case of a flexibility measure.
        
    Returns
    -------
    dict
        The checked and potentially adapted data of the case of the flexibility
        measure. 
    """
    
    #replace NaN values with 0, to enable adaptations  
    row = fillna_dict(row)
     
    #store relevant values in variables
    rd = row['retrieval duration']
    ct = row['catch-up time']
    ad = row['activation duration']
    power = row['power']
    rf = row['retrieval frequency']
    duration = rd + ct + ad
    
    #first check: the overall duration of a retrieval cycle should be over a 
    #quarter of an hour to match the time series of prices and emf
    if duration <= 0.25:
        #if the duration is under a quarter of an hour, the retrieval duration 
        #is set to 0.25 and the catch-up time and active duration to 0
        rd = 0.25
        ct = 0
        ad = 0
    #otherwise it is checked if the retrieval duration, catch-up time, and
    #activation duration are on a quarter-hourly resolution
    elif (rd % 0.25) + (ct % 0.25) + (ad % 0.25):
        #if not, they are round-up to the next 0.25 value 
        if rd % 0.25:
            rd = rd + (0.25 - (rd % 0.25))
        if ct % 0.25:
            ct = ct + (0.25 - (ct % 0.25))
        if ad % 0.25:
            ad = ad + (0.25 - (ad % 0.25))
    
    #update power adequatly, to account for changes in the retrieval duration
    power = power * row['retrieval duration']/rd
    #update duration, due to possible adaption of rd, ct, or ad 
    duration = rd + ct + ad
    
    #second check: application of the flexibility measure with the given duration
    #and retrieval frequency must be plausible and fit into one year
    if duration * rf > 8760:
        #adapt retrieval frequency
        rf = 8760 // duration
    
    #update row with potentially adapted values
    row['retrieval duration'] = rd
    row['catch-up time'] = ct
    row['activation duration']
    row['power'] = power 
    row['retrieval frequency'] = rf 
    
    return row

def fillna_dict(dictionary:dict) -> dict :
    
    """Replace 'NaN' values in a dictionary with 0.
    
    Parameters
    ----------
    dictionary : dict
        Dictionary where NaN values should be replaced by 0.
        
    Returns
    -------
    dict
        Dictionary with 0s instead of NaN values.
    """
    for key in dictionary:
        if isinstance(dictionary[key],float) and isnan(dictionary[key]):
            dictionary[key] = 0
            
    return dictionary
        
    