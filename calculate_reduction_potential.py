# -*- coding: utf-8 -*-
"""
A module that contains all relevant functions for the calculation of the 
CO2 and cost reduction potential of energy flexibility measures.

Methods
-------
calc_reduction_potential :
    Calculate the annual CO2 and cost reduction potential for a data set of
    flexibility measures.
calc_measure_individual : 
    Calculate the annual CO2 and cost reduction potential for a case of an 
    energy flexibility measure without a combination case.
calc_measure_combo :
    Calculate the annual CO2 and cost reduction potential for load increase,
    load reduction and their potential combination for a case of a flexibility measure.
calc_blocks :
    Calculates the CO2 and cost reduction potential of retrieval cycles over
    the target year for a case of an flexibility measure.
calc_load_change : 
    Calculate the quarter-hourly possible load change in MWh, based on the 
    power potential [kW] for a case of a flexibility measure.
calc_rc_length :
    Calculate the length of one retrieval cycle for a case of a flexibility
    measure.
blocks_quarter_hour :
    Calculates the CO2 and cost reduction potential of a retrieval cycle for
    every quarter of an hour.
block_reduction :
    Calculate the CO2 or cost reduction for one retrieval cycle.
max_in_block :
    Identify the quarter-hour with the highest reduction potential in a block.
calc_annual_potential :
    Calculate the annual CO2 and cost reduction potential for a case of a 
    flexibility measure.


@author: Nadine Gabrek
"""

import pandas as pd

def calc_reduction_potential(df_dsm:pd.DataFrame,df_price_emf:pd.DataFrame,avg_price_emf:tuple,
                             max_co2:bool=True,max_cost:bool=False,combo:bool=False) -> pd.DataFrame :
    
    """Calculate the annual CO2 and cost reduction potential for a data set of
    flexibility measures.
    
    This method calculates the annual CO2 and cost reduction potential of the 
    available cases of the given flexibility measures. Different calculation 
    modes are possible. By default only 'max_co2' is set to 'True', such that
    the maximum CO2 reduction potential and associated cost savings are calculated. 
    By setting 'max_cost' to 'True', it is further possible to calculate the maximum 
    cost reduction potential and its associated CO2 savings.The user can also 
    decide to include a special case for the flexibility measures that combines 
    load reduction and load increase, if possible, by setting 'combo' to 'True'.
    The method returns a data frame, where each row contains the results for one
    case of a flexibility measure.
    
    Parameters
    ----------
    df_dsm : pandas.DataFrame
        A data frame with the data of the flexibility measures.
    df_price_emf : pandas.DataFrame
        A data frame with the quarter-hourly time series of electricity prices and 
        emf for the target year. 
    avg_price_emf : tuple
        The annual emission factor (emf) and average electricity price of the 
        target year.
    max_co2 : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing emissions. The default is True.
    max_cost : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing costs. The default is False.
    combo : bool, optional
        A boolean value that indicates if the calculation should also include the
        combination of load increase and load reduction when feasible. The default
        is False.
        
    Returns
    -------
    pandas.DataFrame : 
        A data frame that contains the annual CO2 and cost reduction potential for
        each available case of the given flexibility measures. 
    """
    
    #define the format for the results of the calculation 
    final_results = pd.DataFrame(columns=['TP','name','scope','maximization',
                                          'load change','max. emission',
                                          'ass. cost','max. cost','ass. emission'])

    
    #if the mode combo=True is selected, calculate the reduction potential for 
    #the measures that allow a combination of load reduction and increase
    if combo: 
        #identify measures that potentially allow a combination
        df_dsm_combo = df_dsm[df_dsm.duplicated(['TP','name','scope','maximization',
                                                 'retrieval frequency'],keep=False)]
        df_dsm_lr = df_dsm_combo[df_dsm_combo['load change'] == 'load reduction']
        df_dsm_li = df_dsm_combo[df_dsm_combo['load change'] == 'load increase']

        #iterate over identified load reduction and increase measures to calculate 
        #their individual reduction potential and if possible for their combination
        for index_lr, measure_lr in df_dsm_lr.iterrows():
            #find corresponding measure in load increase dataset
            measure_li = df_dsm_li[(df_dsm_li['TP']==measure_lr['TP'])&
                                   (df_dsm_li['name']==measure_lr['name'])&
                                   (df_dsm_li['scope']==measure_lr['scope'])&
                                   (df_dsm_li['maximization']==measure_lr['maximization'])&
                                   (df_dsm_li['retrieval frequency']==measure_lr['retrieval frequency'])].squeeze()
            
            #calculate the reduction potential for the individual measures and,
            #if possible, for the combination 
            final_results = calc_measure_combo(measure_lr,measure_li,df_price_emf,
                                               avg_price_emf,final_results,max_co2,max_cost)
        
        #exclude df_dsm_combo entries from df_dsm to avoid another recalculation
        df_dsm = df_dsm.drop_duplicates(['TP','name','scope','maximization',
                                         'retrieval frequency'],keep=False)
        
            
    #iterate over remaining flexibility measures and calculate their reduction potential
    for index, measure in df_dsm.iterrows():
        #calculate the reduction potential for the individual measures and add 
        #it to the final results
        final_results.loc[len(final_results)] = calc_measure_individual(measure,
                                            df_price_emf,avg_price_emf,max_co2,max_cost)
        
    return final_results

def calc_measure_individual(measure:pd.Series,df_price_emf:pd.DataFrame,avg_price_emf:tuple,
                            max_co2:bool=True,max_cost:bool=False) -> list:
    
    """Calculate the annual CO2 and cost reduction potential for a case of an 
    energy flexibility measure without a combination case.
    
    This method calculated CO2 and cost reduction potential for the given case
    of an energy flexibility measure that does not allow the combination of load
    increase and load reduction. By default only 'max_co2' is set to 'True', such that
    the maximum CO2 reduction potential and associated cost savings are calculated. 
    By setting 'max_cost' to 'True', it is further possible to calculate the maximum 
    cost reduction potential and its associated CO2 savings.
    
    Parameters
    ----------
    measure : pandas.Series
        The data of one case of a flexibility measure.
    df_price_emf : pandas.DateFrame 
        A data frame with the quarter-hourly time series of electricity prices and 
        emf for the target year. 
    avg_price_emf : tuple
        The annual emission factor (emf) and average electricity price of the 
        target year.
    max_co2 : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing emissions. The default is True.
    max_cost : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing costs. The default is False.    
        
    Returns
    -------
    list
        A list with the results for the case of a flexibility measure in the
        format of the data frame with final results.
    """
        
    #split year in blocks with the length of a retrieval cycle and calculate
    #the maximum reduction potential for each block
    blocks = calc_blocks(measure,df_price_emf,avg_price_emf)
    #calculate annual reduction potential from the blocks
    results = calc_annual_potential(measure,blocks,max_co2,max_cost)
    
    return results

def calc_measure_combo(measure_lr:pd.Series,measure_li:pd.Series,
                       df_price_emf:pd.DataFrame,avg_price_emf:tuple,
                       final_results:pd.DataFrame,max_co2:bool=True,
                       max_cost:bool=False) -> pd.DataFrame:
    
    """Calculate the annual CO2 and cost reduction potential for load increase,
    load reduction and their potential combination for a case of a flexibility measure.
    
    This method calculates the annual CO2 and cost reduction potential for a 
    case of an energy flexibility measure that potentially allows a combination 
    of load increase and load reduction. The reduction potential is calculated 
    only considering load reduction, then only considering load increase and 
    finally for a combination of both, if their length of a retrieval cycle
    match. 

    Parameters
    ----------
    measure_lr : pandas.Series
        The data of one case with load reduction of a flexibility measure.
    measure_li : pandas.Series
        The data of one case with load increase of a flexibility measure.
    df_price_emf : pandas.DataFrame
        A data frame with the quarter-hourly time series of electricity prices and 
        emf for the target year.
    avg_price_emf : tuple
        The annual emission factor (emf) and average electricity price of the 
        target year.
    final_results : pandas.DataFrame
        The data frame that collects the annual CO2 and cost reduction potential 
        for each available case of the flexibility measures.
    max_co2 : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing emissions. The default is True.
    max_cost : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing costs. The default is False. 

    Returns
    -------
    final_results : pandas.DataFrame
        The updated data frame that collects the annual CO2 and cost reduction 
        potential for each available case of the flexibility measures.

    """
            
    #calculate reduction potential for load reduction version of the case  
    blocks_lr = calc_blocks(measure_lr,df_price_emf,avg_price_emf)
    length_lr = calc_rc_length(measure_lr)
    final_results.loc[len(final_results)] = calc_annual_potential(measure_lr,
                                                    blocks_lr,max_co2,max_cost)      
            
    #calculate reduction potential for load increase version of the case 
    blocks_li = calc_blocks(measure_li,df_price_emf,avg_price_emf)
    length_li = calc_rc_length(measure_li)
    final_results.loc[len(final_results)] = calc_annual_potential(measure_li,
                                                    blocks_li,max_co2,max_cost)
            
    #the combination of load reduction and increase is only possible if their 
    #length for a retrieval cycle match
    if length_lr == length_li:
        #create new data frame that collect maximum reduction from load 
        #reduction or increase for each block
        blocks_combo = pd.DataFrame(columns=['max. emission','ass. cost',
                                             'max. cost','ass. emission'])
          
        #iterate over the blocks of load increase and reduction and select 
        #maximum of both for each block
        for index, block_lr in blocks_lr.iterrows():
            block_li = blocks_li.loc[index]
                    
            if (block_lr['max. emission'] > block_li['max. emission']) & (block_lr['max. cost'] > block_li['max. cost']):
                blocks_combo.loc[len(blocks_combo)] = block_lr
            elif (block_li['max. emission'] > block_lr['max. emission']) & (block_li['max. cost'] > block_lr['max. cost']):
                blocks_combo.loc[len(blocks_combo)] = block_li
            elif (block_lr['max. emission'] > block_li['max. emission']) & (block_li['max. cost'] > block_lr['max. cost']):
                blocks_combo.loc[len(blocks_combo)] = [block_lr['max. emission'],
                                                       block_lr['ass. cost'],
                                                       block_li['max. cost'],
                                                       block_li['ass. emission']]
            else:
                blocks_combo.loc[len(blocks_combo)] = [block_li['max. emission'],
                                                       block_li['ass. cost'],
                                                       block_lr['max. cost'],
                                                       block_lr['ass. emission']]  
            
            #define the new combination case of the measure
            measure_combo = {'TP' : measure_lr['TP'],'name' : measure_lr['name'],
                             'scope' : measure_lr['scope'], #exchanged for "combination
                             'maximization':measure_lr['maximization'],
                             'load change':'combination', #exchanged for 'Nan'
                             'retrieval frequency':measure_lr['retrieval frequency']}
        #calculate the reduction potential of the combination and append it
        #to final results data frame
        final_results.loc[len(final_results)] = calc_annual_potential(
                                                    measure_combo,blocks_combo,
                                                    max_co2,max_cost)
      
    return final_results
    

def calc_blocks(measure:pd.Series,df_price_emf:pd.DataFrame,
                        avg_price_emf:tuple) -> pd.DataFrame:
    
    """Calculate the CO2 and cost reduction potential of retrieval cycles over
    the target year for a case of an flexibility measure.
    
    This method calculates the CO2 and cost reduction potential of the givne case
    of an energy flexibility measure for blocks of the length of a retrieval cycle
    over the given target year. Therefore, the potential is first calculated for 
    every quarter of an hour, assuming the respective quarter of an hour to be 
    the starting point of the retrieval cycle. In a next step, this time series
    is seperated into consecutively blocks with the length of a retrieval cycle,
    which are represented by the quarter of an hour with the maximum reduction
    potential within the block.
    
    Parameters
    ----------
    measure : pandas.Series
        The data of one case of a flexibility measure.
    df_price_emf : pandas.DateFrame 
        A data frame with the quarter-hourly time series of electricity prices 
        and emf for the target year. 
    avg_price_emf : tuple
        The annual emission factor (emf) and average electricity price of the 
        target year.
        
    Returns
    -------
    pandas.DataFrame : 
        A data frame with the reduction potential of possible retrieval cycles
        over the target year.
    """
    #calculate load change for one quarter of an hour of the measure
    load_change = calc_load_change(measure)
        
    #get the length of one retrieval cycle
    length = calc_rc_length(measure)

    #calculate reduction potentials for one retrieval cycle for every quarter
    #of an hour
    df_reductions = blocks_quarter_hour(df_price_emf,avg_price_emf,load_change,
                                    measure['retrieval duration'])
        
    #identify max. reduction potential for each retrieval cycles (blocks)
    df_blocks = max_in_block(df_reductions,length)
        
    return df_blocks
    

def calc_load_change(measure:pd.Series) -> float :
    
    '''Calculate the quarter-hourly possible load change in MWh, based on the 
    power potential [kW] for a case of a flexibility measure.
    
    This methods calculates the load change in MWh that can be provided by the 
    available case of the given energy potential, based on the flexible potential
    [kW] of the measure. 
    
    Parameters
    ----------
    measure : pandas.Series
        The data of one case of a flexibility measure.
        
    Returns
    -------
    float :
        The load change in MWh for a case of a flexibility measure.
    '''
    
    #flexible power is given in kW, while the quarter-hourly load change is in MWh
    load_change = measure['power'] / 1000 / 4
    
    #in case of load reduction the possible load change is negative 
    if measure['load change'] == 'load reduction': load_change = load_change * (-1)
    
    return load_change

def calc_rc_length(measure:pd.Series) -> float:
    
    '''Calculate the length of one retrieval cycle for a case of a flexibility
    measure.
    
    The length of the retrieval cycle [h] for the available case of a given energy
    flexibility measure is the summation of the respective activation duration, 
    retrieval duration, and catch-up time.
    
    Parameters
    ----------
    measure : pandas.Series
        The data of one case of a flexibility measure.
        
    Returns
    -------
    float :
        The length of one retrieval cyvle for a case of a flexibility measure.
    '''
    
    return measure['retrieval duration'] + measure['catch-up time'] + measure['activation duration']

def blocks_quarter_hour(df_price_emf:pd.DataFrame, avg_price_emf:tuple, 
                    load_change:float, rd:float) -> pd.DataFrame :
    
    '''Calculates the CO2 and cost reduction potential of a retrieval cycle for
    every quarter of an hour.
    
    Parameters
    ----------
    df_price_emf : pandas.DateFrame 
        A data frame with the quarter-hourly time series of electricity prices 
        and emf for the target year.
    avg_price_emf : tuple
        The annual emission factor (emf) and average electricity price of the 
        target year.
    load_change : float
        The quarter-hourly load change for a case of a flexibility measure.
    rd : float
        The retrieval duration, which is the length of a retrieval cycle for a
        case of a flexibility measure. 
        
    Returns
    -------
    pandas.DataFrame : 
        A data frame with the CO2 and cost reduction potential of a retrieval 
        cycles for every quarter of an hour in the target year. 
    '''
    
    #calc reduction potential of a block for every quarter of an hour 
    df_price_emf['emission_reduction'] = df_price_emf.apply(lambda x: 
                                                block_reduction(x,'emf', df_price_emf, load_change, avg_price_emf, rd),axis=1)
    df_price_emf['price_reduction'] = df_price_emf.apply(lambda x: 
                                                block_reduction(x,'price', df_price_emf, load_change, avg_price_emf, rd),axis=1)
    
    return df_price_emf

def block_reduction(row:pd.Series, column:str,df_price_emf:pd.DataFrame, load_change:float, 
                         avg_price_emf:tuple, rd:float) -> float :
    
    '''Calculate the CO2 or cost reduction for one retrieval cycle.
    
    This methods calculates the CO2 or cost reduction potential (as indicated by
    column)for a retrieval cycle for a case of an energy flexibility measure for
    a given time frame of the target year. The following formula is applied over
    one retrieval cycle to calculate the CO2 reduction potential:
        CO2 reduction potential = ∑ load change * (-emf + average emf).
    The equivalent formula is applied for the calculation of the cost reduction,
    using electricity prices instead of emf. 
        
    
    Parameters
    ----------
    row : pandas.Series
        The row of a data frame, which represents a specific quarter-hour from 
        time series of emission factors (emf) and electricity prices.
    column : str
        A string that indicates for which column of the time series ('emf' or 'price')
        the calculation should be conducted. 
    df_price_emf : pandas.DateFrame 
        A data frame with the quarter-hourly time series of electricity prices 
        and emf for the target year.
    load_change : float
        The quarter-hourly load change for a case of a flexibility measure.
    avg_price_emf : tuple
        The annual emission factor (emf) and average electricity price of the 
        target year.
    rd : float
        The retrieval duration, which is the length of a retrieval cycle for a
        case of a flexibility measure.
    
    Returns
    -------
    float : 
        The CO2 or cost reduction of one retrieval cycle for a given time frame
        of the target year.
        
    '''
    if column not in ['emf','price']:
        raise ValueError('block_reduction: column must be "emf" or "price".')
    
    #rd [h] needs to be multiplied by 4 to match the index of the quarter-hourly times series
    last_index = row.name + (rd*4) - 1 
    
    #variable to access the correct column by index
    i = 0
    if column == 'emf':
        i = 1
        
    #if not enough quarter-hours for a block are left, the reduction is set to 0 
    if last_index > len(df_price_emf):
        reduction = 0    
    else:
        #the reduction is calculated by assuming the load change is made up for on average price or emf
        reduction = (-1) * (load_change * 
                            df_price_emf.loc[row.name:last_index,column]).sum() + (load_change* 
                                                                                   avg_price_emf[i] * (rd*4))
        
    return reduction

def max_in_block(df:pd.DataFrame, length:float) -> pd.DataFrame :
    
    '''Identify the quarter-hour with the highest reduction potential in a block.
    
    Seperates the given data frame of quarter-hourly reduction potentials into 
    blocks to account for time restrictions. Each block has the length of one 
    retrieval cycle and is represented by the maximum reduction potential within
    the block.
    
    Parameters
    ----------
    df : pandas.DataFrame
        A data frame of quarter-hourly reduction potentials for one retrieval
        cycle.
    length : float
        The length of one retrieval cycle for the given case of a flexibility
        measure. 
        
    Returns
    -------
    pandas.DataFrame :
        A data frame of retrieval cycles and their maximum reduction potential
        over the target year. 
    '''
    
    df_blocks = pd.DataFrame(columns=['max. emission','ass. cost','max. cost','ass. emission'])
    #needs to be multiplied by 4 to transform from hourly to quarter-hourly basis
    block = int(length*4)
    
    #iterate over quarter-hourly reductions based on the starting point of a block
    for index in range(0,len(df),block):
        #get indices with the maximum reduction potential in the current block
        max_indices = df.loc[index:(index+block-1),'emission_reduction':'price_reduction'].idxmax()
        
        #extract and save new blocks and their reduction potential to data frame
        df_blocks.loc[len(df_blocks)] = [df.loc[max_indices[0],'emission_reduction'],df.loc[max_indices[0],'price_reduction'],
                         df.loc[max_indices[1],'price_reduction'],df.loc[max_indices[1],'emission_reduction']]
    
    return df_blocks

def calc_annual_potential(measure:pd.Series,blocks:pd.DataFrame,
                          max_co2:bool=True,max_cost:bool=False) -> list:
    
    '''Calculate the annual CO2 and cost reduction potential for a case of a 
    flexibility measure.
    
    This methods aggregates the annual CO2 and cost reduction potential for a 
    case of an energy flexibility measure based on the annual retrieval frequency
    k by summing up the k blocks with the largest respective reduction potential.

    Parameters
    ----------
    measure : pd.Series
        The data of one case of a flexibility measure.
    blocks : pd.DataFrame
        A data frame with reduction potentials of retrieval cycles over the 
        target year.
    max_co2 : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing emissions. The default is True.
    max_cost : bool, optional
        A boolean value that indicates if the reduction potential should be
        calculated by minimizing costs. The default is False.

    Returns
    -------
    list
        A list that contains the annual CO2 and cost reduction potential for a 
        case of a flexibility measure. 
    '''
    
    reduction_emission = ['NaN','NaN']
    reduction_cost = ['NaN','NaN']
    
    if max_co2:
        #emission optimized annual reductions
        sorted_by_emissions = blocks[['max. emission','ass. cost']].sort_values(by=
                                                'max. emission', ascending=False)
        k_max_emissions = sorted_by_emissions.head(measure['retrieval frequency'])
        #measure is only applied when there is a positive reduction potential 
        k_max_emissions = k_max_emissions[k_max_emissions['max. emission'] > 0]
        reduction_emission = k_max_emissions.sum(axis=0)
    
    if max_cost:
        #cost optimized annual reductions
        sorted_by_cost = blocks[['max. cost','ass. emission']].sort_values(by='max. cost', ascending=False)
        k_max_cost = sorted_by_cost.head(measure['retrieval frequency'])
        #measure is only applied when there is a positive reduction potential 
        k_max_cost = k_max_cost[k_max_cost['max. cost'] > 0]
        reduction_cost = k_max_cost.sum(axis=0)
    
    return (measure['TP'], measure['name'], measure['scope'], measure['maximization'], measure['load change'], 
            reduction_emission[0], reduction_emission[1], reduction_cost[0], reduction_cost[1])


    
    