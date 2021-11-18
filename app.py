#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 16:28:29 2021

@author: benoitdeschrynmakers
"""

from flask import Flask, request
import json
from random import choice
import numpy as np 
import json
import numpy as np
from scipy.optimize import linprog


app = Flask(__name__)


@app.route('/productionplan', methods=['POST'])
def solve_problem():
    
    data = request.get_json()

    fuels =  list(data["fuels"].values())
    load = float(data["load"])
    powerplants = [list(x.values()) for x in data["powerplants"]]
     
    
    # 1. Decision Variable
    #──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    
    decision_variables = {
        
        "fuels" : list(data["fuels"].values()),
        "load" : (data["load"]),
        "powerplants" : [list(x.values()) for x in data["powerplants"]]
    }   
    
    
    # 2. Solution Encoding
    #──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    
    
    size =  len(decision_variables["powerplants"])
           
    index_windturbine = [] 
    for index, test in enumerate(powerplants):
        for ind, value in enumerate(test):
            if value =="windturbine":
                index_windturbine.append(index)
    number_windturbine = len(index_windturbine) 
    
    index_thermal = []
    for index, test in enumerate(powerplants):
        for ind, value in enumerate(test):
            if value =="gasfired":
                index_thermal.append(index)
            elif value =="turbojet":
                index_thermal.append(index)
    number_thermal = len(index_thermal) 
    
    
    def get_marginal_cost(plant):
            if powerplants[plant][1] == "gasfired":
                return round(fuels[0] / powerplants[plant][2],1)
            elif powerplants[plant][1] == "turbojet":
                return round(fuels[1] / powerplants[plant][2],1)
            elif powerplants[plant][1] == "windturbine":
                return float(0)
        
    marginal_cost = [get_marginal_cost(i) for i in range(size)]
    marginal_cost_index = [get_marginal_cost(i) for i in range(size)]
    powerplant_names = [powerplants[i][0] for i in range(size)]
    powerplant_type = [powerplants[i][1] for i in range(size)]
    powerplant_Pmin = [powerplants[i][3] for i in range(size)]
    powerplant_Pmax = [powerplants[i][4] for i in range(size)]
    
    merit_order = {powerplant_names[i]: [powerplant_type[i],marginal_cost[i],powerplant_Pmin[i],powerplant_Pmax[i]] for i in range(size)}
    merit_order_index = ([i[0] for i in sorted(enumerate(marginal_cost), key=lambda k: k[1])])
    
    
    # 3. Build Solution
    #──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    
    def build_solution():
           
           solution_representation = [0 for i in range(size)]
           indexes_available = [number for number in range(len(solution_representation))] 
           capacity_used = 0
           remaining_capacity = load
           counter = 0
    
           if fuels[-1] != 0 and number_windturbine != 0:
                  
                
                while counter < number_windturbine and capacity_used < load :
                    random_index = choice(index_windturbine)
                    indexes_available.remove(random_index)
                    index_windturbine.remove(random_index) 
                    merit_order_index.remove(random_index)
                    capacity = round(powerplants[random_index][4] * ((fuels[-1])*0.01),1)
                    capacity_used += capacity
                    remaining_capacity -= capacity 
                    solution_representation[random_index] = capacity
                    counter += 1                            
                
                else: 
                    
                    Pmax = powerplant_Pmax[0:4]
                    Pmin = powerplant_Pmin[0:4]
                    obj = marginal_cost[0:4]
                    lhs_eq = [[1,1,1,1]]  
                    rhs_eq = [remaining_capacity]
                    bnd = [(Pmin[i], Pmax[i]) for i in range(len(Pmin))] 
                    opt = linprog(c=obj, A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd, method="revised simplex")
                    thermal_list = opt.x.tolist()
                    thermal_list = [round(num, 1) for num in thermal_list]
                    
    
            
           if fuels[-1] == 0 and number_windturbine != 0:
                
                
                while counter < number_windturbine and capacity_used < load :
                    random_index = choice(index_windturbine)
                    indexes_available.remove(random_index)
                    index_windturbine.remove(random_index)
                    merit_order_index.remove(random_index)
                    counter += 1   
                
                else:
                    Pmax = powerplant_Pmax[0:4]
                    Pmin = powerplant_Pmin[0:4]
                    obj = marginal_cost[0:4]
                    lhs_eq = [[1,1,1,1]]  
                    rhs_eq = [remaining_capacity]
                    bnd = [(Pmin[i], Pmax[i]) for i in range(len(Pmin))] 
                    opt = linprog(c=obj, A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd, method="revised simplex")
                    thermal_list = opt.x.tolist()
                    thermal_list = [round(num, 1) for num in thermal_list]
                    
                    
           
           solution = thermal_list + solution_representation[4:]
           
          
           return solution 
             
    solution_test=build_solution()
    
    # 4. Optimize Solution (merit-order)
    #──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    
    def optimize(solution):
        
        solution= solution_test
        to_add = solution[2]    
        r1 = powerplant_Pmax[0] - solution[0]
        r2 = powerplant_Pmax[1] - solution[1] 
        
        if r1 + r2 >= to_add:
            
            if r1 >= to_add :
                solution[0] += to_add
                solution[2] = 0
            
            else:
                solution[0] += r1
                to_add -= r1
                solution[1] += to_add
                solution[2] = 0
        
        return solution
    
    
    solution = optimize(solution_test)
    
    # 5. Json export
    #──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
       
        
    dict_1 = {"name": powerplant_names[0] , "p": solution[0] }
    dict_2 = {"name": powerplant_names[1] , "p": solution[1] }
    dict_3 = {"name": powerplant_names[2] , "p": solution[2] }
    dict_4 = {"name": powerplant_names[3] , "p": solution[3] }
    dict_5 = {"name": powerplant_names[4] , "p": solution[4] }
    dict_6 = {"name": powerplant_names[5] , "p": solution[5] }
    
    
    solution = (json.dumps([dict_1,
                             dict_2,
                             dict_3,
                             dict_4,
                             dict_5,
                             dict_6], indent=5))
    
    return solution

    
        



if __name__ == '__main__':
    app.run(port=8888, debug=True)
    
    







