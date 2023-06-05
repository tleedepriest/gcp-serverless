import streamlit as st
import pandas as pd
import numpy as np

FILENAME = "test.csv"

# extract cols from timestamp col...
DATE_COL = "date"
DATETIME_COL = "file_path"
YEAR_COL = "year"

@st.cache_data
def load_data(**kwargs):
    data = pd.read_csv(FILENAME, **kwargs)
    data[YEAR_COL] = data[DATETIME_COL].str.extract(r'(\d{4})')
    #lowercase = lambda x: str(x).lower()
    #data.rename(lowercase, axis='columns', inplace=True)
    return data

st.title("IBJJF Results")
data_load_state = st.text('Loading data...')
data = load_data()
data_load_state.text("Done! (using st.cache_data)")



metric_counts = data.groupby(['file_path', YEAR_COL]).size().reset_index(name='counts').groupby(YEAR_COL).size().reset_index(name="counts")
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(metric_counts)
st.subheader('Number of IBJJF Events Per Year')
#hist_values = np.histogram(metric_counts, bins=len(metric_counts), range=(data[YEAR_COL].min(), data[YEAR_COL].max()))
st.bar_chart(metric_counts, y="counts", x="year")

# Some number in the range 2012-2022
#year_to_filter = st.slider('year', 2012, 2022, 2013)
#filtered_data = data[data[YEAR_COL] == str(year_to_filter)]

#st.subheader('Map of all pickups at %s:00' % hour_to_filter)
#st.map(filtered_data)