import streamlit as st
import pandas as pd
import sqlite3

# --- Page Config ---
st.set_page_config(page_title="Food Wastage Manager", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stHeaderActionElements"],
        .stAppHeader {
            display: none;
        }
        .stMainBlockContainer {
            padding: 0rem 4rem 1rem;
        }
    </style>
""", unsafe_allow_html=True)


# --- DB Connection ---
def get_connection():
    return sqlite3.connect("food_wastage.db")


# --- Home Page ---
def home_page():
    st.header("🌍 Welcome to Food Wastage Manager")
    st.write(
        """
        This platform helps manage and analyze food donations to minimize wastage
        and ensure food reaches the people who need it most.  

        **Features you’ll find here:**  
        - 🔎 *Search & Filter*: Explore available food listings by city, provider, food type, or meal type.  
        - 📊 *SQL Queries*: Run powerful pre-defined queries to gain insights into providers, receivers, claims, and food availability.  

        ---
        ### Why this project?  
        Food wastage is a pressing global issue. By managing food supply chains efficiently,  
        we can:  
        - Reduce hunger and food insecurity  
        - Support local communities and NGOs  
        - Build a more sustainable food ecosystem  

        Use the navigation above to get started 🚀
        """
    )


# --- Page 1: Search & Filter ---
def search_page():
    st.header("🔎 Search & Filter Food Listings")

    conn = get_connection()

    # --- Dynamic dropdown values ---
    cities = pd.read_sql_query("SELECT DISTINCT City FROM providers", conn)["City"].dropna().tolist()
    providers = pd.read_sql_query("SELECT DISTINCT Name FROM providers", conn)["Name"].dropna().tolist()

    # Sidebar filters
    filter_city = st.sidebar.selectbox("Filter by City", ["All"] + cities)
    filter_provider = st.sidebar.selectbox("Filter by Provider", ["All"] + providers)
    filter_food_type = st.sidebar.multiselect(
        "Filter by Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"]
    )
    filter_meal_type = st.sidebar.multiselect(
        "Filter by Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"]
    )

    # Explicitly select unique columns with aliases
    query = """
        SELECT 
            f.Food_ID,
            f.Food_Name,
            f.Quantity,
            f.Expiry_Date,
            f.Food_Type,
            f.Meal_Type,
            f.Location AS Food_Location,
            p.Provider_ID,
            p.Name AS Provider_Name,
            p.Type AS Provider_Type,
            p.Address AS Provider_Address,
            p.City AS Provider_City,
            p.Contact AS Provider_Contact
        FROM food_listings f
        JOIN providers p ON f.Provider_ID = p.Provider_ID
        WHERE 1=1
    """

    if filter_city != "All":
        query += f" AND p.City='{filter_city}'"
    if filter_provider != "All":
        query += f" AND p.Name='{filter_provider}'"
    if filter_food_type:
        ft = "', '".join(filter_food_type)
        query += f" AND f.Food_Type IN ('{ft}')"
    if filter_meal_type:
        mt = "', '".join(filter_meal_type)
        query += f" AND f.Meal_Type IN ('{mt}')"

    df = pd.read_sql_query(query, conn)
    st.dataframe(df, use_container_width=True, height=480)

    conn.close()


# --- Page 2: Queries ---
def queries_page():
    st.header("📊 SQL Analysis Queries")

    conn = get_connection()

    queries = {
        "Providers & Receivers per City":
            "SELECT p.City, COUNT(DISTINCT p.Provider_ID) AS Total_Providers, COUNT(DISTINCT r.Receiver_ID) AS Total_Receivers FROM providers p LEFT JOIN receivers r ON p.City = r.City GROUP BY p.City;",
        "Top Food Provider Type":
            "SELECT Provider_Type, SUM(Quantity) AS Total_Quantity FROM food_listings GROUP BY Provider_Type ORDER BY Total_Quantity DESC LIMIT 1;",
        "Providers Contact Info":
            "SELECT Name, Type, Contact FROM providers;",
        "Top Receivers by Claims":
            "SELECT r.Name, COUNT(c.Claim_ID) AS Total_Claims FROM claims c JOIN receivers r ON c.Receiver_ID = r.Receiver_ID GROUP BY r.Name ORDER BY Total_Claims DESC LIMIT 5;",
        "Total Food Available":
            "SELECT SUM(Quantity) AS Total_Foods FROM food_listings;",
        "City with Highest Listings":
            "SELECT Location, COUNT(Food_ID) AS Total_Listings FROM food_listings GROUP BY Location ORDER BY Total_Listings DESC LIMIT 1;",
        "Most Common Food Types":
            "SELECT Food_Type, COUNT(*) AS Count_Type FROM food_listings GROUP BY Food_Type ORDER BY Count_Type DESC;",
        "Claims per Food Item":
            "SELECT f.Food_Name, COUNT(c.Claim_ID) AS Total_Claims FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID GROUP BY f.Food_Name ORDER BY Total_Claims DESC;",
        "Top Provider by Successful Claims":
            "SELECT p.Name, COUNT(c.Claim_ID) AS Successful_Claims FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID JOIN providers p ON f.Provider_ID = p.Provider_ID WHERE c.Status='Completed' GROUP BY p.Name ORDER BY Successful_Claims DESC LIMIT 1;",
        "Claims by Status %":
            "SELECT Status, ROUND(COUNT() * 100.0 / (SELECT COUNT() FROM claims), 2) AS Percentage FROM claims GROUP BY Status;",
        "Avg Quantity Claimed per Receiver":
            "SELECT r.Name, ROUND(AVG(f.Quantity),2) AS Avg_Quantity_Claimed FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID JOIN receivers r ON c.Receiver_ID = r.Receiver_ID GROUP BY r.Name;",
        "Most Claimed Meal Type":
            "SELECT Meal_Type, COUNT(*) AS Claim_Count FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID GROUP BY Meal_Type ORDER BY Claim_Count DESC LIMIT 1;",
        "Quantity Donated per Provider":
            "SELECT p.Name, SUM(f.Quantity) AS Total_Donated FROM food_listings f JOIN providers p ON f.Provider_ID = p.Provider_ID GROUP BY p.Name ORDER BY Total_Donated DESC;",
        "Top 5 Cities by Completed Claims":
            "SELECT f.Location, COUNT(c.Claim_ID) AS Completed_Claims FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID WHERE c.Status='Completed' GROUP BY f.Location ORDER BY Completed_Claims DESC LIMIT 5;",
        "Food Items Nearing Expiry (Next 3 Days)":
            "SELECT Food_Name, Expiry_Date, Quantity FROM food_listings WHERE date(Expiry_Date) <= date('now','+3 days');"
    }

    # Sidebar query selector
    selected_query = st.sidebar.radio("Choose a Query", list(queries.keys()))

    # Show only selected query
    st.write(f"📃 {selected_query}")
    df = pd.read_sql_query(queries[selected_query], conn)
    st.dataframe(df, use_container_width=True)

    conn.close()


# --- Main ---
col1, col2 = st.columns([3, 2], vertical_alignment='bottom')

with col1:
    st.title("Food Wastage Manager")

with col2:
    page = st.radio(
        "Navigation",
        ["Home", "Search & Filter", "SQL Queries"],
        horizontal=True,
        label_visibility="collapsed"
    )

if page == "Home":
    home_page()
elif page == "Search & Filter":
    search_page()
elif page == "SQL Queries":
    queries_page()