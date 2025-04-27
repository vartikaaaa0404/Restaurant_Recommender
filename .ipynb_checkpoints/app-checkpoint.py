import streamlit as st
import pandas as pd
import json
import os
import pydeck as pdk
import time
from PIL import Image
import random
import string
import secrets
import hashlib

# Load user and restaurant data
user_df = pd.read_csv("userprofile.csv")
# Fix the DtypeWarning by specifying low_memory=False
restaurant_df = pd.read_csv("processed_data.csv", low_memory=False)

# Placeholder for bookmarks
BOOKMARK_FILE = "bookmarked_restaurants.json"
if not os.path.exists(BOOKMARK_FILE):
    with open(BOOKMARK_FILE, "w") as f:
        json.dump({}, f)

# Placeholder for user passwords
PASSWORDS_FILE = "user_passwords.json"
if not os.path.exists(PASSWORDS_FILE):
    # Initialize with default password for each user (hashed)
    passwords = {}
    for user_id in user_df['userID'].values:
        # By default, use userID as password but store it as a hash
        passwords[user_id] = hashlib.sha256(user_id.encode()).hexdigest()
    
    with open(PASSWORDS_FILE, "w") as f:
        json.dump(passwords, f)

# User profile data storage
USER_PROFILES_FILE = "user_profiles.json"
if not os.path.exists(USER_PROFILES_FILE):
    # Initialize with empty profiles
    profiles = {}
    for user_id in user_df['userID'].values:
        profiles[user_id] = {
            "full_name": "",
            "email": "",
            "phone": "",
            "address": ""
        }
    
    with open(USER_PROFILES_FILE, "w") as f:
        json.dump(profiles, f)

def load_bookmarks():
    with open(BOOKMARK_FILE, "r") as f:
        return json.load(f)

def save_bookmarks(bookmarks):
    with open(BOOKMARK_FILE, "w") as f:
        json.dump(bookmarks, f)

def load_passwords():
    with open(PASSWORDS_FILE, "r") as f:
        return json.load(f)

def save_passwords(passwords):
    with open(PASSWORDS_FILE, "w") as f:
        json.dump(passwords, f)

def load_profiles():
    with open(USER_PROFILES_FILE, "r") as f:
        return json.load(f)

def save_profiles(profiles):
    with open(USER_PROFILES_FILE, "w") as f:
        json.dump(profiles, f)

# Function to generate a secure password
def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

# Function to display star rating
def display_star_rating(rating):
    full_stars = int(rating)
    half_star = rating - full_stars >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)
    
    stars_html = """
    <div style="font-size: 24px; color: #FFD700;">
    """
    # Add full stars
    stars_html += "★" * full_stars
    # Add half star if needed
    if half_star:
        stars_html += "⯨"
    # Add empty stars
    stars_html += "☆" * empty_stars
    stars_html += f" <span style='font-size: 14px; color: #555;'>({rating:.1f})</span></div>"
    
    return stars_html

# App state
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

# Set page config for a wider layout
st.set_page_config(layout="wide", page_title="Restaurant Recommender")

# Custom welcome screen with pink background
if not st.session_state.logged_in:
    # Add CSS to set background color for the welcome page
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
                    # Get passwords
                    passwords = load_passwords()
                    hashed_input = hashlib.sha256(password_input.encode()).hexdigest()
                    
                    # Check if password hash matches
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
                
        # Add password generation feature
        st.markdown("### 🔑 Need a password?")
        password_length = st.slider("Password Length", 8, 20, 12)
        if st.button("Generate Secure Password"):
            st.session_state.generated_password = generate_password(password_length)
            
        # Display generated password if available
        if st.session_state.generated_password:
            st.code(st.session_state.generated_password)
            st.markdown("Copy this password and keep it secure!")

    with col2:
        st.markdown("""
        <h1 style='font-size: 3em;'>🍽️ Restaurant Recommender</h1>
        <p style='font-size: 1.2em;'>Discover food you love, effortlessly. Login from the sidebar to get personalized suggestions.</p>
        """, unsafe_allow_html=True)

        # Display cycling images
        image_folder = "restaurant_images"
        if os.path.exists(image_folder):
            # Find all cuisine folders
            cuisine_folders = [f for f in os.listdir(image_folder) if os.path.isdir(os.path.join(image_folder, f))]
            
            if cuisine_folders:
                # Create a 2x2 grid for images
                grid1, grid2 = st.columns(2)
                
                # Display first row of images
                with grid1:
                    # Select a random cuisine and image from that cuisine
                    cuisine = random.choice(cuisine_folders)
                    cuisine_path = os.path.join(image_folder, cuisine)
                    image_files = [f for f in os.listdir(cuisine_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                    if image_files:
                        img_path = os.path.join(cuisine_path, random.choice(image_files))
                        st.image(Image.open(img_path), use_container_width=True)
                
                with grid2:
                    # Select another random cuisine and image
                    cuisine = random.choice(cuisine_folders)
                    cuisine_path = os.path.join(image_folder, cuisine)
                    image_files = [f for f in os.listdir(cuisine_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                    if image_files:
                        img_path = os.path.join(cuisine_path, random.choice(image_files))
                        st.image(Image.open(img_path), use_container_width=True)
                
                # Display second row of images
                with grid1:
                    # Select a random cuisine and image
                    cuisine = random.choice(cuisine_folders)
                    cuisine_path = os.path.join(image_folder, cuisine)
                    image_files = [f for f in os.listdir(cuisine_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                    if image_files:
                        img_path = os.path.join(cuisine_path, random.choice(image_files))
                        st.image(Image.open(img_path), use_container_width=True)
                
                with grid2:
                    # Select another random cuisine and image
                    cuisine = random.choice(cuisine_folders)
                    cuisine_path = os.path.join(image_folder, cuisine)
                    image_files = [f for f in os.listdir(cuisine_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
                    if image_files:
                        img_path = os.path.join(cuisine_path, random.choice(image_files))
                        st.image(Image.open(img_path), use_container_width=True)
else:
    # Header section with title and user profile button
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.title("Restaurant Recommendation System")
        st.markdown("Use the filters below to find the perfect restaurant for your next meal. 🍜🍕")
    
    with header_col2:
        if st.session_state.username != "Guest":
            # User profile button with icon and username
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
            
            # Hidden button that will be clicked by the JavaScript
            if st.button("View Profile", key="user-profile-button", help="View your profile details"):
                st.session_state.show_user_profile = not st.session_state.show_user_profile
                st.session_state.show_restaurants = False
    
    st.info(f"👋 Logged in as {st.session_state.username}")

    # Set up sidebar
    st.sidebar.markdown("## 🍒 Options")
    
    # Logout button at the top
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.show_profile = False
        st.session_state.show_user_profile = False
        st.session_state.show_restaurants = False
    
    # Add bookmarks count in sidebar for non-guest users
    if st.session_state.username != "Guest":
        # Add a separator
        st.sidebar.markdown("---")
        
        # Show only bookmark count in sidebar
        bookmarks = load_bookmarks()
        user_bookmarks = bookmarks.get(st.session_state.username, [])
        
        if user_bookmarks:
            st.sidebar.markdown(f"### 🔖 {len(user_bookmarks)} Bookmarked Restaurants")
            if st.sidebar.button("View My Bookmarks"):
                st.session_state.show_user_profile = True
                st.session_state.show_restaurants = False
        else:
            st.sidebar.markdown("### 🔖 No Bookmarks Yet")
        
        st.sidebar.markdown("---")

    # Filter options in sidebar with magnifying glass icon
    st.sidebar.markdown("## 🔍 Filter Options")
    cuisine = st.sidebar.selectbox("Preferred Cuisine", ["Any"] + sorted(restaurant_df['Rcuisine_x'].dropna().unique()))
    distance = st.sidebar.slider("Maximum Distance (km)", 1, 50, 10)
    group_score = st.sidebar.slider("Minimum Group Friendliness", 0.0, 1.0, 0.5)
    
    # Add new filter for average rating
    min_rating = st.sidebar.slider("Minimum Average Rating", 1.0, 5.0, 3.0, 0.5)
    
    # Fix day filter - use proper column name based on your dataset
    days_of_week = ["Any", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day = st.sidebar.selectbox("Preferred Day to Visit", days_of_week)
    
    # Fix time slot filter - ensure these exist in your dataset
    time_slots = ["Any", "Morning", "Afternoon", "Evening"]
    time_slot = st.sidebar.selectbox("Preferred Time Slot", time_slots)
    
    num_recs = st.sidebar.slider("Number of Recommendations", 1, 20, 10)

    if st.sidebar.button("Find Restaurants"):
        st.session_state.show_restaurants = True
        st.session_state.show_user_profile = False
    
    # Main content area - User Profile View
    if st.session_state.username != "Guest" and st.session_state.show_user_profile:
        user_data = user_df[user_df['userID'] == st.session_state.username].iloc[0]
        
        # Create tabs for different sections of the user profile
        profile_tab, account_tab, bookmarks_tab, visited_tab = st.tabs(["📋 Profile", "🔒 Account Settings", "🔖 Bookmarks", "🗺️ Places Visited"])
        
        # Profile Tab
        with profile_tab:
            st.header(f"👤 {st.session_state.username}'s Profile")
            
            # Load user profile data
            profiles = load_profiles()
            user_profile = profiles.get(st.session_state.username, {
                "full_name": "",
                "email": "",
                "phone": "",
                "address": ""
            })
            
            # Create columns for a more organized profile display
            col1, col2 = st.columns(2)
            
            # Personal information in first column
            with col1:
                st.subheader("Personal Information")
                # Show existing information from the database
                if 'birth_year' in user_data:
                    st.markdown(f"**Birth Year:** {user_data['birth_year']}")
                if 'marital_status' in user_data:
                    st.markdown(f"**Marital Status:** {user_data['marital_status']}")
                if 'interest' in user_data:
                    st.markdown(f"**Interest:** {user_data['interest']}")
                if 'personality' in user_data:
                    st.markdown(f"**Personality:** {user_data['personality']}")
                if 'smoker' in user_data:
                    st.markdown(f"**Smoker:** {user_data['smoker']}")
                if 'drink_level' in user_data:
                    st.markdown(f"**Drinking Level:** {user_data['drink_level']}")
                
                # Show editable profile information
                st.subheader("Edit Additional Details")
                with st.form("profile_form"):
                    full_name = st.text_input("Full Name", value=user_profile.get("full_name", ""))
                    email = st.text_input("Email Address", value=user_profile.get("email", ""))
                    phone = st.text_input("Phone Number", value=user_profile.get("phone", ""))
                    address = st.text_area("Address", value=user_profile.get("address", ""))
                    
                    if st.form_submit_button("Save Profile Changes"):
                        # Update profile
                        profiles[st.session_state.username] = {
                            "full_name": full_name,
                            "email": email,
                            "phone": phone,
                            "address": address
                        }
                        save_profiles(profiles)
                        st.success("Profile updated successfully!")
            
            # Preferences in second column
            with col2:
                st.subheader("Food Preferences")
                if 'dress_preference' in user_data:
                    st.markdown(f"**Dress Preference:** {user_data['dress_preference']}")
                if 'ambience' in user_data:
                    st.markdown(f"**Preferred Ambience:** {user_data['ambience']}")
                if 'transport' in user_data:
                    st.markdown(f"**Transportation:** {user_data['transport']}")
                if 'hijos' in user_data:
                    st.markdown(f"**Family Status:** {user_data['hijos']}")
        
        # Account Settings Tab
        with account_tab:
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
                    passwords = load_passwords()
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
                        save_passwords(passwords)
                        st.success("Password changed successfully!")
        
        # Bookmarks Tab
        with bookmarks_tab:
            st.header("🔖 Your Bookmarked Restaurants")
            
            bookmarks = load_bookmarks()
            user_bookmarks = bookmarks.get(st.session_state.username, [])
            
            if not user_bookmarks:
                st.info("You haven't bookmarked any restaurants yet.")
            else:
                # Display bookmarks in a grid
                bookmark_cols = st.columns(3)
                
                for i, name in enumerate(user_bookmarks):
                    with bookmark_cols[i % 3]:
                        st.markdown(f"### {name}")
                        # Try to find the restaurant in the dataframe
                        restaurant = restaurant_df[restaurant_df['name'] == name]
                        if not restaurant.empty:
                            row = restaurant.iloc[0]
                            st.markdown(f"**Cuisine:** {row['Rcuisine_x']}")
                            # Display star rating instead of number
                            st.markdown(display_star_rating(row['avg_rating']), unsafe_allow_html=True)
                            st.markdown(f"**Group Friendly:** {row['group_friendly_score']:.2f}")
                            st.markdown(f"**Distance:** {row['distance_km']} km")
                            st.markdown(f"[📍 View on Map](https://www.google.com/maps/search/?api=1&query={row['rest_latitude']},{row['rest_longitude']})")
                            
                            # Option to remove bookmark
                            if st.button(f"❌ Remove", key=f"remove_{name}"):
                                user_bookmarks.remove(name)
                                bookmarks[st.session_state.username] = user_bookmarks
                                save_bookmarks(bookmarks)
                                st.success(f"Removed {name} from bookmarks!")
                                st.experimental_rerun()
                        else:
                            st.markdown(f"*Restaurant details not available*")
                        
                        st.markdown("---")
        
        # Places Visited Tab
        with visited_tab:
            st.header("🗺️ Your Location & Places")
            
            # Location information
            if 'latitude' in user_data and 'longitude' in user_data:
                st.subheader("Your Location")
                st.markdown(f"**Latitude:** {user_data['latitude']}")
                st.markdown(f"**Longitude:** {user_data['longitude']}")
                
                # Display map with user location
                map_data = pd.DataFrame({
                    'lat': [user_data['latitude']],
                    'lon': [user_data['longitude']]
                })
                st.map(map_data)
                
                # Show nearby restaurants (example)
                st.subheader("Restaurants Near You")
                nearby = restaurant_df[restaurant_df['distance_km'] < 5].head(5)
                
                if not nearby.empty:
                    for _, row in nearby.iterrows():
                        st.markdown(f"### {row['name']} ({row['distance_km']:.1f} km)")
                        st.markdown(f"**Cuisine:** {row['Rcuisine_x']}")
                        # Display star rating instead of number
                        st.markdown(display_star_rating(row['avg_rating']), unsafe_allow_html=True)
                        st.markdown(f"[📍 View on Map](https://www.google.com/maps/search/?api=1&query={row['rest_latitude']},{row['rest_longitude']})")
                        st.markdown("---")
                else:
                    st.info("No restaurants found near your location.")
            else:
                st.info("Location information not available.")

    # Show restaurant recommendations when button is clicked
    if st.session_state.show_restaurants:
        filtered = restaurant_df.copy()

        # Apply cuisine filter
        if cuisine != "Any":
            filtered = filtered[filtered['Rcuisine_x'] == cuisine]

        # Apply other filters
        filtered = filtered[filtered['group_friendly_score'] >= group_score]
        filtered = filtered[filtered['distance_km'] <= distance]
        filtered = filtered[filtered['avg_rating'] >= min_rating]  # Apply average rating filter

        # Apply day filter if selected
        if day != "Any":
            day_column = f"days_{day.lower()}"  # Make sure column names match your dataset
            if day_column in filtered.columns:
                filtered = filtered[filtered[day_column] == 1]
            else:
                st.warning(f"Day filter '{day}' could not be applied. Column '{day_column}' not found.")

        # Apply time filter if selected
        if time_slot != "Any":
            time_column = "time"  # Adjust if your time column has a different name
            if time_column in filtered.columns:
                filtered = filtered[filtered[time_column] == time_slot.lower()]
            else:
                st.warning(f"Time filter could not be applied. Column '{time_column}' not found.")

        # Get top recommendations based on filters
        filtered = filtered.sort_values('avg_rating', ascending=False).head(num_recs)

        bookmarks = load_bookmarks()
        user_bookmarks = bookmarks.get(st.session_state.username, [])

        if filtered.empty:
            st.warning("No restaurants match your criteria. Please try adjusting your filters.")
        else:
            st.subheader("🍽️ Recommended Restaurants")
            
            # Create a list of rows for display in columns
            restaurants = filtered.to_dict('records')
            
            # Display restaurants in 2 columns
            col1, col2 = st.columns(2)
            
            for i, row in enumerate(restaurants):
                # Alternate between columns
                with col1 if i % 2 == 0 else col2:
                    with st.container():
                        st.markdown(f"### {row['name']} ({row['Rcuisine_x']})")
                        
                        # Extract first cuisine
                        first_cuisine = str(row['Rcuisine_x']).split(';')[0].strip().lower()
                        cuisine_folder = os.path.join("restaurant_images", first_cuisine)
                        
                        # Show images if folder exists for the cuisine
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
                            # Display star rating instead of number
                            st.markdown(display_star_rating(row['avg_rating']), unsafe_allow_html=True)
                        
                        with details_col2:
                            st.markdown(f"**Group Friendly:** {row['group_friendly_score']:.2f}")
                            st.markdown(f"**Distance:** {row['distance_km']} km")
                            
                        st.markdown(f"[📍 View on Map](https://www.google.com/maps/search/?api=1&query={row['rest_latitude']},{row['rest_longitude']})")

                        # Use a unique key for each button by combining placeID with index
                        button_key = f"{row['placeID']}_{i}"
                        
                        if row['name'] not in user_bookmarks:
                            if st.button(f"🔖 Bookmark", key=button_key):
                                user_bookmarks.append(row['name'])
                                bookmarks[st.session_state.username] = user_bookmarks
                                save_bookmarks(bookmarks)
                                st.success(f"Bookmarked {row['name']}!")
                        else:
                            st.info("✅ Already Bookmarked")
                        
                        st.markdown("---")
