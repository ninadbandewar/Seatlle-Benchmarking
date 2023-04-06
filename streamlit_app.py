#############################################################################
# Course: Interactive Data Science(05839-A)
# Coded By: Aditi Kanaujia, Jeffrey Na, Nikita Khatwani, Ninad Bandewar, Pragnya Sridhar
# AndrewID: akanauji, jjna, nkhatwan, nbandewa, pragnyas
# Date: Nov 22, 2022
# Thanks to Prof. John Stamper, Prof. Adam Perer & TAs for there assistance

#############################################################################
# Library Imports
#############################################################################

import urllib
import math
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import folium as fo
from streamlit_folium import st_folium
from PIL import Image
#from vega_datasets import data

#############################################################################
# Introduction
#############################################################################

st.set_page_config(layout = "wide")

#############################################################################
# Extra Font Styles
#############################################################################

# from https://discuss.streamlit.io/t/change-font-size-in-st-write/7606
st.markdown("""
<style>
.smallSubHeader {
    font-size:18px !important;
    font-weight:bold !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.description {
    font-size:15px !important;
}
</style>
""", unsafe_allow_html=True)

#############################################################################
# Introduction (Continue)
#############################################################################


st.title("Energy map exploration of buildings in the city of Seattle")


urllib.request.urlretrieve('https://raw.githubusercontent.com/CMU-IDS-Fall-2022/final-project-the-viz-kids/main/769689.jpg', 'seattle.jpeg')
img = Image.open('seattle.jpeg')
st.image(img ,use_column_width= True)


st.header("Introduction")
st.write(
    "Buildings contribute to 38% of global emissions as per the UN \
    Environmental Global Status Report 2020. Hence, it is crucial for us to \
    make efforts to reduce energy consumption in buildings. Each building’s energy usage is \
    mentioned in its monthly bill. However, it is quite challenging to assess \
    if this amount would be higher/lower than others or the set average \
    (threshold) consumption value for say, the 2050 goal. This can be achieved \
    using the benchmark data. To be specific, Seattle has State Policies to \
    require all public, commercial, and multifamily buildings to complete the \
    benchmarking report of energy consumption in the building. In this regard, \
    this app can be used to identify energy efficient buildings to learn more \
    about practices responsible for its efficiency and also to identify \
    buildings that perform poorly. This will help the owners or other parties \
    for further analysis and assess if the building must be retrofitted with \
    newer green attributes like more energy efficient appliances, better \
    heating/cooling systems, airtight construction, etc to reduce its energy \
    consumption.")

#############################################################################
# Data Import
#############################################################################

@st.cache (allow_output_mutation=True)
def load(url):
    return pd.read_csv(url, encoding = "latin1")

df = load("https://raw.githubusercontent.com/CMU-IDS-Fall-2022/final-project-the-viz-kids/main/Combined.csv")

if st.checkbox("Show Raw Data"):
    st.write(df)

#############################################################################
# Part 1: Map
#############################################################################

# Extract Necessary Columns to reduce the expense of computation
dfMap = df[["OSEBuildingID", "DataYear", "Address", "ZipCode", "Latitude", "Longitude", "YearBuilt",
            "NumberofFloors", "PropertyGFABuilding(s)", "LargestPropertyUseType", 
            "ENERGYSTARScore", "SiteEUIWN(kBtu/sf)", "PredictedEnergyStar"]]

def clear_zipcodes():
    st.session_state.zipcodes = []
    return

# Drop Null Value Rows
dfMap.dropna(axis = "rows", subset = ["PropertyGFABuilding(s)", "NumberofFloors", 
            "YearBuilt", "ENERGYSTARScore", "SiteEUIWN(kBtu/sf)", "Latitude", "Longitude"], inplace = True)

# Create Columns for colors
@st.cache (allow_output_mutation = True)
def setEUIColors(dataFrame):
    EUIDict = {0: "#2CBA00", 1: "#A3FF00", 2: "#FFA700", 3: "#FF7B00", 
                     4: "#FF7272", 5: "#FF0000", 6: "#A40808"}
    dataFrame["EUIColors"] = pd.cut(dataFrame["SiteEUIWN(kBtu/sf)"].apply(np.ceil), 
                    [0, 25, 50, 75, 100, 125, 150, 1000000],\
                    labels=[EUIDict[0], EUIDict[1], EUIDict[2], EUIDict[3], 
                    EUIDict[4], EUIDict[5], EUIDict[6]])
    return dataFrame

@st.cache (allow_output_mutation = True)
def setEnergyScoreColors(dataFrame):
    energyScoreDict = {0: "#0700C4", 1: "#0000FF", 2: "#0052FF", 3: "#0077AF", 
                     4: "#00A3FF", 5: "#00CCFF", 6: "#66CBFF"}
    dataFrame["EnergyColors"] = pd.cut(dataFrame["ENERGYSTARScore"].apply(np.ceil), 
                        [0, 15, 30, 45, 60, 75, 90, 100],\
                        labels=[energyScoreDict[0], energyScoreDict[1], energyScoreDict[2], 
                                energyScoreDict[3], energyScoreDict[4], energyScoreDict[5], 
                                energyScoreDict[6] ])
    return dataFrame

dfMap = setEUIColors(dfMap)
dfMap = setEnergyScoreColors(dfMap)


filterCol, mapCol, legendCol = st.columns([1,4,0.5])

with filterCol: 
    st.subheader("Data Filters")
    st.markdown('<p class = "smallSubHeader" > Select the Type of Map. </p>'
                    , unsafe_allow_html = True)
    mapSelect = st.radio("Type", label_visibility = "collapsed", 
                        options = ["Energy Use Intensity Map", "Energy Star Score Map"])


    
    # Data Year Filter
    st.markdown('<p class = "smallSubHeader" > Select the Year. </p>'
                    , unsafe_allow_html = True)
    # Get Unique Years and a descending sort
    years = np.sort(dfMap["DataYear"].unique())[::-1]
    yearSelect = st.selectbox("Year", label_visibility = "collapsed",
                 options = years)
    
    dfMapYear = dfMap[dfMap["DataYear"] == yearSelect]



    # Energy Use Intensity / Energy Star Score Filter
    if (mapSelect == "Energy Use Intensity Map"):
        # Extract Range for the Current Data Frame
        maxEUI = math.ceil(np.sort(dfMap["SiteEUIWN(kBtu/sf)"])[::-1][0])
        minEUI = math.floor(np.sort(dfMap["SiteEUIWN(kBtu/sf)"])[0])

        st.markdown('<p class = "smallSubHeader" > Filter with Energy Use Intensity (kBTU/sq.ft.). </p>'
                    , unsafe_allow_html = True)
        EUIRange = st.slider("Energy Use Intensity", label_visibility = "collapsed", 
                                min_value = minEUI, max_value = maxEUI, 
                                value = [minEUI, maxEUI], step = 25)
        
        minEUISelect, maxEUISelect = EUIRange[0], EUIRange[1]

        dfMap = dfMap[dfMap["SiteEUIWN(kBtu/sf)"].between(minEUISelect, maxEUISelect, inclusive = 'both')] 
    
    elif (mapSelect == "Energy Star Score Map"):
        # Extract Range for the Current Data Frame
        maxEnergyScore = math.ceil(np.sort(dfMap["ENERGYSTARScore"])[::-1][0])
        minEnergyScore = math.floor(np.sort(dfMap["ENERGYSTARScore"])[0])

        st.markdown('<p class = "smallSubHeader" > Filter with Energy Star Score. </p>'
                    , unsafe_allow_html = True)
        energyScoreRange = st.slider("Energy Star Score", label_visibility = "collapsed", 
                                min_value = minEnergyScore, max_value = minEnergyScore, 
                                value = [minEnergyScore, maxEnergyScore], step = 10)

        minEnergyScoreSelect, maxEnergyScoreSelect = energyScoreRange[0], energyScoreRange[1]

        dfMap = dfMap[dfMap["ENERGYSTARScore"].between(minEnergyScoreSelect, maxEnergyScoreSelect, inclusive = "both")] 
    


    # ZipCode Filter
    st.markdown('<p class = "smallSubHeader" > Filter with Zipcodes. </p>'
                    , unsafe_allow_html = True)
    zipcodes = np.sort(dfMap["ZipCode"].unique())
    zipcodeSelect = st.multiselect("Zipcode", label_visibility = "collapsed", 
                                    options = zipcodes, key = "zipcodes")
    st.button("Clear Zipcodes", on_click = clear_zipcodes)

    if (zipcodeSelect != []):
        dfMap = dfMap[dfMap["ZipCode"].isin(zipcodeSelect)]
    


    # Area Filter    
    st.markdown('<p class = "smallSubHeader" > Filter with Gross Floor Area. </p>'
                    , unsafe_allow_html = True)
    
    if (len(dfMap) == 0):
        st.markdown('<p class = "description" > There are NO BUILDINGS that match these parameters. </p>'
                    , unsafe_allow_html = True)
    elif (len(dfMap) == 1):
        st.markdown(f'<p class = "description" > The ONLY BUILDING with these \
                        parameters has a floor area of \
                        {int(dfMap.iloc[0]["PropertyGFABuilding(s)"])} sq.ft. </p>',
                    unsafe_allow_html = True)
    else:
        maxArea = math.ceil(np.sort(dfMap["PropertyGFABuilding(s)"])[::-1][0])
        minArea = math.floor(np.sort(dfMap["PropertyGFABuilding(s)"])[0])

        areaRange = st.slider("Area", label_visibility = "collapsed", 
                            min_value = minArea, max_value = maxArea, 
                            value = [minArea, maxArea])
    
        minAreaSelect, maxAreaSelect = areaRange[0], areaRange[1]

        dfMap = dfMap[dfMap["PropertyGFABuilding(s)"].between(minAreaSelect, maxAreaSelect, inclusive = "both")] 
    
    

    # Number of Floors Filter
    st.markdown('<p class = "smallSubHeader" > Filter With Number of Floors. </p>'
                        , unsafe_allow_html = True)

    if (len(dfMap) == 0):
        st.markdown('<p class = "description" > There are NO BUILDINGS that match these parameters. </p>'
                    , unsafe_allow_html = True)
    elif (len(dfMap) == 1):
        st.markdown(f'<p class = "description" > The ONLY BUILDING with these parameters \
                    has {int(dfMap.iloc[0]["NumberofFloors"])} number of floors. </p>'
                    , unsafe_allow_html = True)
    else:
        maxFloor = math.ceil(np.sort(dfMap["NumberofFloors"])[::-1][0])
        minFloor = math.floor(np.sort(dfMap["NumberofFloors"])[0])

        floorRange = st.slider("Floors", label_visibility = "collapsed", 
                                min_value = minFloor, max_value = maxFloor, 
                                value = [minFloor, maxFloor])

        minFloorSelect, maxFloorSelect = floorRange[0], floorRange[1]

        dfMap = dfMap[dfMap["NumberofFloors"].between(minFloorSelect, maxFloorSelect, inclusive = "both")]

    

    # Year Built Filter
    st.markdown('<p class = "smallSubHeader" > Filter With Year Built. </p>'
                        , unsafe_allow_html = True)

    if (len(dfMap) == 0):
        st.markdown('<p class = "description" > There are NO BUILDINGS that match these parameters. </p>'
                    , unsafe_allow_html = True)
    elif (len(dfMap) == 1):
        st.markdown(f'<p class = "description" > The ONLY BUILDING with these parameters \
                    was built in {int(dfMap.iloc[0]["YearBuilt"])}. </p>'
                    , unsafe_allow_html = True)
    else:
        maxYearBuilt = math.ceil(np.sort(dfMap["YearBuilt"])[::-1][0])
        minYearBuilt = math.floor(np.sort(dfMap["YearBuilt"])[0])
        
        yearBuiltRange = st.slider("YearBuilt", label_visibility = "collapsed", 
                                    min_value = minYearBuilt, max_value = maxYearBuilt, 
                                    value = [minYearBuilt, maxYearBuilt])

        minYearBuiltSelect, maxYearBuiltSelect = yearBuiltRange[0], yearBuiltRange[1]    
        
        dfMap = dfMap[dfMap["YearBuilt"].between(minYearBuiltSelect, maxYearBuiltSelect, inclusive = "both")]


with mapCol:
    if (mapSelect == "Energy Use Intensity Map"):
        st.subheader(f"{yearSelect} Energy Use Intensity Map")
    elif (mapSelect == "Energy Star Score Map"):
        st.subheader(f"{yearSelect} Energy Star Score Map")

    map = fo.Map(location = [47.6062, -122.3321], tiles = "cartodbpositron", \
                zoom_start = 14, min_zoom = 12, max_zoom = 16,
                width = "100%", height = "75%")
    
    if (mapSelect == "Energy Use Intensity Map"):        

        for i, row in dfMap.iterrows():
            popContent = f"Address: {row['Address']} <br> \
                Program: {row['LargestPropertyUseType']} <br> \
                EUI: {row['SiteEUIWN(kBtu/sf)']}"            
            fo.Circle(
                radius = 15,
                location = [row["Latitude"], row["Longitude"]],
                color = row["EUIColors"],
                fill = True,
                fill_opacity = 1,
                popup = fo.Popup(popContent, min_width = 200, max_width = 200),
                tooltip = row["Address"]
            ).add_to(map)
        
        st_map = st_folium(map, width = 1500, height = 750)

        point = st_map["last_object_clicked"]
        if point:
            latitude, longitude = point["lat"], point["lng"]
        else:
            latitude = dfMap.iloc[0]["Latitude"]
            longitude = dfMap.iloc[0]["Longitude"]
            energyStar = dfMap.iloc[0]["ENERGYSTARScore"]

        df_point = dfMap[(dfMap["Latitude"] == latitude) & (dfMap["Longitude"] == longitude)]

        st.markdown(f'<p class = "smallSubHeader" > Your Selected Building is {df_point.iloc[0]["Address"]}. </p>'
                    , unsafe_allow_html = True)
          
    
    elif (mapSelect == "Energy Star Score Map"):
        
        for i, row in dfMap.iterrows():
            if (row["PredictedEnergyStar"] == 0):
                popContent = f"Address: {row['Address']} <br> \
                            Program: {row['LargestPropertyUseType']} <br> \
                            Energy Star Score: {row['ENERGYSTARScore']}"
            else:
                popContent = f"Address: {row['Address']} <br> \
                            Program: {row['LargestPropertyUseType']} <br> \
                            Predicted Energy Star Score: {row['ENERGYSTARScore']}*"
            fo.Circle(
                radius = 15,
                location = [row["Latitude"], row["Longitude"]],
                color = row["EnergyColors"], 
                fill = True,
                fill_opacity = 1,
                popup = fo.Popup(popContent, min_width = 200, max_width = 200),
                tooltip = row["Address"]
            ).add_to(map)

        st_map = st_folium(map, width = 1500, height = 750)

        point = st_map["last_object_clicked"]
        if point:
            latitude, longitude = point["lat"], point["lng"]
        else:
            latitude = dfMap.iloc[0]["Latitude"]
            longitude = dfMap.iloc[0]["Longitude"]
            energyStar = dfMap.iloc[0]["ENERGYSTARScore"]

        df_point = dfMap[(dfMap["Latitude"] == latitude) & (dfMap["Longitude"] == longitude)]

        st.markdown(f'<p class = "smallSubHeader" > Your Selected Building is {df_point.iloc[0]["Address"]}. </p>'
                    , unsafe_allow_html = True)  
       
with legendCol:

    st.subheader("Legend")

    if (mapSelect == "Energy Use Intensity Map"):    
        urllib.request.urlretrieve('https://raw.githubusercontent.com/CMU-IDS-Fall-2022/final-project-the-viz-kids/main/legend%202.jpg', 'legend1.jpeg')
        img = Image.open('legend1.jpeg')
        st.image(img ,use_column_width= True)

    elif (mapSelect == "Energy Star Score Map"):    
        urllib.request.urlretrieve('https://raw.githubusercontent.com/CMU-IDS-Fall-2022/final-project-the-viz-kids/main/legend%20-1.jpg', 'legend2.jpeg')
        img = Image.open('legend2.jpeg')
        st.image(img ,use_column_width= True)  


#############################################################################
# Part 2: Building Statistics
#############################################################################

df["Address"] = df["Address"].str.upper()
df["SiteEUIWN(kBtu/sf)"] = df["SiteEUIWN(kBtu/sf)"].round(1)
df_result_search = pd.DataFrame()

if st.button("Analyze Your Selected Building"):
    df_result_search = df[df["OSEBuildingID"] == df_point.iloc[0]["OSEBuildingID"]]
            

    temp_df1 = df_result_search.iloc[0]
    temp_df2 = df_result_search.iloc[-1]
    ZipInput = temp_df1["ZipCode"]
    TypeInput = temp_df1["LargestPropertyUseType"]
    YearInput = temp_df1["YearBuilt"]
    FloorInput = temp_df1["NumberofFloors"]
    EUIInput = temp_df2["SiteEUIWN(kBtu/sf)"]
    ESInput = temp_df2["ENERGYSTARScore"]
    
    st.write("Zip Code: **{ZIP}**".format(ZIP = int(ZipInput)))
    st.write("Property Type: **{Type}**".format(Type = TypeInput))
    st.write("Built Year: **{Year}**".format(Year = int(YearInput)))
    st.write("Number of Floors: **{Floor}**".format(Floor = int(FloorInput)))
    st.write("Site EUI (2020): **{EUI}** kBtu/sf".format(EUI = EUIInput))
    st.write("ENERGY STAR Score (2020): **{ES}**".format(ES = int(ESInput)))
    
    
    ################# CHATPER 1
    
    st.subheader("1. HOW MUCH EFFICIENT IS YOUR BUILDING?")

    ################# CHATPER 1-1

    st.write("**1-1. CITY LEVEL EFFICIENCY**")
    st.write("Let's compare your building with the average of the buildings in the same neighborhood in the city of Seattle.")
    st.write("**1) EUI: Your Building vs. {Type} in the city of Seattle**".format(Type = TypeInput))
    
    #1) EUI trend_selected ######################################

    chart1_year = df_result_search["DataYear"]
    chart1_eui = df_result_search["SiteEUIWN(kBtu/sf)"]
    chart1_data = pd.concat([chart1_year, chart1_eui], axis=1)
    chart1_data["Type"] = "YOUR BUILDING"
    
            
    #2) EUI trend_city mean ######################################

    city_search = df[df['LargestPropertyUseType'] == (TypeInput)]
    # st.write(city_search)      
    
    mean16 = city_search[city_search["DataYear"] == 2016]["SiteEUIWN(kBtu/sf)"].mean()
    mean17 = city_search[city_search["DataYear"] == 2017]["SiteEUIWN(kBtu/sf)"].mean()
    mean19 = city_search[city_search["DataYear"] == 2019]["SiteEUIWN(kBtu/sf)"].mean()
    mean20 = city_search[city_search["DataYear"] == 2020]["SiteEUIWN(kBtu/sf)"].mean()
    mean16 = round(mean16, 1)
    mean17 = round(mean17, 1)
    mean19 = round(mean19, 1)
    mean20 = round(mean20, 1)
    
    city_mean = pd.DataFrame({"DataYear":[2016, 2017, 2019, 2020],
                                "SiteEUIWN(kBtu/sf)": [mean16, mean17, mean19, mean20],
                                "Type": ["CITY AVERAGE", "CITY AVERAGE", "CITY AVERAGE", "CITY AVERAGE"]})        
    
    chart1_data = chart1_data.append(city_mean, ignore_index = True)
    
    #3) EUI trend_chart ######################################

    chart1_plot = (alt.Chart(chart1_data)
                    .mark_line(point=True)
                    .encode(
                        x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                        y= alt.Y("SiteEUIWN(kBtu/sf)"),
                        color = "Type",
                        tooltip=["SiteEUIWN(kBtu/sf)"]))
    
    st.altair_chart(chart1_plot, use_container_width=True)        
    
    #4) ES trend_selected ######################################

    st.write("**2) Energy Star score: Your Building vs. {Type} in the city of Seattle**".format(Type = TypeInput))
    chart2_year = df_result_search["DataYear"]
    chart2_es = df_result_search["ENERGYSTARScore"]
    chart2_data = pd.concat([chart2_year, chart2_es], axis=1)
    chart2_data["Type"] = "YOUR BUILDING"
    
            
    #5) ES trend_city mean ######################################

    city_search = df[df['LargestPropertyUseType'] == (TypeInput)]
            
    mean16 = city_search[city_search["DataYear"] == 2016]["ENERGYSTARScore"].mean()
    mean17 = city_search[city_search["DataYear"] == 2017]["ENERGYSTARScore"].mean()
    mean19 = city_search[city_search["DataYear"] == 2019]["ENERGYSTARScore"].mean()
    mean20 = city_search[city_search["DataYear"] == 2020]["ENERGYSTARScore"].mean()
    mean16 = round(mean16, 1)
    mean17 = round(mean17, 1)
    mean19 = round(mean19, 1)
    mean20 = round(mean20, 1)
    
    city_mean = pd.DataFrame({"DataYear":[2016, 2017, 2019, 2020],
                                "ENERGYSTARScore": [mean16, mean17, mean19, mean20],
                                "Type": ["CITY AVERAGE", "CITY AVERAGE", "CITY AVERAGE", "CITY AVERAGE"]})        
    
    chart2_data = chart2_data.append(city_mean, ignore_index = True)
    
    #6) ES trend_chart ######################################

    chart2_plot = (alt.Chart(chart2_data)
                    .mark_line(point=True)
                    .encode(
                        x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                        y= alt.Y("ENERGYSTARScore"),
                        color = "Type",
                        tooltip=["ENERGYSTARScore"]))
    
    st.altair_chart(chart2_plot, use_container_width=True)

    ################# CHATPER 1-2

    st.write("**1-2. NEIGHBORHOOD LEVEL EFFICIENCY**")
    st.write("Let's compare your building with the average of the buildings in the same neighborhood in the city of Seattle.")
    st.write("**1) EUI: Your Building vs. {ZIP} neighborhood in the city of Seattle**".format(ZIP = int(ZipInput)))
    
    #1) EUI trend_selected ######################################

    chart3_data = pd.concat([chart1_year, chart1_eui], axis=1)
    chart3_data["Type"] = "YOUR BUILDING"
    
    #2) EUI trend_neighborhood mean ######################################

    city_search = df[df['LargestPropertyUseType'] == (TypeInput)]
    nb_search = city_search[city_search['ZipCode'] == (int(ZipInput))]
    
    mean16 = nb_search[nb_search["DataYear"] == 2016]["SiteEUIWN(kBtu/sf)"].mean()
    mean17 = nb_search[nb_search["DataYear"] == 2017]["SiteEUIWN(kBtu/sf)"].mean()
    mean19 = nb_search[nb_search["DataYear"] == 2019]["SiteEUIWN(kBtu/sf)"].mean()
    mean20 = nb_search[nb_search["DataYear"] == 2020]["SiteEUIWN(kBtu/sf)"].mean()
    mean16 = round(mean16, 1)
    mean17 = round(mean17, 1)
    mean19 = round(mean19, 1)
    mean20 = round(mean20, 1)

    nb_mean = pd.DataFrame({"DataYear":[2016, 2017, 2019, 2020],
                                "SiteEUIWN(kBtu/sf)": [mean16, mean17, mean19, mean20],
                                "Type": ["NEIGHBORHOOD AVERAGE", "NEIGHBORHOOD AVERAGE", "NEIGHBORHOOD AVERAGE", "NEIGHBORHOOD AVERAGE"]})        
    
    chart3_data = chart3_data.append(nb_mean, ignore_index = True)

    #3) EUI trend_chart ######################################

    chart3_plot = (alt.Chart(chart3_data)
                    .mark_line(point=True)
                    .encode(
                        x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                        y= alt.Y("SiteEUIWN(kBtu/sf)"),
                        color = "Type",
                        tooltip=["SiteEUIWN(kBtu/sf)"]))
    
    st.altair_chart(chart3_plot, use_container_width=True)

    #4) ES trend_selected ######################################

    st.write("**2) Energy Star score: Your Building vs. {ZIP} neighborhood in the city of Seattle**".format(ZIP = int(ZipInput)))
    chart4_data = pd.concat([chart2_year, chart2_es], axis=1)
    chart4_data["Type"] = "YOUR BUILDING"        
            
    #5) ES trend_city mean ######################################

    city_search = df[df['PrimaryPropertyType'] == (TypeInput)]
    nb_search = city_search[city_search['ZipCode'] == (ZipInput)]
            
    mean16 = nb_search[nb_search["DataYear"] == 2016]["ENERGYSTARScore"].mean()
    mean17 = nb_search[nb_search["DataYear"] == 2017]["ENERGYSTARScore"].mean()
    mean19 = nb_search[nb_search["DataYear"] == 2019]["ENERGYSTARScore"].mean()
    mean20 = nb_search[nb_search["DataYear"] == 2020]["ENERGYSTARScore"].mean()
    mean16 = round(mean16, 1)
    mean17 = round(mean17, 1)
    mean19 = round(mean19, 1)
    mean20 = round(mean20, 1)
    
    nb_mean = pd.DataFrame({"DataYear":[2016, 2017, 2019, 2020],
                                "ENERGYSTARScore": [mean16, mean17, mean19, mean20],
                                "Type": ["NEIGHBORHOOD AVERAGE", "NEIGHBORHOOD AVERAGE", "NEIGHBORHOOD AVERAGE", "NEIGHBORHOOD AVERAGE"]})        
    
    chart4_data = chart4_data.append(nb_mean, ignore_index = True)
    
    #6)ES trend_chart ######################################

    chart4_plot = (alt.Chart(chart4_data)
                    .mark_line(point=True)
                    .encode(
                        x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                        y= alt.Y("ENERGYSTARScore"),
                        color = "Type",
                        tooltip=["ENERGYSTARScore"]))
    
    st.altair_chart(chart4_plot, use_container_width=True)        
    
    ################# CHATPER 1-3

    st.write("**1-3. BUILDING LEVEL EFFICIENCY**")
    st.write("Let's compare the efficiency with the energy sources used in your building")
    st.write("**1) EUI: Your Efficiency and Energy sources**")  

    #1) Energe Source trend_table ######################################

    chart5_year1 = df_result_search["DataYear"]
    chart5_use1 = df_result_search["Electricity(kBtu)"]
    chart5_use1 = chart5_use1.rename("Total Consumption(kBtu)")
    chart5_data1 = pd.concat([chart5_year1, chart5_use1], axis=1)
    chart5_data1["Total Consumption(kBtu)"] = chart5_data1["Total Consumption(kBtu)"].fillna(0)
    chart5_data1["Type"] = "Electricity"
    
    chart5_year2 = df_result_search["DataYear"]
    chart5_use2 = df_result_search["NaturalGas(kBtu)"]
    chart5_use2 = chart5_use2.rename("Total Consumption(kBtu)")
    chart5_data2 = pd.concat([chart5_year2, chart5_use2], axis=1)
    chart5_data2["Total Consumption(kBtu)"] = chart5_data2["Total Consumption(kBtu)"].fillna(0)
    chart5_data2["Type"] = "Natural Gas"
    
    chart5_year3 = df_result_search["DataYear"]
    chart5_use3 = df_result_search["SteamUse(kBtu)"]
    chart5_use3 = chart5_use3.rename("Total Consumption(kBtu)")
    chart5_data3 = pd.concat([chart5_year3, chart5_use3], axis=1)
    chart5_data3["Total Consumption(kBtu)"] = chart5_data3["Total Consumption(kBtu)"].fillna(0)
    chart5_data3["Type"] = "Steam"
    
    chart5_data = chart5_data1.append(chart5_data2, ignore_index = True)
    chart5_data = chart5_data.append(chart5_data3, ignore_index = True)

    #2) EUI + Energe Source trend_chart ######################################

    cols = st.columns(2)
    
    with cols[0]:
        chart6_year = df_result_search["DataYear"]
        chart6_eui = df_result_search["SiteEUIWN(kBtu/sf)"]
        chart6_data = pd.concat([chart6_year, chart6_eui], axis=1)
        chart6_plot = (alt.Chart(chart6_data)
                        .mark_line(point=True)
                        .encode(
                            x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                            y= alt.Y("SiteEUIWN(kBtu/sf)"),
                            tooltip=["SiteEUIWN(kBtu/sf)"])
                        .configure_mark(color="#FA852D"))
        
        st.altair_chart(chart6_plot, use_container_width=True)


    with cols[1]:
        chart5_plot = (alt.Chart(chart5_data)
                        .mark_bar(size=20)
                        .encode(
                            x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                            y= alt.Y("Total Consumption(kBtu)", stack="zero"),
                            color = alt.Color("Type", scale=alt.Scale(scheme="set3")),
                            tooltip=["Total Consumption(kBtu)"]))
        
        
        bar = st.altair_chart(chart5_plot, use_container_width=True)        

    
    st.write("**2) Energy Star Score: Your Efficiency and Energy sources**")
    
    #3) ES Score + Energe Source trend_chart ######################################

    cols = st.columns(2)
    
    with cols[0]:
        chart7_year = df_result_search["DataYear"]
        chart7_es = df_result_search["ENERGYSTARScore"]            
        chart7_data = pd.concat([chart7_year, chart7_es], axis=1)
        chart7_plot = (alt.Chart(chart7_data)
                        .mark_line(point=True)
                        .encode(
                            x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                            y= alt.Y("ENERGYSTARScore"),
                            tooltip=["ENERGYSTARScore"])
                        .configure_mark(color="#FA852D"))
        
        st.altair_chart(chart7_plot, use_container_width=True)

    with cols[1]:
        chart5_plot = (alt.Chart(chart5_data)
                        .mark_bar(size=20)
                        .encode(
                            x= alt.X("DataYear:O", axis=alt.Axis(values=df["DataYear"].unique(), labelAngle=0)),
                            y= alt.Y("Total Consumption(kBtu)", stack="zero"),
                            color = alt.Color("Type", scale=alt.Scale(scheme="set3")),
                            tooltip=["Total Consumption(kBtu)"]))        
        
        bar = st.altair_chart(chart5_plot, use_container_width=True)

    ################# CHAPTER 2
    

    df_result_search = df[df["OSEBuildingID"] == df_point.iloc[0]["OSEBuildingID"]]

    st.subheader("2. WHICH CHARACTERISTICS OF YOUR BUILDING SHOULD BE REVIEWED IN TERMS OF ENERGY EFFICIENCY?")

    #pick property of selected building 
    df_selectedProperty =  df_result_search[df_result_search["DataYear"] == 2020]

    #drop outliers
    df = df[df['SiteEUIWN(kBtu/sf)']<1000]

    #fill blanks
    df["SiteEUIWN(kBtu/sf)"] = df["SiteEUIWN(kBtu/sf)"].fillna(0)

    selectedProperty = df_selectedProperty.iloc[0]["LargestPropertyUseType"]
    st.write(f"2-1. Do {selectedProperty}s use more energy as compared to other program types?")     

    #new data frame for order of programs as per EUI
    def getTop10Inclusive(colName, df, dfSelectedPoint):
        plot_data = df[df['SiteEUIWN(kBtu/sf)']<1000].groupby([colName])\
            .agg(SiteEUI = ("SiteEUIWN(kBtu/sf)","mean")).sort_values(by=["SiteEUI"],ascending=True)

        plot_data = plot_data.reset_index()
        plot_data.index.names = ["index"]
        plot_data.columns = [colName,'SiteEUI']
        plot_data_9 = plot_data[:9]   

        selectedProperty = dfSelectedPoint.iloc[0][colName]

        if selectedProperty in list(plot_data_9[colName]):
            plot_data_10 = plot_data[:10]
        else:
            plot_data_selected = plot_data[plot_data[colName] == selectedProperty]
            plot_data_10 = pd.concat([plot_data_9, plot_data_selected]).sort_values(by=["SiteEUI"],ascending=True)
        return plot_data_10


    largestProperty_10 = getTop10Inclusive("LargestPropertyUseType", df, df_selectedProperty)

    #graph
    histProgram = alt.Chart(largestProperty_10).mark_bar().encode(
            alt.X("LargestPropertyUseType", title = "Program", sort = "-y", axis=alt.Axis(labelAngle = -30)), 
            alt.Y("SiteEUI"),
            color = alt.condition(
            alt.datum["LargestPropertyUseType"] == df_selectedProperty.iloc[0]["LargestPropertyUseType"],  # If the year is 1810 this test returns True,
            alt.value('orange'),     # which sets the bar orange.
            alt.value('steelblue'))
    
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )
    st.altair_chart(histProgram, use_container_width=True)

    

    #filters to choose for the user
    df99 = [df.columns[6],df.columns[11],df.columns[14],df.columns[13],df.columns[29]]
    

    #pick 2020
    df1 = df[(df['DataYear'] == 2020) & (df['LargestPropertyUseType'] == selectedProperty)]

    st.write("2-2. During 2020, how does the neighborhood of your building compare with the best performing neighborhood in the city of Seattle?")
    filtered = "ZipCode"
    dfChart = getTop10Inclusive(filtered, df1, df_selectedProperty)

    # graph
    hist1 = alt.Chart(dfChart).mark_bar().encode(
        alt.X(filtered,type = "ordinal", axis=alt.Axis(labelAngle = -30), sort = "-y"), 
        alt.Y("SiteEUI",aggregate="mean"),
        color = alt.condition(
            alt.datum[filtered] == df_selectedProperty.iloc[0][filtered],  # If the year is 1810 this test returns True,
            alt.value('orange'),     # which sets the bar orange.
            alt.value('steelblue'))
        # alt.Color("Species")
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )
    st.altair_chart(hist1, use_container_width=True)

    st.write("2-3. During 2020, how do the buildings built in this year compare with the buildings built in other years?")
    filtered = "YearBuilt"
    dfChart = getTop10Inclusive(filtered, df1, df_selectedProperty)

    # graph
    hist1 = alt.Chart(dfChart).mark_bar().encode(
        alt.X(filtered,type = "ordinal", axis=alt.Axis(labelAngle = -30), sort = "-y"), 
        alt.Y("SiteEUI",aggregate="mean"),
        color = alt.condition(
            alt.datum[filtered] == df_selectedProperty.iloc[0][filtered],  # If the year is 1810 this test returns True,
            alt.value('orange'),     # which sets the bar orange.
            alt.value('steelblue'))
        # alt.Color("Species")
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )
    st.altair_chart(hist1, use_container_width=True)

    st.write("2-4. During 2020, how do buildings with similar gross floor area compare with the other buildings with different size in the city of Seattle?")
    filtered = "PropertyGFABuilding(s)"
    dfChart = getTop10Inclusive(filtered, df1, df_selectedProperty)

    # graph
    hist1 = alt.Chart(dfChart).mark_bar().encode(
        alt.X(filtered,type = "ordinal", axis=alt.Axis(labelAngle = -30), sort = "-y"), 
        alt.Y("SiteEUI",aggregate="mean"),
        color = alt.condition(
            alt.datum[filtered] == df_selectedProperty.iloc[0][filtered],  # If the year is 1810 this test returns True,
            alt.value('orange'),     # which sets the bar orange.
            alt.value('steelblue'))
        # alt.Color("Species")
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )
    st.altair_chart(hist1, use_container_width=True)

    st.write("2-5. During 2020, how do buildings with same floors as my building compare with the other buildings with different number of floors?")
    filtered = "NumberofFloors"
    dfChart = getTop10Inclusive(filtered, df1, df_selectedProperty)

    # graph
    hist1 = alt.Chart(dfChart).mark_bar().encode(
        alt.X(filtered,type = "ordinal", axis=alt.Axis(labelAngle = -30), sort = "-y"), 
        alt.Y("SiteEUI",aggregate="mean"),
        color = alt.condition(
            alt.datum[filtered] == df_selectedProperty.iloc[0][filtered],  # If the year is 1810 this test returns True,
            alt.value('orange'),     # which sets the bar orange.
            alt.value('steelblue'))
        # alt.Color("Species")
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )
    st.altair_chart(hist1, use_container_width=True)

    st.write("2-6. During 2020, how do buildings with similar electricity consumption compare other buildings in the city of Seattle with varying consumption?")
    filtered = "Electricity(kBtu)"
    dfChart = getTop10Inclusive(filtered, df1, df_selectedProperty)

    # graph
    hist1 = alt.Chart(dfChart).mark_bar().encode(
        alt.X(filtered,type = "ordinal", axis=alt.Axis(labelAngle = -30), sort = "-y"), 
        alt.Y("SiteEUI",aggregate="mean"),
        color = alt.condition(
            alt.datum[filtered] == df_selectedProperty.iloc[0][filtered],  # If the year is 1810 this test returns True,
            alt.value('orange'),     # which sets the bar orange.
            alt.value('steelblue'))
        # alt.Color("Species")
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )
    st.altair_chart(hist1, use_container_width=True)
