# Configuration parameters

BASE_PRICE = 10.0
MIN_PRICE = 5.0
MAX_PRICE = 20.0

# Model 1 parameters
ALPHA = 0.1

# Model 2 parameters
MODEL2_PARAMS = {
    'alpha': 0.6,
    'beta': 0.3,
    'gamma': 0.2,
    'delta': 0.4,
    'epsilon': 0.1,
    'lambda_': 0.2
}

# Model 3 parameters
NEARBY_LOTS_K = 3  # Number of nearby competitors to consider

# Vehicle type weights
VEHICLE_WEIGHTS = {
    'car': 1.0,
    'bike': 0.8,
    'truck': 1.2
}

# Geospatial parameters
EARTH_RADIUS_KM = 6371.0
MAX_DISTANCE_KM = 2.0  # Consider competitors within 2km radius
