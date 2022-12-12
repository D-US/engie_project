from flask import Flask
from flask import request
from flask import jsonify
import math

app = Flask(__name__)

#global variables
power_plant_type = ['gasfired', 'turbojet', 'windturbine']
fuels_type = ["gas(euro/MWh)", "kerosine(euro/MWh)", "co2(euro/ton)",  "wind(%)"]
sorting_label = ['efficiency', 'pmin', 'pmax', 'unit_needed', 'energy_per_hour' ]

@app.route("/productionplan", methods = ['POST'])
def init():
    payload_json = request.get_json( )
    load = payload_json ['load']
    fuels_ar = payload_json['fuels']
    powerplants_ar = payload_json['powerplants']

    dict_list = calculate_power_cost(fuels_ar, powerplants_ar )
    dict_list = merit_ranking(dict_list)
    dict_list = assign_p_value(load, dict_list)
    

    return build_render_json(dict_list)


def assign_p_value(load_value, power_plant_list):
    new_list = []
    result_wind =  assign_p_value_by_plant_type(load_value, power_plant_type[2],power_plant_list)
    new_list = result_wind[0]

    
    result_gas = assign_p_value_by_plant_type(result_wind[1], power_plant_type[0],power_plant_list)
    for item in result_gas[0]:
        new_list.append(item)
    
    result_turbo = assign_p_value_by_plant_type(result_gas[1], power_plant_type[1],power_plant_list)
    for item in result_turbo[0]:
        new_list.append(item)
    
    return new_list

def assign_p_value_by_plant_type(rem_load_value, plant_type, power_plant_list):
    new_list = []
    load_val = rem_load_value
    print (load_val, plant_type,power_plant_list )
  
    if plant_type == power_plant_type[2]:
        plant_list = get_plant_by_type(power_plant_list, plant_type)
        if load_val <= 0:
            for item in plant_list:
                item['p'] = 0
                new_list.append(item)
        else:
            for item in plant_list:
                item['p'] = item['energy_per_hour']
                new_list.append(item)
                load_val -= item['p']

    elif (plant_type == power_plant_type[0]) or (plant_type == power_plant_type[1]):
        plant_list = get_plant_by_type(power_plant_list, plant_type)
        for item in plant_list:
            if load_val <=0:
                item['p'] =0
                load_val = 0

            elif load_val <= item['pmin'] :
                item['p'] = load_val
                load_val = 0

            elif load_val >= item['pmin'] & load_val <= item['pmax'] :
                item['p'] = load_val
                load_val -= item['p']
            
            else:
                item['p'] = load_val - ( item['pmax'] - item['pmin'])
                load_val -= item['p']

            new_list.append(item)

    return [new_list, load_val]

def calculate_power_cost(fuels_ar, powerplants_ar ):
   
    new_powerplants_ar =[]
    for plant in powerplants_ar:
        unit_needed = 1/plant['efficiency']
        price = -1
        energy_per_hour = -1
        if plant['type'].lower() == power_plant_type[0]:
            price = fuels_ar[fuels_type[0]]

        elif plant['type'].lower() == power_plant_type[1]:
            price = fuels_ar[fuels_type[1]]
        
        elif plant['type'].lower() == power_plant_type[2]:
            price = fuels_ar[fuels_type[2]]
            energy_per_hour =(plant['pmax'] *fuels_ar[fuels_type[3]] ) / 100          
        
        else:
            energy_per_hour = (plant['pmax'] *fuels_ar[fuels_type[3]] ) / 100 

        
        plant["range_power"] = (plant['pmax'] - plant['pmin'])
        plant["cost_1mwh"]= round(unit_needed * price, 1)
        plant["unit_needed"]= math.floor(unit_needed)
        plant['energy_per_hour']= math.floor(energy_per_hour)

        new_powerplants_ar.append(plant)

    return new_powerplants_ar

def merit_ranking(power_plant_list):
    ranking =0
    result_wind = rank_plant_by_type(power_plant_list, power_plant_type[2], start_ranking=ranking)
    new_list = result_wind[0]

    result_gas = rank_plant_by_type(power_plant_list, power_plant_type[0], start_ranking=result_wind[1])
    for item in result_gas[0]:
        new_list.append(item)

    result_turbo = rank_plant_by_type(power_plant_list, power_plant_type[1], start_ranking= result_gas[1])
    for item in result_turbo[0]:
        new_list.append(item)

    return new_list

def get_plant_by_type(power_plant_list, plant_type):
    new_list =[]
    for plant in power_plant_list:
        if plant['type'].lower() == plant_type.lower():
            new_list.append(plant)
    return new_list

def rank_plant_by_type(power_plant_list, plant_type, start_ranking=0):
    plant_list = get_plant_by_type(power_plant_list, plant_type)
    newlist =[]
    temp_list= []
    rank = start_ranking
    if plant_type in power_plant_type[0:2]:
        temp_list = sorted(plant_list, key=lambda i: (i[sorting_label[0]], i[sorting_label[1]], i[sorting_label[2]], i[sorting_label[3]]),  reverse=True)
        
    else:
         temp_list = sorted(plant_list, key=lambda i: (i[sorting_label[2]], i[sorting_label[4]]),  reverse=True)

    for item in temp_list:
        item['rank'] = rank
        newlist.append(item)
        rank += 1

    return [newlist, rank]


def build_render_json(return_value):
    val =  []
    for item in return_value:
        temp ={
           'name': item['name'], 
           'p' : item['p']
        }
        val.append(temp)
    return val#jsonify(val)

if __name__ == '__main__':
    app.run(host="localhost", port=8888, debug=True)