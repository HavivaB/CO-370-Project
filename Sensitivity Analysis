import gurobipy as gp
from gurobipy import GRB

def sensitivity_analysis_fuel_costs(model, fuel_price_range):

    results = {}

    for city, price_list in fuel_price_range.items():
        results[city] = []

        for price in price_list:
            # Update fuel price for the city
            fuel_prices[city] = price

            # Recalculate fuel costs in the objective function
            obj_fn = 0
            for day_num in range(0, 5):
                for arc in arc_set:
                    depart = arc.split("-")[0][0]
                    arrive = arc.split("-")[1][0]

                    if arrive != "t":  # Only consider valid arcs with costs
                        revenue = revenues_matrix[table_index[depart]][table_index[arrive]] * X[arc, day_num]
                        fuel_cost = calculate_fuel_cost(arc) * n[arc, day_num]  # Recalculate fuel cost
                        landing_cost = get_landing_fee(arc) * n[arc, day_num]  # Landing cost per flight
                        aif_cost = get_aif(arc) * X[arc, day_num]  # AIF per passenger
                        cost = fuel_cost + landing_cost + aif_cost  # Total cost
                        obj_fn += revenue - cost

            # Update the model objective
            model.setObjective(obj_fn, GRB.MAXIMIZE)

            # Optimize the model with updated fuel prices
            model.optimize()

            # Check if the model solved successfully
            if model.status == GRB.OPTIMAL:
                results[city].append({
                    "Fuel Price": price,
                    "Profit": model.ObjVal
                })
            else:
                results[city].append({
                    "Fuel Price": price,
                    "Profit": None  
                })

    return results


# Range of fuel prices for sensitivity analysis
fuel_price_range = {
    'H': [1.00, 1.10, 1.28, 1.50],  # Example fuel price variations for Halifax
    'M': [1.00, 1.10, 1.17, 1.50],  # Example for Montreal
    'T': [1.00, 1.10, 1.29, 1.50],  # Example for Toronto
    'W': [1.00, 1.10, 1.19, 1.50],  # Example for Winnipeg
    'V': [1.00, 1.10, 1.30, 1.50],  # Example for Vancouver
}

# Conduct sensitivity analysis
fuel_sensitivity_results = sensitivity_analysis_fuel_costs(FLIGHTS_MODEL, fuel_price_range)

# Output the results
for city, results in fuel_sensitivity_results.items():
    print(f"\nSensitivity Analysis for {city} (Fuel Prices):")
    for result in results:
        fuel_price = result["Fuel Price"]
        profit = result["Profit"]
        print(f"Fuel Price: {fuel_price:.2f}, Profit: {profit if profit is not None else 'Infeasible'}")
