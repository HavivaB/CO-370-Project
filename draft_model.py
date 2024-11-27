
import gurobipy as gp
from gurobipy import GRB

'''
Processing data
'''
# File containing passenger demands (days are separated by: "end")
f_demands = open("demands.txt", "r")
demand_data = f_demands.readlines()
f_demands.close()

# File containing ticket revenues data
f_revenues = open("ticket_revenues.txt", "r")
rev_data = f_revenues.readlines()
f_revenues.close()

# Cities by table index are given by:
table_index = {'H':0, 'M':1, 'T':2, 'W':3, 'V':4}

# Reading the demands data
day_total = 0               # total number of passengers flying in one day
total_daily_demands = []    # list of total number of passengers flying by day
day_demands_matrix = []     # matrix of passenger demands for one day
demands_matrix = []         # list of daily demands matrices
for line_num in range(0, len(demand_data)):
    row = demand_data[line_num].split(",")
    if row == ["end\n"] or row == ["end"]:   # end of the data for this day
        demands_matrix.append(day_demands_matrix)
        day_demands_matrix = []
        total_daily_demands.append(day_total)
        day_total=0
    else:
        row = list(map(lambda x: int(x), row))
        day_total += sum(row)
        day_demands_matrix.append(row)

# Reading the revenue data
revenues_matrix = []
for line_num in range(0, len(rev_data)):
    row = rev_data[line_num].split(",")
    revenues_matrix.append(list(map(lambda x: int(x), row)))

'''
# Building the digraph
'''
cities = ['V', 'W', 'T', 'M', 'H']
arc_set = [] + ['T*-H', 'M*-H']  # form: each arc (i,j) is a string: "i-j"  
for i in cities:
    arc_set.append(i + '-' + 't')
    for j in cities:
        if i != j:
            if i == 'T' or i == 'M':
                arc_set.append(i + j + '-' + j)
                arc_set.append(i + j + '-' + 't')
            elif i == 'V' or i == 'W':
                if j == 'H':
                    arc_set.append(i + j + '-' + 'T*') 
                    arc_set.append(i + j + '-' + 'M*')
                    arc_set.append(i + j + '-' + 't')
                else:
                    arc_set.append(i + j + '-' + j)
                    arc_set.append(i + j + '-' +'t')
            else: #i = 'H'
                if j == 'T' or j == 'M':
                    arc_set.append('H' + j + '-' + j)
                    arc_set.append(i + j + '-' + 't')
                elif j == 'W' or j == 'V': 
                    arc_set.append('H' + j + '-' + 'T*'), arc_set.append('T*' + '-' + j)
                    arc_set.append('H' + j + '-' + 'M*'), arc_set.append('M*' + '-' + j)
                    arc_set.append(i + j + '-' + 't')

node_set = cities.copy() + ['T*', 'M*', 't']
for i in cities:
    for j in cities:
        if i != j:
            node_set.append(i + j)


'''
# Building the model
'''
FLIGHTS_MODEL = gp.Model("Passenger_Demands")

# Variables - by arc and day
X = FLIGHTS_MODEL.addVars(arc_set, [0,1,2,3,4], vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'), name="x")
n = FLIGHTS_MODEL.addVars(arc_set, [0, 1, 2, 3, 4], vtype=GRB.INTEGER, lb=0, name="n") # This is the total number of flights flying from city i to j on day k

# Parameters
plane_capacity = 211 # aribitray plane capcity 
FuelCost = 1000  # Arbitrary fuel cost per flight This is temprory should really vaary from place to place
LandingCost = 500  # Arbitrary landing cost per flight really should vary from place to place
DepartureCost = 500  # Arbitrary departure cost per flight Vary from place to place


# Objective function
obj_fn = 0
for day_num in range(0,5):
    for arc in arc_set:
        depart = arc.split("-")[0][0]
        arrive = arc.split("-")[1][0]
        if arrive != 't': # then the arc has some cost
            revenue = revenues_matrix[table_index[depart]][table_index[arrive]] * X[arc, day_num]
            cost = (FuelCost + LandingCost + DepartureCost) * n[arc, day_num] # arbitrarily added really costs need to be adjusted
            # obj_fn += revenues_matrix[table_index[depart]][table_index[arrive]] * X[arc, day_num]
            obj_fn += revenue - cost

## Add fixed costs by plane here - not related to passenger demands

FLIGHTS_MODEL.setObjective(obj_fn, GRB.MAXIMIZE)


# Flow conservation constraints - by node and day
for day_num in range(0,5):
    for v in node_set:
        v_demand = 0
        if v == 't': # the sink node
            v_demand = total_daily_demands[day_num]
        elif (len(v) == 1) or (v == 'T*') or (v=='M*'): # a destination node
            v_demand = 0
        else: # a supply node
            depart = list(v)[0]   # starting city
            arrive = list(v)[1]   # destination city
            v_demand = -1 * demands_matrix[day_num][table_index[depart]][table_index[arrive]]

        v_constraint = 0
        for arc in arc_set:
            if v == arc.split("-")[0]: # outgoing arc from v
                v_constraint += -1 * X[arc,day_num]
            elif v == arc.split("-")[1]: # incoming arc to v
                v_constraint += X[arc,day_num]
    
        FLIGHTS_MODEL.addConstr(v_constraint == v_demand, name=v+str(day_num)) # flow conservation constraints


# Flow conservation - ensure those on layovers make their destination
for day_num in range(0,5):
    FLIGHTS_MODEL.addConstr(X['VH-T*', day_num] + X['WH-T*', day_num] == X['T*-H', day_num])
    FLIGHTS_MODEL.addConstr(X['VH-M*', day_num] + X['WH-M*', day_num] == X['M*-H', day_num])
    FLIGHTS_MODEL.addConstr(X['HV-T*', day_num] == X['T*-V', day_num])
    FLIGHTS_MODEL.addConstr(X['HV-M*', day_num] == X['M*-V', day_num])
    FLIGHTS_MODEL.addConstr(X['HW-T*', day_num] == X['T*-W', day_num])
    FLIGHTS_MODEL.addConstr(X['HW-M*', day_num] == X['M*-W', day_num])


# Capacity constraints
for day_num in range(0, 5):
    for arc in arc_set:
        if 't' not in arc:  # Ignore sink arcs
            FLIGHTS_MODEL.addConstr(
                X[arc, day_num] <= plane_capacity * n[arc, day_num],
                name="capacity_" + arc + "_" + str(day_num)
            )

# Profit constraints
for day_num in range(0, 5):
    for arc in arc_set:
        if 't' not in arc:  # Ignore sink arcs
            ticket_price = revenues_matrix[table_index[arc.split("-")[0][0]]][table_index[arc.split("-")[1][0]]]
            operating_cost = (FuelCost + LandingCost + DepartureCost) * n[arc, day_num]
            FLIGHTS_MODEL.addConstr(
                operating_cost <= ticket_price * X[arc, day_num],
                name="profit_" + arc + "_" + str(day_num)
            )


# Run the model
FLIGHTS_MODEL.optimize()


# Test to confirm:
for day_num in range(0,5):
    for arc in arc_set:
        if (len(arc.split("-")[0])==2) and (arc.split("-")[1] == 't'):
            print("X[" + arc + ", " + str(day_num) + "] = " + str(X[arc, day_num].X))
