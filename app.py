import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import google.generativeai as genai
import os


# ==============================
# PAGE SETTINGS
# ==============================

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="centered"
)


# ==============================
# LOAD DATASET
# ==============================

@st.cache_data
def load_dataset():

    path = "data/india_tourism_dataset.json"

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return pd.DataFrame(data)


df = load_dataset()



# ==============================
# GEMINI CONFIGURATION
# ==============================

GEMINI_API_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"


if GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE":

    genai.configure(
        api_key=GEMINI_API_KEY
    )

    gemini_model = genai.GenerativeModel(
        "gemini-2.5-flash"
    )

else:

    gemini_model = None



# ==============================
# RECOMMENDATION SYSTEM
# ==============================

def recommend_places(
        budget,
        season,
        trip_type
):

    data = df.copy()


    score = []


    for index,row in data.iterrows():

        points = 0


        # Budget matching

        if "budget_category" in row:

            if budget.lower() in str(
                row["budget_category"]
            ).lower():

                points += 3



        # Season matching

        if "best_seasons" in row:

            if season.lower() in str(
                row["best_seasons"]
            ).lower():

                points += 3



        # Trip type matching

        if "trip_types" in row:

            if trip_type.lower() in str(
                row["trip_types"]
            ).lower():

                points += 4



        # Popularity bonus

        if "popularity_score" in row:

            try:

                points += float(
                    row["popularity_score"]
                ) / 10

            except:

                pass


        score.append(points)



    data["match_score"] = score


    return data.sort_values(
        by="match_score",
        ascending=False
    ).head(5)



# ==============================
# CREATE PDF
# ==============================

def create_pdf(content):

    file_name = "AI_Travel_Itinerary.pdf"


    doc = SimpleDocTemplate(
        file_name
    )


    styles = getSampleStyleSheet()


    story = []


    for line in content.split("\n"):

        story.append(
            Paragraph(
                line,
                styles["Normal"]
            )
        )

        story.append(
            Spacer(
                1,
                10
            )
        )


    doc.build(
        story
    )


    return file_name



# ==============================
# HEADER
# ==============================


st.title(
    "🌍 AI Travel Planner"
)

st.write(
    "Plan your perfect trip using Artificial Intelligence"
)



# ==============================
# USER INPUT
# ==============================


budget = st.selectbox(
    "💰 Select Budget",
    [
        "Budget",
        "Moderate",
        "Luxury"
    ]
)


season = st.selectbox(
    "🌦 Select Season",
    [
        "Summer",
        "Winter",
        "Monsoon",
        "Spring"
    ]
)


trip_type = st.selectbox(
    "🎯 Travel Type",
    [
        "Adventure",
        "Beach",
        "Family",
        "Luxury",
        "Nature",
        "Solo",
        "Honeymoon"
    ]
)


days = st.slider(
    "📅 Number of Days",
    1,
    15,
    5
)




if st.button(
    "🔍 Recommend Places",
    key="recommend_button"
):

    st.session_state.results = recommend_places(
        budget,
        season,
        trip_type
    )
# ==============================
# DISPLAY RECOMMENDATIONS
# ==============================

if "results" in st.session_state:

    st.divider()

    st.subheader(
        "⭐ Recommended Destinations"
    )


    results = st.session_state.results


    for i, row in results.iterrows():

        name = row.get(
            "destination_name",
            "Unknown Destination"
        )


        with st.expander(
            f"📍 {name}"
        ):


            st.write(
                "🏛️ State:",
                row.get(
                    "state",
                    "Not available"
                )
            )


            st.write(
                "💰 Budget:",
                row.get(
                    "budget_category",
                    "Not available"
                )
            )


            st.write(
                "🌦 Best Season:",
                row.get(
                    "best_seasons",
                    "Not available"
                )
            )


            st.write(
                "🎯 Trip Type:",
                row.get(
                    "trip_types",
                    "Not available"
                )
            )


            st.write(
                "⭐ Popularity Score:",
                row.get(
                    "popularity_score",
                    "Not available"
                )
            )


            st.write(
                "🛡 Safety Rating:",
                row.get(
                    "safety_rating",
                    "Not available"
                )
            )


            st.write(
                "🏞 Attractions:"
            )

            st.write(
                row.get(
                    "primary_attractions",
                    "Not available"
                )
            )


            st.write(
                "🎒 Activities:"
            )

            st.write(
                row.get(
                    "activities_available",
                    "Not available"
                )
            )



            # ==============================
            # MAP
            # ==============================


            if "coordinates" in row:


                try:

                    coordinates = row["coordinates"]


                    lat = coordinates["latitude"]

                    lon = coordinates["longitude"]


                    travel_map = folium.Map(
                        location=[
                            lat,
                            lon
                        ],
                        zoom_start=10
                    )


                    folium.Marker(
                        [
                            lat,
                            lon
                        ],
                        popup=name
                    ).add_to(
                        travel_map
                    )


                    st_folium(
                        travel_map,
                        width=650,
                        height=400
                    )


                except:

                    st.info(
                        "Map location not available"
                    )



            # ==============================
            # GEMINI AI ITINERARY
            # ==============================
            if st.button(
                f"🤖 Generate AI Trip Plan - {name}",
                key=f"ai_plan_{i}"
            ):

                prompt = f"""

Create a detailed {days} day travel itinerary.

Destination:
{name}

State:
{row.get('state','')}

Travel Type:
{trip_type}

Budget:
{budget}


Include:

1. Day wise itinerary
2. Places to visit
3. Local food recommendations
4. Transport options
5. Estimated expenses
6. Safety tips
7. Packing suggestions

Make it practical for Indian travellers.

"""


                if gemini_model:


                    with st.spinner(
                        "Generating AI plan..."
                    ):


                        response = gemini_model.generate_content(
                            prompt
                        )


                    itinerary = response.text


                else:


                    itinerary = """

Gemini API key is not added.

Add your API key in the GEMINI CONFIGURATION section.

"""


                st.success(
                    "AI Travel Plan Ready"
                )


                st.write(
                    itinerary
                )


                # PDF DOWNLOAD

                pdf_file = create_pdf(
                    itinerary
                )


                with open(
                    pdf_file,
                    "rb"
                ) as file:


                    st.download_button(
                        label="📄 Download Itinerary PDF",
                        data=file,
                        file_name="AI_Travel_Plan.pdf",
                        mime="application/pdf"
                    )



# ==============================
# DATASET ANALYTICS
# ==============================


st.divider()


st.subheader(
    "📊 Travel Dataset Analytics"
)


col1, col2 = st.columns(2)


with col1:

    st.metric(
        "Total Destinations",
        len(df)
    )


with col2:

    if "state" in df.columns:

        st.metric(
            "States Covered",
            df["state"].nunique()
        )



if "state" in df.columns:

    st.subheader(
        "Top Tourist States"
    )


    state_count = (
        df["state"]
        .value_counts()
        .head(10)
    )


    st.bar_chart(
        state_count
    )



# ==============================
# FOOTER
# ==============================


st.divider()


st.caption(
    "✈️ AI Travel Planner | Built using Streamlit + Gemini AI"
)


