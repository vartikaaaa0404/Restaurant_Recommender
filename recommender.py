import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder, MinMaxScaler, MultiLabelBinarizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from itertools import chain

# Load the preprocessed data
data = pd.read_csv('processed_data.csv', low_memory=False, dtype={'column_name': str})

# DBSCAN Clustering for location
location_data = data[['rest_latitude', 'rest_longitude']].dropna()
scaler = StandardScaler()
location_scaled = scaler.fit_transform(location_data)
db = DBSCAN(eps=0.5, min_samples=5).fit(location_scaled)
data['location_cluster'] = -1
data.loc[location_data.index, 'location_cluster'] = db.labels_

# Handle cuisine as multilabel and clean duplicates
data['combined_cuisine'] = data['Rcuisine_x'].fillna('') + ';' + data['Rcuisine_y'].fillna('')
data['combined_cuisine'] = data['combined_cuisine'].apply(
    lambda x: list(set(i.strip().lower() for i in x.split(';') if i.strip()))
)

mlb = MultiLabelBinarizer()
cuisine_encoded = pd.DataFrame(mlb.fit_transform(data['combined_cuisine']), columns=mlb.classes_)

# Extract all available cuisines
available_cuisines = sorted(set(chain.from_iterable(data['combined_cuisine'])))

# Encode categorical variables
categorical_features = [
    'alcohol', 'smoking_area', 'dress_code', 'accessibility', 'price',
    'Rambience', 'franchise', 'area', 'other_services'
]
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
encoded_cats = pd.DataFrame(
    encoder.fit_transform(data[categorical_features]),
    columns=encoder.get_feature_names_out(categorical_features)
)

# Scale numerical features
numerical_features = [
    'distance_km', 'popularity_score_scaled', 'food_rating_scaled',
    'service_rating_scaled', 'trending_score', 'group_friendly_score', 'avg_rating'
]
scaler2 = MinMaxScaler()
scaled_numerics = pd.DataFrame(
    scaler2.fit_transform(data[numerical_features]),
    columns=numerical_features
)

# Content-based feature matrix and cosine similarity
content_features_matrix = pd.concat([cuisine_encoded, encoded_cats, scaled_numerics], axis=1)
cosine_sim_matrix = cosine_similarity(content_features_matrix)
data = data.reset_index(drop=True)

def get_soft_filtered_recommendations(
    user_id,
    cuisine=None,
    max_distance=10,
    min_group_score=0.5,
    days=None,           # <-- now a list of day codes, e.g. ['mon','fri']
    top_n=10
):
    """
    Personalized recommendations for a user with optional cuisine, distance,
    group friendliness, and a list of days when they want to visit.
    """
    if user_id not in data['userID'].values:
        return pd.DataFrame({'error': [f"User ID {user_id} not found."]})

    # Base similarity on the user's top-rated place
    user_history = data[data['userID'] == user_id]
    top_place_id = user_history.sort_values('rating', ascending=False).iloc[0]['placeID']
    idx = data[data['placeID'] == top_place_id].index[0]
    sim_scores = list(enumerate(cosine_sim_matrix[idx]))

    def calculate_score(row):
        score = sim_scores[row.name][1]
        # cuisine preference
        if cuisine and cuisine.lower() in row['combined_cuisine']:
            score += 0.1
        # distance
        if row['distance_km'] <= max_distance:
            score += 0.1
        else:
            score -= 0.05
        # group friendliness
        if row['group_friendly_score'] >= min_group_score:
            score += 0.1
        # day availability bonus if any selected day matches
        if days:
            for d in days:
                col = f"days_{d.capitalize()}"
                if col in row and row[col] == 1:
                    score += 0.1
                    break
        return score

    data['matching_score'] = data.apply(calculate_score, axis=1)
    top_recs = data.sort_values('matching_score', ascending=False).head(top_n)

    return top_recs[[
        'placeID','name','Rcuisine_x','distance_km','group_friendly_score',
        'matching_score','avg_rating','rest_latitude','rest_longitude'
    ]]

__all__ = ['get_soft_filtered_recommendations', 'available_cuisines']
