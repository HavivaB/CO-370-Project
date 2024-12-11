
## FUEL, LANDING FEES, AIF together
import gurobipy as gp
from gurobipy import GRB

airports = ['M', 'T', 'W', 'V', 'H']  

# Distance between airports in km
distances = {
    ('H', 'M'): 804,
    ('H', 'T'): 1288,
    ('M', 'T'): 507,
    ('M', 'W'): 1818,
    ('M', 'V'): 3682,
    ('T', 'W'): 1504,
    ('T', 'V'): 3345,
    ('W', 'V'): 1864,
}

# Fuel price at departing airport
fuel_prices = {
    'H': 1.28,
    'M': 1.17,
    'T': 1.29,
    'W': 1.19,
    'V': 1.30,
}

# Landing fees at airports
landing_fees = {
    "Halifax": 11.29,
    "Montreal": 11.64,
    "Toronto": 18.97,
    "Winnipeg": 7.50,
    "Vancouver": 7.98,
}

# Airport Improvement Fee (AIF) per passenger for each airport
aif_rates = {
    "Halifax": 28,
    "Montreal": 35,
    "Toronto": 30,
    "Winnipeg": 25,
    "Vancouver": 25,
}

# Helper function to calculate fuel cost per flight
def calculate_fuel_cost(arc):
    """
    Calculate the fuel cost of traveling along a given arc (route).
    """
    depart_city = arc[0]  # Departure city code
    arrive_city = arc.split("-")[1][0]  # Arrival city code

    # Exclude arcs involving sink nodes or invalid routes
    if depart_city == "t" or arrive_city == "t" or "*" in depart_city or "*" in arrive_city:
        return 0

    # Validate city codes
    if depart_city not in airports or arrive_city not in airports:
        print(f"Warning: Invalid city code in arc {arc}")
        return 0

    # Calculate fuel cost based on distance and consumption
    distance = distances.get((depart_city, arrive_city), 0) or distances.get((arrive_city, depart_city), 0)
    fuel_price = fuel_prices[depart_city]
    fuel_consumption_per_km = 2.86  
    return distance * fuel_consumption_per_km * fuel_price

# Helper function to calculate landing fee
def get_landing_fee(arc):
    """
    Returns the landing fee for the destination city in the given arc.
    """
    destination = arc.split("-")[1][0]  # Get the destination city code
    city_map = {'H': 'Halifax', 'M': 'Montreal', 'T': 'Toronto', 'W': 'Winnipeg', 'V': 'Vancouver'}
    landing_fee_rate = landing_fees.get(city_map.get(destination, ""), 0)  # Fee rate per ton
    mtow_tons = 70.535  
    return landing_fee_rate * mtow_tons

# Helper function to calculate AIF per passenger
def get_aif(arc):
    """
    Returns the Airport Improvement Fee (AIF) for the departure city in the given arc.
    """
    departure = arc[0]  # Departure city code
    city_map = {'H': 'Halifax', 'M': 'Montreal', 'T': 'Toronto', 'W': 'Winnipeg', 'V': 'Vancouver'}
    aif_rate = aif_rates.get(city_map.get(departure, ""), 0)  # AIF per passenger
    return aif_rate

'''
Processing data
'''

# File containing passenger demands (days are separated by: "end")
f_demands = open("/Users/vivek.persad/Downloads/demands.txt", "r")  
demand_data = f_demands.readlines()
f_demands.close()

# File containing ticket revenues data
f_revenues = open("/Users/vivek.persad/Downloads/ticket_revenues.txt", "r")  
rev_data = f_revenues.readlines()
f_revenues.close()

# Cities by table index are given by:
table_index = {'H': 0, 'M': 1, 'T': 2, 'W': 3, 'V': 4}

# Reading the demands data
day_total = 0               # total number of passengers flying in one day
total_daily_demands = []    # list of total number of passengers flying by day
day_demands_matrix = []     # matrix of passenger demands for one day
demands_matrix = []         # list of daily demands matrices

for line_num in range(len(demand_data)):
    row = demand_data[line_num].split(",")
    if row == ["end\n"] or row == ["end"]:  # End of data for this day
        demands_matrix.append(day_demands_matrix)
        day_demands_matrix = []
        total_daily_demands.append(day_total)
        day_total = 0
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
print(arc_set) # Haviva added
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
X = FLIGHTS_MODEL.addVars(arc_set, [0,1,2,3,4], vtype=GRB.INTEGER, lb=0, ub=float('inf'), name="x")
n = FLIGHTS_MODEL.addVars(arc_set, [0, 1, 2, 3, 4], vtype=GRB.INTEGER, lb=0, name="n") # This is the total number of flights flying from city i to j on day k
Z = FLIGHTS_MODEL.addVars(cities, [0,1,2,3,4,5], vtype=GRB.INTEGER, lb=0, name="Z")


plane_capacity = 211  # Plane capacity of B767

# Objective
obj_fn = 0
for day_num in range(0,5):
    for arc in arc_set:
        depart = arc.split("-")[0][0]
        arrive = arc.split("-")[1][0]

        if arrive != "t":  # then the arc has some cost
            revenue = revenues_matrix[table_index[depart]][table_index[arrive]] * X[arc, day_num]
            fuel_cost = calculate_fuel_cost(arc) * n[arc, day_num] 
            landing_cost = get_landing_fee(arc) * n[arc, day_num] 
            aif_cost = get_aif(arc) * X[arc, day_num]  
            cost = fuel_cost + landing_cost + aif_cost 
            obj_fn += revenue - cost

FLIGHTS_MODEL.setObjective(obj_fn, GRB.MAXIMIZE)

# Flow conservation constraints - by node and day
for day_num in range(0,5):
    for v in node_set:
        v_demand = 0
        if v == 't': # the sink node
            v_demand = total_daily_demands[day_num]
        elif (len(v) == 1) or (v == 'T*') or (v=='M*'): # a destination node
            v_demand = 0
        else:  # a supply node
            depart = list(v)[0]   # starting city
            arrive = list(v)[1]   # destination city
            v_demand = -1 * demands_matrix[day_num][table_index[depart]][table_index[arrive]]

        v_constraint = 0
        for arc in arc_set:
            if v == arc.split("-")[0]: # outgoing arc from v
                v_constraint += -1 * X[arc,day_num]
            elif v == arc.split("-")[1]: # incoming arc to v
                v_constraint += X[arc,day_num]
        
        FLIGHTS_MODEL.addConstr(v_constraint == v_demand, name=f"flow_{v}_{day_num}")

# Flow conservation - ensure those on layovers make their destination
for day_num in range(0,5):
    FLIGHTS_MODEL.addConstr(X['VH-T*', day_num] + X['WH-T*', day_num] == X['T*-H', day_num])
    FLIGHTS_MODEL.addConstr(X['VH-M*', day_num] + X['WH-M*', day_num] == X['M*-H', day_num])
    FLIGHTS_MODEL.addConstr(X['HV-T*', day_num] == X['T*-V', day_num])
    FLIGHTS_MODEL.addConstr(X['HV-M*', day_num] == X['M*-V', day_num])
    FLIGHTS_MODEL.addConstr(X['HW-T*', day_num] == X['T*-W', day_num])
    FLIGHTS_MODEL.addConstr(X['HW-M*', day_num] == X['M*-W', day_num])


## Haviva part added for capacity constraints
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
            operating_cost = cost * n[arc, day_num] # cost = overall of landing, fuel and AIF
            FLIGHTS_MODEL.addConstr(
                operating_cost <= ticket_price * X[arc, day_num],
                name="profit_" + arc + "_" + str(day_num)
            )


# Enough planes
for day_num in range(0,5):
    for c in cities:
        out_flights = 0
        in_flights = 0
        for arc in arc_set:
            depart = arc.split("-")[0]
            arrive = arc.split("-")[1]
            if ('*' not in depart) and ('t' not in arrive):
                if depart[0] == c:
                    out_flights += n[arc, day_num]
                elif arrive[0] == c:
                    in_flights += n[arc, day_num]
        
        FLIGHTS_MODEL.addConstr(Z[c, day_num] >= out_flights)
        FLIGHTS_MODEL.addConstr(Z[c, day_num] + in_flights - out_flights == Z[c, day_num+1])



# Run the model
FLIGHTS_MODEL.optimize()

# Output
for day_num in range(0, 5):
    print(f"\nDay {day_num}:")
    for arc in arc_set:
        x_value = X[arc, day_num].X
        n_value = n[arc, day_num].X
        if x_value > 0 or n_value > 0:
            print(f"Arc {arc}, Day {day_num}: Passengers = {x_value}, Flights = {n_value}")




