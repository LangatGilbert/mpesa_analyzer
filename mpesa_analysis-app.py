#modules/packages required
import os

import base64

#for data manipulation/wrangling
import numpy as np
from numpy import int64
import pandas as pd

#for data visualization
import matplotlib as mpl
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

#for date manipulation
import datetime as datetime
import calendar

#dashboard creation
import streamlit as st

from mpesa_analyser import pdf_cleaner_wrangler

#for pdf extraction as pdf
import tabula
from tabula.io import read_pdf


# Supress unnecessary warnings so that presentation looks clean
import warnings
warnings.filterwarnings('ignore')

header = st.beta_container()
dataset =  st.beta_container()
data_headline = st.beta_container()
sidebar_contents =  st.beta_container()

with header:
    #setting up the title
    st.title("Analyse your MPESA Transactions")
    
    st.markdown("""
    This is an hobby project trying to understand my expenses|income during a specified period. The Goal is to answer the following:
    * Common income streams 
    * Common expenses
    * Most common merchants I transact
    """
    )

with dataset:
    st.sidebar.title("File Upload:")
    
    #insert file uploading sidebar
    uploaded_file = st.sidebar.file_uploader("Upload your input CSV file", type=["pdf"]) 

    #input the pdf password
    password = st.sidebar.text_input("Input your pdf password","Type Here",type = 'password')

    dfs = tabula.read_pdf(uploaded_file,pages="all",multiple_tables=True,password = password,stream=True, lattice=  True)

    mpesa_df = pdf_cleaner_wrangler(dfs)

with sidebar_contents:
    #select the year of interest
    #st.sidebar.title("Features Selection")
    st.sidebar.subheader("Select Year of Interest")
    selected_year = st.sidebar.selectbox('Transactions Year', list(reversed(range(2019,2021))))

    #creating select box
    st.sidebar.subheader("Select Month of Interest")
    sorted_month_group = sorted(mpesa_df.month.unique())
    month_group = st.sidebar.multiselect('month', sorted_month_group, sorted_month_group, key = 'selected_month')


    # Sidebar - Group selection selection
    st.sidebar.subheader("Select the ACTIVITY of interest")
    sorted_unique_group = sorted(mpesa_df.ACTIVITY.unique())
    selected_group = st.sidebar.multiselect('ACTIVITY', sorted_unique_group, sorted_unique_group, key = 'selected_trans_group')


#Filtering data
df_selected_group = mpesa_df[(mpesa_df['year']==selected_year) & (mpesa_df.month.isin(month_group)) & (mpesa_df.ACTIVITY.isin(selected_group))]


with data_headline:
    inc_col, exp_col = st.beta_columns(2)
    inc_col.markdown(f'''<div class="card text-white bg-info mb-3" style="width: 20rem">
                        <div class="card bg-primary">
                        <div class="card-body">
                            <h5 class="card-title">Total Income</h5>
                            <p class="card-text">{sum(df_selected_group['MONEY IN']):,.2f}</p>
                        </div>
                        </div>''', unsafe_allow_html=True)

    exp_col.markdown(f'''<div class="card text-white bg-info mb-3" style="width: 20rem">
                            <div class="card-body">
                                <h5 class="card-title">Total Expenses</h5>
                                <p class="card-text">{sum(df_selected_group['MONEY OUT']):,.2f}</p>
                            </div>
                            </div>''', unsafe_allow_html=True)



st.header('Display Transactions Stats of Selected Group(s)')
st.write('Data Dimension: ' + str(df_selected_group.shape[0]) + ' rows and ' + str(df_selected_group.shape[1]) + ' columns.')
st.dataframe(df_selected_group)

# #filtering data per the month
# df_month_group = mpesa_df[(mpesa_df.month.isin(month_group))]


# st.header('Display the Monthly Stats of Selected Group(s)')
# st.write('Data Dimension: ' + str(df_month_group.shape[0]) + ' rows and ' + str(df_month_group.shape[1]) + ' columns.')
# st.dataframe(df_month_group)

#Download the csv file.
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href = "data:file/csv;base64,{b64}" download = "df_selected_group.csv">Download CSV File </a>'
    return href

st.markdown(filedownload(df_selected_group), unsafe_allow_html = True)

# Group the data frame by month and item and extract a number of stats from each group
mpesa_agg =df_selected_group.groupby(['COHORT','ACTIVITY','RECIPIENT'], as_index= False).agg({
                                        # Find the min, max, and sum of the duration column
                                        'MONEY OUT': ["count", sum],
                                        # find the number of network type entries
                                        'MONEY IN': [sum],
                                        'TOTAL AMOUNT':[sum]
                                        }
                                        )

mpesa_agg.columns = [' '.join(col).strip() for col in mpesa_agg.columns.values]
mpesa_agg = mpesa_agg.where(pd.notnull(mpesa_agg), None)

#st.dataframe(mpesa_agg)


# #"label+value+percent parent+percent entry+percent root"
# fig =px.treemap(mpesa_agg, path=['transactions_cohort', 'transactions_group','receiver_desc'], values='total_amount sum')
# # this is what I don't like, accessing traces like this
# fig.data[0].textinfo = 'label+text+value+percent root'

# #fig.layout.hovertamplate = '%{label}<br>%{value}'
# fig.data[0].hovertemplate = '%{label}<br>%{value}'
# fig.show()

# #show bar of each cateory
# agree = st.button("Click to a visualization")
# if agree:
#  #st.bar_chart(df_selected_group['transactions_group'])
#  st.plotly_chart(fig)