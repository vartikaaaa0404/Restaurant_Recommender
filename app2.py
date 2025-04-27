import streamlit as st
import pandas as pd
import json
import os
import time
import random
import string
import secrets
import hashlib
from PIL import Image

# File paths
DATA_FOLDER = "data/"
DATA_FILES = {
    "BOOKMARK_FILE": os.path.join(DATA_FOLDER, "bookmarked_restaurants.json"),
    "PASSWORDS_FILE": os.path.join(DATA_FOLDER,"user_passwords.json"),
    "USER_PROFILES_FILE": os.path.join(DATA_FOLDER,"user_profiles.json"),
    "REVIEWS_FILE":os.path.join(DATA_FOLDER ,"restaurant_reviews.json")
}

# Load data
user_df = pd.read_csv(os.path.join(DATA_FOLDER, "userprofile.csv"))
restaurant_df = pd.read_csv(os.path.join(DATA_FOLDER, "processed_data.csv"), low_memory=False)

# Initialize session state
def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "show_profile" not in st.session_state:
        st.session_state.show_profile = False
    if "show_user_profile" not in st.session_state:
        st.session_state.show_user_profile = False
    if "show_restaurants" not in st.session_state:
        st.session_state.show_restaurants = False
    if "generated_password" not in st.session_state:
        st.session_state.generated_password = ""

# File operations
def init_files():
    # Initialize json files if they don't exist
    for file_key, file_path in DATA_FILES.items():
        if not os.path.exists(file_path):
            initial_data = {}
            
            # Special handling for default user data
            if file_key == "PASSWORDS_FILE":
                for user_id in user_df['userID'].values:
                    initial_data[user_id] = hashlib.sha256(user_id.encode()).hexdigest()
            elif file_key == "USER_PROFILES_FILE":
                for user_id in user_df['userID'].values:
                    initial_data[user_id] = {
                        "full_name": "", "email": "", "phone": "", "address": ""
                    }
            
            with open(file_path, "w") as f:
                json.dump(initial_data, f)

def load_data(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def save_data(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f)

# Helper functions
def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
    return ''.join(secrets.choice(alphabet) for i in range(length))

def display_star_rating(rating):
    full_stars = int(rating)
    half_star = rating - full_stars >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    stars_html = '<div style="font-size: 24px; color: #FFD700;">'
    stars_html += "★" * full_stars
    if half_star:
        stars_html += "⯨"
    stars_html += "☆" * empty_stars
    stars_html += f' <span style="font-size: 14px; color: #555;">({rating:.1f})</span></div>'
    
    return stars_html

def is_open_in_time_slot(hours_str, time_range):
    if pd.isna(hours_str):
        return False
    for part in str(hours_str).split(';'):
        part = part.strip()
        if not part:
            continue
        try:
            open_time, close_time = part.split('-')
            open_hour = int(open_time.split(':')[0])
            close_hour = int(close_time.split(':')[0])
            # Handle overnight (close_hour < open_hour)
            if close_hour < open_hour:
                close_hour += 24
            # Check for overlap
            slot_start, slot_end = time_range
            for h in range(open_hour, close_hour):
                if slot_start <= h < slot_end:
                    return True
        except Exception:
            continue
    return False

# User management functions
def get_user_reviews(username):
    reviews = load_data(DATA_FILES["REVIEWS_FILE"])
    return reviews.get(username, {})

def save_user_review(username, restaurant_name, review_text, rating):
    reviews = load_data(DATA_FILES["REVIEWS_FILE"])
    if username not in reviews:
        reviews[username] = {}
    
    reviews[username][restaurant_name] = {
        "text": review_text,
        "rating": rating,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_data(reviews, DATA_FILES["REVIEWS_FILE"])

# UI Components
def welcome_screen():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #ffebee;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("## 🔐 User Login")
        username_input = st.text_input("Enter your User ID")
        password_input = st.text_input("Enter Password", type="password")
        
        login_col1, login_col2 = st.columns(2)
        with login_col1:
            if st.button("Login"):
                if username_input in user_df['userID'].values:
                    passwords = load_data(DATA_FILES["PASSWORDS_FILE"])
                    hashed_input = hashlib.sha256(password_input.encode()).hexdigest()
                    
                    if hashed_input == passwords.get(username_input, ""):
                        st.session_state.logged_in = True
                        st.session_state.username = username_input
                        st.session_state.show_profile = False
                        st.session_state.show_restaurants = False
                        st.success(f"Welcome back, {username_input}!")
                    else:
                        st.error("Incorrect password.")
                else:
                    st.error("Username not found.")
        
        with login_col2:
            if st.button("Continue as Guest"):
                st.session_state.logged_in = True
                st.session_state.username = "Guest"
                st.session_state.show_profile = False
                st.session_state.show_restaurants = False
                
        # Password generation
        st.markdown("### 🔑 Need a password?")
        password_length = st.slider("Password Length", 8, 20, 12)
        if st.button("Generate Secure Password"):
            st.session_state.generated_password = generate_password(password_length)
            
        if st.session_state.generated_password:
            st.code(st.session_state.generated_password)
            st.markdown("Copy this password and keep it secure!")

    with col2:
        st.markdown("""
        <h1 style='font-size: 3em;'>🍽️ Restaurant Recommender</h1>
        <p style='font-size: 1.2em;'>Discover food you love, effortlessly. Login from the sidebar to get personalized suggestions.</p>
        """, unsafe_allow_html=True)

        # Display random restaurant images
        display_random_restaurant_images()

def display_random_restaurant_images():
    image_folder = "restaurant_images"
    if os.path.exists(image_folder):
        cuisine_folders = [f for f in os.listdir(image_folder) if os.path.isdir(os.path.join(image_folder, f))]
        
        if cuisine_folders:
            grid1, grid2 = st.columns(2)
            cols = [grid1, grid2, grid1, grid2]
            
            for i in range(4):
                with cols[i]:
                    cuisine = random.choice(cuisine_folders)
                    cuisine_path = os.path.join(image_folder, cuisine)
                    image_files = [f for f in os.listdir(cuisine_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                    if image_files:
                        img_path = os.path.join(cuisine_path, random.choice(image_files))
                        st.image(Image.open(img_path), use_container_width=True)

def display_user_profile():
    user_data = user_df[user_df['userID'] == st.session_state.username].iloc[0]
    
    profile_tab, account_tab, bookmarks_tab, visited_tab = st.tabs(["📋 Profile", "🔒 Account Settings", "🔖 Bookmarks", "🗺️ Places Visited"])
    
    # Profile Tab
    with profile_tab:
        st.header(f"👤 {st.session_state.username}'s Profile")
        
        profiles = load_data(DATA_FILES["USER_PROFILES_FILE"])
        user_profile = profiles.get(st.session_state.username, {
            "full_name": "", "email": "", "phone": "", "address": ""
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Information")
            # Display user data
            for field in ['birth_year', 'marital_status', 'interest', 'personality', 'smoker', 'drink_level']:
                if field in user_data:
                    st.markdown(f"**{field.replace('_', ' ').title()}:** {user_data[field]}")
            
            # Edit profile form
            st.subheader("Edit Additional Details")
            with st.form("profile_form"):
                full_name = st.text_input("Full Name", value=user_profile.get("full_name", ""))
                email = st.text_input("Email Address", value=user_profile.get("email", ""))
                phone = st.text_input("Phone Number", value=user_profile.get("phone", ""))
                address = st.text_area("Address", value=user_profile.get("address", ""))
                
                if st.form_submit_button("Save Profile Changes"):
                    profiles[st.session_state.username] = {
                        "full_name": full_name, "email": email, 
                        "phone": phone, "address": address
                    }
                    save_data(profiles, DATA_FILES["USER_PROFILES_FILE"])
                    st.success("Profile updated successfully!")
        
        with col2:
            st.subheader("Food Preferences")
            for field in ['dress_preference', 'ambience', 'transport', 'hijos']:
                if field in user_data:
                    st.markdown(f"**{field.replace('_', ' ').title()}:** {user_data[field]}")
    
    # Account Settings Tab
    with account_tab:
        display_account_settings()
    
    # Bookmarks Tab
    with bookmarks_tab:
        display_bookmarks()
    
    # Places Visited Tab
    with visited_tab:
        display_visited_places(user_data)

def display_account_settings():
    st.header("🔒 Account Settings")
    
    # Password change section
    st.subheader("Change Password")
    
    with st.form("password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        # Password generation option
        if st.checkbox("Generate a secure password instead"):
            password_length = st.slider("Password Length", 8, 20, 12)
            if st.button("Generate Password"):
                new_generated_password = generate_password(password_length)
                st.code(new_generated_password)
                st.markdown("Copy this password and use it as your new password below.")
        
        if st.form_submit_button("Update Password"):
            # Validate password change
            passwords = load_data(DATA_FILES["PASSWORDS_FILE"])
            hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
            
            if hashed_current != passwords.get(st.session_state.username, ""):
                st.error("Current password is incorrect.")
            elif new_password != confirm_password:
                st.error("New passwords don't match.")
            elif len(new_password) < 8:
                st.error("New password must be at least 8 characters long.")
            else:
                # Update password
                hashed_new = hashlib.sha256(new_password.encode()).hexdigest()
                passwords[st.session_state.username] = hashed_new
                save_data(passwords, DATA_FILES["PASSWORDS_FILE"])
                st.success("Password changed successfully!")

def display_bookmarks():
    st.header("🔖 Your Bookmarked Restaurants")
    
    bookmarks = load_data(DATA_FILES["BOOKMARK_FILE"])
    user_bookmarks = bookmarks.get(st.session_state.username, [])
    
    if not user_bookmarks:
        st.info("You haven't bookmarked any restaurants yet.")
        return
    
    # Display bookmarks in a grid
    bookmark_cols = st.columns(3)
    
    for i, name in enumerate(user_bookmarks):
        with bookmark_cols[i % 3]:
            restaurant = restaurant_df[restaurant_df['name'] == name]
            if not restaurant.empty:
                row = restaurant.iloc[0]
                st.markdown(f"### {name}")
                st.markdown(f"**Cuisine:** {row['Rcuisine_x']}")
                st.markdown(display_star_rating(row['avg_rating']), unsafe_allow_html=True)
                st.markdown(f"**Group Friendly:** {row['group_friendly_score']:.2f}")
                st.markdown(f"**Distance:** {row['distance_km']} km")
                st.markdown(f"[📍 View on Map](https://www.google.com/maps/search/?api=1&query={row['rest_latitude']},{row['rest_longitude']})")
                
                # Use name as part of the key for uniqueness
                if st.button(f"❌ Remove", key=f"remove_bookmark_{name}_{i}"):
                    user_bookmarks.remove(name)
                    bookmarks[st.session_state.username] = user_bookmarks
                    save_data(bookmarks, DATA_FILES["BOOKMARK_FILE"])
                    st.success(f"Removed {name} from bookmarks!")
                    st.experimental_rerun()
            else:
                st.markdown(f"### {name}")
                st.markdown(f"*Restaurant details not available*")
            
            st.markdown("---")

def display_visited_places(user_data):
    st.header("🗺️ Your Location & Places")
    
    # Location information
    if 'latitude' in user_data and 'longitude' in user_data:
        st.subheader("Your Location")
        st.markdown(f"**Latitude:** {user_data['latitude']}")
        st.markdown(f"**Longitude:** {user_data['longitude']}")
        
        # Display map
        map_data = pd.DataFrame({
            'lat': [user_data['latitude']],
            'lon': [user_data['longitude']]
        })
        st.map(map_data)
        
        # Show nearby restaurants
        st.subheader("Restaurants Near You")
        nearby = restaurant_df[restaurant_df['distance_km'] < 5].head(5)
        
        if not nearby.empty:
            for idx, row in nearby.iterrows():
                st.markdown(f"### {row['name']} ({row['distance_km']:.1f} km)")
                st.markdown(f"**Cuisine:** {row['Rcuisine_x']}")
                st.markdown(display_star_rating(row['avg_rating']), unsafe_allow_html=True)
                st.markdown(f"[📍 View on Map](https://www.google.com/maps/search/?api=1&query={row['rest_latitude']},{row['rest_longitude']})")
                st.markdown("---")
        else:
            st.info("No restaurants found near your location.")
    else:
        st.info("Location information not available.")

def display_restaurant_recommendations(filters):
    filtered = restaurant_df.copy()

    # Apply cuisine filter
    if filters["cuisine"] != "Any":
        filtered = filtered[filtered['Rcuisine_x'] == filters["cuisine"]]

    # Apply other filters
    filtered = filtered[filtered['group_friendly_score'] >= filters["group_score"]]
    filtered = filtered[filtered['distance_km'] <= filters["distance"]]
    filtered = filtered[filtered['avg_rating'] >= filters["min_rating"]]

    # Apply day filter
    if filters["day"] != "Any":
        day_column = filters["days_options"][filters["day"]]
        if day_column in filtered.columns:
            filtered = filtered[filtered[day_column] == 1]

    # Apply time filter
    if filters["time_slot"] != "Any":
        filtered = filtered[filtered['hours'].apply(lambda x: is_open_in_time_slot(x, filters["time_slots"][filters["time_slot"]]))]

    # Get top recommendations
    filtered = filtered.sort_values('avg_rating', ascending=False).head(filters["num_recs"])

    bookmarks = load_data(DATA_FILES["BOOKMARK_FILE"])
    user_bookmarks = bookmarks.get(st.session_state.username, [])

    if filtered.empty:
        st.warning("No restaurants match your criteria. Please try adjusting your filters.")
        return
    
    st.subheader("🍽️ Recommended Restaurants")
    
    # Display restaurants in 2 columns
    col1, col2 = st.columns(2)
    
    for i, row in enumerate(filtered.to_dict('records')):
        with col1 if i % 2 == 0 else col2:
            display_restaurant_card(row, user_bookmarks, i)

def display_restaurant_card(row, user_bookmarks, index):
    with st.container():
        st.markdown(f"### {row['name']} ({row['Rcuisine_x']})")
        
        # Find cuisine images
        first_cuisine = str(row['Rcuisine_x']).split(';')[0].strip().lower()
        cuisine_folder = os.path.join("restaurant_images", first_cuisine)
        
        if os.path.exists(cuisine_folder):
            image_files = [f for f in os.listdir(cuisine_folder) if f.endswith(('.jpg', '.png', '.jpeg'))]
            if image_files:
                selected_images = random.sample(image_files, min(2, len(image_files)))
                img_cols = st.columns(len(selected_images))
                
                for j, image in enumerate(selected_images):
                    image_path = os.path.join(cuisine_folder, image)
                    img_cols[j].image(image_path, use_container_width=True)
            else:
                st.image("https://via.placeholder.com/300x200.png?text=No+Image", caption="No images available", use_container_width=True)
        else:
            st.image("https://via.placeholder.com/300x200.png?text=No+Image", caption="Cuisine folder not found", use_container_width=True)
        
        # Restaurant details
        details_col1, details_col2 = st.columns(2)
        
        with details_col1:
            st.markdown(f"**Cuisine:** {row['Rcuisine_x']}")
            st.markdown(display_star_rating(row['avg_rating']), unsafe_allow_html=True)
        
        with details_col2:
            st.markdown(f"**Group Friendly:** {row['group_friendly_score']:.2f}")
            st.markdown(f"**Distance:** {row['distance_km']} km")
            
        st.markdown(f"[📍 View on Map](https://www.google.com/maps/search/?api=1&query={row['rest_latitude']},{row['rest_longitude']})")

        # Review section
        st.markdown("### 📝 Your Review")
        user_reviews = get_user_reviews(st.session_state.username)
        existing_review = user_reviews.get(row['name'], {})
        
        # Create a unique key for each form using restaurant name and index
        unique_form_key = f"review_form_{row['name']}_{index}_{random.randint(0, 10000)}"
        with st.form(unique_form_key):
            review_text = st.text_area("Write your review", value=existing_review.get("text", ""))
            review_rating = st.slider("Your Rating", 1.0, 5.0, float(existing_review.get("rating", 3.0)), 0.5)
            
            if st.form_submit_button("Save Review"):
                if review_text.strip():
                    save_user_review(st.session_state.username, row['name'], review_text, review_rating)
                    st.success("Review saved successfully!")
                else:
                    st.warning("Please write a review before saving.")
        
        # Display existing review
        if existing_review:
            st.markdown("#### Your Previous Review")
            st.markdown(display_star_rating(existing_review["rating"]), unsafe_allow_html=True)
            st.markdown(f"*{existing_review['text']}*")
            st.markdown(f"*Posted on: {existing_review['timestamp']}*")

        # Bookmark button with unique key
        button_key = f"bookmark_{row['name']}_{index}_{random.randint(0, 10000)}"
        
        if row['name'] not in user_bookmarks:
            if st.button(f"🔖 Bookmark", key=button_key):
                user_bookmarks.append(row['name'])
                bookmarks = load_data(DATA_FILES["BOOKMARK_FILE"])
                bookmarks[st.session_state.username] = user_bookmarks
                save_data(bookmarks, DATA_FILES["BOOKMARK_FILE"])
                st.success(f"Bookmarked {row['name']}!")
        else:
            st.info("✅ Already Bookmarked")
        
        st.markdown("---")

def sidebar_filters():
    st.sidebar.markdown("## 🍒 Options")
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.show_profile = False
        st.session_state.show_user_profile = False
        st.session_state.show_restaurants = False
    
    # Show bookmarks count for non-guest users
    if st.session_state.username != "Guest":
        st.sidebar.markdown("---")
        
        bookmarks = load_data(DATA_FILES["BOOKMARK_FILE"])
        user_bookmarks = bookmarks.get(st.session_state.username, [])
        
        if user_bookmarks:
            st.sidebar.markdown(f"### 🔖 {len(user_bookmarks)} Bookmarked Restaurants")
            if st.sidebar.button("View My Bookmarks"):
                st.session_state.show_user_profile = True
                st.session_state.show_restaurants = False
        else:
            st.sidebar.markdown("### 🔖 No Bookmarks Yet")
        
        st.sidebar.markdown("---")

    # Filter options
    st.sidebar.markdown("## 🔍 Filter Options")
    
    # Define filter options
    days_options = {
        "Any": None,
        "Weekday (Mon-Fri)": "days_Mon;Tue;Wed;Thu;Fri;",
        "Saturday": "days_Sat;",
        "Sunday": "days_Sun;"
    }
    
    time_slots = {
        "Any": None,
        "Morning (06:00-12:00)": (6, 12),
        "Afternoon (12:00-18:00)": (12, 18),
        "Evening (18:00-24:00)": (18, 24)
    }
    
    # Collect filters
    filters = {
        "cuisine": st.sidebar.selectbox("Preferred Cuisine", ["Any"] + sorted(restaurant_df['Rcuisine_x'].dropna().unique())),
        "distance": st.sidebar.slider("Maximum Distance (km)", 1, 50, 10),
        "group_score": st.sidebar.slider("Minimum Group Friendliness", 0.0, 1.0, 0.5),
        "min_rating": st.sidebar.slider("Minimum Average Rating", 1.0, 5.0, 3.0, 0.5),
        "day": st.sidebar.selectbox("Preferred Day to Visit", list(days_options.keys())),
        "time_slot": st.sidebar.selectbox("Preferred Time Slot", list(time_slots.keys())),
        "num_recs": st.sidebar.slider("Number of Recommendations", 1, 20, 10),
        "days_options": days_options,
        "time_slots": time_slots
    }
    
    if st.sidebar.button("Find Restaurants"):
        st.session_state.show_restaurants = True
        st.session_state.show_user_profile = False
        
    return filters

def main():
    # Initialize files and session state
    init_files()
    init_session_state()
    
    # Set page config for a wider layout
    st.set_page_config(layout="wide", page_title="Restaurant Recommender")
    
    # Login screen
    if not st.session_state.logged_in:
        welcome_screen()
        return
    
    # Header section
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.title("Restaurant Recommendation System")
        st.markdown("Use the filters below to find the perfect restaurant for your next meal. 🍜🍕")
    
    with header_col2:
        if st.session_state.username != "Guest":
            # User profile button
            user_button_style = """
            <style>
            .user-button {
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #f0f2f6;
                border-radius: 8px;
                padding: 10px;
                margin-top: 20px;
                cursor: pointer;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }
            .user-button:hover {
                background-color: #e0e2e6;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .user-icon {
                font-size: 24px;
                margin-right: 8px;
            }
            .user-name {
                font-weight: bold;
            }
            </style>
            """
            st.markdown(user_button_style, unsafe_allow_html=True)
            
            user_button_html = f"""
            <div class="user-button" onclick="document.getElementById('user-profile-button').click()">
                <div class="user-icon">👤</div>
                <div class="user-name">{st.session_state.username}</div>
            </div>
            """
            st.markdown(user_button_html, unsafe_allow_html=True)
            
            if st.button("View Profile", key="user-profile-button", help="View your profile details"):
                st.session_state.show_user_profile = not st.session_state.show_user_profile
                st.session_state.show_restaurants = False
    
    st.info(f"👋 Logged in as {st.session_state.username}")

    # Sidebar filters
    filters = sidebar_filters()

    # Main content area
    if st.session_state.username != "Guest" and st.session_state.show_user_profile:
        display_user_profile()
    elif st.session_state.show_restaurants:
        display_restaurant_recommendations(filters)

if __name__ == "__main__":
    main()