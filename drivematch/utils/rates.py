from decimal import Decimal


def calculate_fare(base_fare, cost_per_km, cost_per_minute, service_fee, distance_km, time_min, surge_multiplier=None):
    initial_fare = base_fare + (cost_per_km * distance_km) + (cost_per_minute * time_min)
    total_fare = initial_fare + service_fee
    if surge_multiplier:
        total_fare = initial_fare * surge_multiplier + service_fee

    return Decimal(total_fare)


def calculate_percent(value):
    percentage = Decimal(20 / 100)
    result = value * percentage

    return Decimal(result)
