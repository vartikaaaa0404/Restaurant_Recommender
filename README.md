# Restaurant Recommender System

## Overview
The Restaurant Recommender System is a Streamlit web application that provides personalized restaurant recommendations based on user preferences, location, and filtering criteria. The system uses machine learning techniques to recommend restaurants that match users' tastes while considering factors like cuisine, distance, group-friendliness, and availability.

## Features

### User Management
- User authentication system with secure password hashing
- User profile management
- Password generation and reset functionality

### Restaurant Discovery
- Customizable filtering by cuisine, distance, group-friendliness, rating, day, and time
- Smart recommendations based on user preferences and past ratings
- Location-based restaurant search

### Personalization
- Bookmark favorite restaurants for quick access
- Write and save reviews for visited restaurants
- Personalized recommendations based on user history

### User Interface
- Responsive layout with intuitive navigation
- Interactive maps for location visualization
- Restaurant cards with images, ratings, and details

## Technical Implementation

### Machine Learning
- DBSCAN clustering for location-based grouping
- Cosine similarity for content-based recommendations
- Feature engineering for restaurant attributes
- Personalization based on user history

### Data Management
- User profiles stored in JSON
- Restaurant data stored in CSV format
- Secure password management with SHA-256 hashing
- Review and bookmark persistence

### Application Structure
- Streamlit web interface
- Modular Python code organization
- Responsive UI components
- Secure data handling

## Setup 
### Prerequisites
- Python 3.7+
- Streamlit
- Pandas
- Scikit-learn
- PIL (Python Imaging Library)
- Other dependencies in requirements.txt

## Data Files
- `processed_data.csv`: Contains restaurant information with features
- `userprofile.csv`: Contains user demographic information
- `bookmarked_restaurants.json`: Stores user bookmarks
- `user_passwords.json`: Stores hashed user passwords
- `user_profiles.json`: Stores additional user profile information
- `restaurant_reviews.json`: Stores user reviews for restaurants

## Code Structure
- `app2.py`: Main Streamlit application
- `recommender.py`: Contains recommendation algorithm implementation
- Data files and image folders for UI elements

## Usage
### User Login
- Enter your User ID and password
- Options to generate secure passwords
- Continue as guest functionality

### Finding Restaurants
1. Use sidebar filters to specify preferences:
   - Cuisine type
   - Maximum distance
   - Minimum group friendliness score
   - Minimum rating
   - Preferred day and time
   - Number of recommendations
2. Click "Find Restaurants" to see personalized recommendations

### Managing Profile
- Update personal information
- Change password securely
- View and manage bookmarked restaurants
- See places near your location

### Interacting with Recommendations
- View detailed restaurant information
- Write and save reviews
- Bookmark favorite places
- View locations on map

## Future Enhancements
- Collaborative filtering implementation
- Social features (friend recommendations)
- Mobile app version
- Integration with food delivery services
- Enhanced visualization of restaurant data

## License
[Your License Information]

## Contributors
VARTIKA RAWAT , VAANI TYAGI , KUNAL SHARMA

## Acknowledgments
- Data sources - https://www.kaggle.com/datasets/uciml/restaurant-data-with-consumer-ratings
- Libraries and frameworks used
**  Core Frameworks:**
-Streamlit: The main web application framework used to build the interactive UI
-Pandas: Used for data manipulation and analysis

**Machine Learning Libraries:**
Scikit-learn: Used for various machine learning components including:
 -StandardScaler, MinMaxScaler for feature scaling
 -OneHotEncoder for categorical data encoding
 -MultiLabelBinarizer for multi-label feature encoding
 -DBSCAN for location clustering
 -Cosine similarity calculation for recommendation algorithm

**Data Processing & Visualization:**
-NumPy: For numerical computations
-PIL (Python Imaging Library): For handling images in the application

**Security & Cryptography:**
-Hashlib: For password hashing using SHA-256
-Secrets: For secure password generation

**Standard Python Libraries:**
-JSON: For data storage and retrieval
-OS: For file operations
-Time: For timestamp generation
-Random: For generating random elements and selections
-String: For string operations, especially in password generation
-Itertools (chain): For flattening lists in cuisine processing
