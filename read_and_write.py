# -*- coding: utf-8 -*-
# Script published by Hochschule Mannheim - Mannheim University of Applied Sciences - Germany: https://www.hs-mannheim.de/
"""
A module used to read the data required for the calculation and to store the 
results. 

Methods
-------
read_input_data : 
    Read in and return all relevant input data for the given target year.  
read_price_and_emf :
    Read in data set with time series of electricity prices [€/MWh] and  
    emission factors (emf) [g CO2-äq./kWh].
read_and_adapt_dsm : 
    Read in data set of flexibility measures defined by the user and transform
    it into an adequate format for further use.
read_avg_price_and_emf : 
    Read in and return annual emissionfactors (emf) [g CO2-äq./kWh] and average 
    electricity price [€/MWh] of target year.
save_to_csv : 
    
    
@author: Nadine Gabrek
"""

import pandas as pd
from auxiliary_calculation import add_row
from math import isnan

def read_input_data(year:int) -> (pd.DataFrame,pd.DataFrame,tuple) :
    
    """Read in and return all relevant input data for the given target year.
    
    Next to the quarter-hourly time series of electricity prices and emission 
    factors (emf) of the target year, the method returns the annual emf and 
    average price. Furthermore, the input data of the energy flexibility 
    measures is read, adapted (adaptions are saved in csv file), and returned. 
    
    Parameters
    ----------
    year : int
        The target year for the calculation, from which the electricity prices 
        and emf stem. 
        
    Returns
    -------
    pandas.DataFrame
        A data frame of quarter-hourly time series with electricity prices and emf.
    pandas.DataFrame
        A data frame with adapted parameters of the flexibility measures.
    tuple
        A tuple with the average annual electricity price and emf. 
    """
    
    #Read quarter-hourly times series of prices and emf of target year
    df_price_emf = read_price_and_emf(f'data/preis_und_emf_{year}.csv')
    
    #Read average annual price and emf of target year
    avg_price_emf = read_avg_price_and_emf('data/mittlere_preise_und_emf.csv',year)

    #Read and adapt the input data of flexibility measures 
    df_dsm = read_and_adapt_dsm('data/dsm_rohdaten.csv')
    
    #Write the adapted data of flexibility measures in a csv and save it 
    save_to_csv(df_dsm,'output/adapted_dsm.csv')

    return df_price_emf, df_dsm, avg_price_emf

def read_price_and_emf(path:str) -> pd.DataFrame :
    
    """Read in data set with time series of electricity prices [€/MWh] and  
    emission factors (emf) [g CO2-äq./kWh].
    
    This method reads in a semicolon seperated csv-file, which contains 
    quarter-hourly time series of electricity prices and CO2 emission factors 
    (emf) that have the column names 'Strompreis' and 'CO₂-Emissionsfaktor des 
    Strommix'. The column names are adapted for further use before the data
    frame is returned. 
    
    Parameters
    ----------
    path : str
        The path of the file that contains the required data.
        
    Returns
    -------
    pandas.DataFrame
        A data frame of quarter-hourly time series with electricity prices and emf.
    """
    
    #Read in data set, column names are specified to simplfy the renaming
    df = pd.read_csv(path,sep=';',usecols=['Strompreis','CO₂-Emissionsfaktor des Strommix'],encoding='utf-8')
    #Rename columns for an easier handeling in the later calculations
    df = df.rename(columns={'Strompreis':'price','CO₂-Emissionsfaktor des Strommix':'emf'})
    
    return df

def read_and_adapt_dsm(path:str) -> pd.DataFrame :
    
    """Read in data set of flexibility measures defined by the user and transform
    the data into an adequate format for further use.
    
    The user defines all energy flexibility measures, for which the calculation 
    of the reduction potential should be conducted, in the csv-file 'dsm_rohdaten'. 
    This semicolon seperated file is then read in and transformed into an adequate 
    format for further use. Each flexibility measure can be defined for eight 
    different cases: potential or perspective, maximum flexible power or retrieval
    duration, load reduction or load increase. 
    
    Units of input data:
        - power [kW]
        - retrieval duration [h]
        - catch-up time [h] 
        - retrieval frequency [1/a] 
    
    Parameters
    ----------
    path : str
        The path of the file that contains the required data.
        
    Returns
    -------
    pandas.DataFrame
        A data frame with the adapted flexibility measures data.
    """
    
    #read in data of the flexibility measures defined by the user
    df = pd.read_csv(path,sep=';',decimal='.', encoding='utf-8')
    
    #define new data frame with required format for further use
    df_new = pd.DataFrame(columns=['TP','name','scope','maximization','load change','power','retrieval duration',
                                   'activation duration','catch-up time','retrieval frequency'])
    
    #check which cases of the measures were defined by user and append data of 
    #the respective cases in new format to a newly defined data frame
    for index,row in df.iterrows():

        #there are 8 different cases 
        if not isnan(row['Potential_maxLeistung_LE_Leistung [kW]']):
            df_new = add_row(row,df_new,'potential','power','load increase')
            
        if not isnan(row['Potential_maxLeistung_LV_Leistung [kW]']):
            df_new = add_row(row,df_new,'potential','power','load reduction')
            
        if not isnan(row['Potential_maxAbrufdauer_LE_Leistung [kW]']):
            df_new = add_row(row,df_new,'potential','retrieval duration','load increase')
            
        if not isnan(row['Potential_maxAbrufdauer_LV_Leistung [kW]']):
            df_new = add_row(row,df_new,'potential','retrieval duration','load reduction')
            
        if not isnan(row['Perspektive_maxLeistung_LE_Leistung [kW]']):
            df_new = add_row(row,df_new,'perspective','power','load increase')
            
        if not isnan(row['Perspektive_maxLeistung_LV_Leistung [kW]']):
            df_new = add_row(row,df_new,'perspective','power','load reduction')
            
        if not isnan(row['Perspektive_maxAbrufdauer_LE_Leistung [kW]']):
            df_new = add_row(row,df_new,'perspective','retrieval duration','load increase')
            
        if not isnan(row['Perspektive_maxAbrufdauer_LV_Leistung [kW]']):
            df_new = add_row(row,df_new,'perspective','retrieval duration','load reduction')
    
    #return newly formatted data frame that only contains relevant cases 
    return df_new


def read_avg_price_and_emf(path:str,year:int) -> tuple :
    
    """Read in and return annual emissionfactors (emf) [g CO2-äq./kWh] and average 
    electricity price of target year.
    
    The annual emission factors in the semicolon seperated input csv 
    'mittlere_preise_und_emf' for the target years 2019 - 2023 can be downloaded from the
    CO2 Monitor by FfE and TenneT (https://co2-monitor.org/), which is generally
    calculated as follows: 
        annual emission factor = annual emissions / annual generation.
        
    Parameters
    ----------
    path : str
        The path of the file that contains the required data set.
    year : int
        The target year for the calculation, from which the electricity price 
        and emf stem.
        
    Returns
    -------
    tuple
        A tuple that contains the annual average electricity price and annual emf.
    """
    
    #read csv 
    df = pd.read_csv(path,sep=';', encoding='utf-8')
    
    #extract the annual specific emissions and average price for the target year 
    specific_emission = df.query(f'Jahr=={year}')['spez. CO2 Emissionen [g CO2/kWh]']
    avg_price = df.query(f'Jahr=={year}')['mittlerer Strompreis [EUR/MWh]']
    
    return (avg_price,specific_emission) 

def save_to_csv(df_dsm:pd.DataFrame, path:str) -> None :
    
    """Save the given data frame to a semicolon  seperated csv file.
    
    Parameters
    ----------
    df_dsm : pandas.DataFrame
        The data frame that is saved to csv.
    path : str
        The path where the csv is stored. 
    """
    
    df_dsm.to_csv(path, sep=";", encoding='utf-8')
    
    
    




