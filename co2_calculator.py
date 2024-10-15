# -*- coding: utf-8 -*-
"""CO2 and Cost Reduction Calculator for Flexibility Measures

This calculator allows the user to compute the CO2 and cost reduction potential
of energy flexibility measures. The user can decide to calculate the reduction
potential with regard to the maximum CO2 reduction and/or the maximum cost 
reduction. Furthermore, the user has the option to calculate the reduction 
potential for a combination of load reduction and increase measures, when the
parameters of the respective flexibility measures allow so.

The calculator requires semicolon seperated input files (.csv) for the parameters 
of the flexiblity measures (dsm_rohdaten.csv), the average annual emission factors 
(emf) and electricity prices (mittlere_preise_und_emf.csv) as well as the 
quarter-hourly time series of prices and emf for the desired target years
(preis_und_emf_{year}.csv).

This code requires that `pandas` be installed within the Python environment the 
script is run in. 

This file contains the following function:
    
    * main - the main function of the calculator
    
@author: Nadine Gabrek
"""

from datetime import date
import read_and_write as rw
import calculate_reduction_potential as crp
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--filename', help='File name of the results file', type=str, default=str(date.today())+'_results')
parser.add_argument('--year', help='Year on which the calculation should be based on: 2019, 2020, 2021, 2022 or 2023', type=int, default=2023)
parser.add_argument('--combination', help='Choose mode of calculation: True for combination of load increase and reducation', type=bool, default=False)
parser.add_argument('--max_co2', help='Decide if the calculation should be based on the optimization of the CO2 reduction potential', type=bool, default=True)
parser.add_argument('--max_cost', help='Decide if the calculation should be based on the optimization of the cost reduction potential', type=bool, default=False)
args = parser.parse_args()


def main(results_file:str,year:int=2023,combination:bool=False,max_co2:bool=True,max_cost:bool=False):
    print("Start computation...")
    
    #read data 
    print("\nRead data..")
    df_price_emf, df_dsm, avg_price_emf = rw.read_input_data(year)
    
    #calculate CO2- and cost reduction potential of flexibility measures
    print("\nStart calculation of reduction potential...")
    results = crp.calc_reduction_potential(df_dsm,df_price_emf,avg_price_emf,max_co2,max_cost,combination)
    
    #write results to csv, if the user didn't set a file name a default format is applied
    print("\nWrite final results to csv...")
    rw.save_to_csv(results,f'output/{results_file}_{year}.csv')
    
    print("\nDone.")
    

if __name__ == "__main__":
    if args.filename == "":
        main("Test_14102024")
    else:
        main(args.filename,args.year,args.combination,args.max_co2,args.max_cost)
 