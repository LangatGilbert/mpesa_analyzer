#modules/packages required
import os

import base64

#for data manipulation/wrangling
import numpy as np
from numpy import int64
import pandas as pd
pd.options.display.float_format = "{:,.2f}".format

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
st.set_page_config(page_title ="M-Pesa Transactions Analysis Dashboard",page_icon=":bar_chart:", layout="wide")

from mpesa_analyser import pdf_cleaner_wrangler

#for pdf extraction as pdf
import tabula
from tabula.io import read_pdf


# Supress unnecessary warnings so that presentation looks clean
import warnings
warnings.filterwarnings('ignore')

header = st.container()
dataset =  st.container()
data_headline = st.container()
sidebar_contents =  st.container()

#st.cache
with header:
    #setting up the title
    st.title(":bar_chart: M-Pesa Transactions Analysis Dashboard")
    
    st.markdown("""
    This helps you understand your M-Pesa inflows and outflows within a specified period. The Goal is to answer the following:
    * Where does majority of my inflows come from?
    * Where does my outflows go to?
    * Who are top merchants I transact with?
    * Which bills do I pay often?
    """
    )

with dataset:
    st.sidebar.title("Please upload pdf here:")
    
    #insert file uploading sidebar
    uploaded_file = st.sidebar.file_uploader("Upload your M-Pesa statement:", type=["pdf"]) 

    #input the pdf password
    password = st.sidebar.text_input("Input your pdf password","Type Here",type = 'password')

    #if uploaded_file is not None:
        
    dfs = tabula.read_pdf(uploaded_file,pages="all",multiple_tables=True,password = password,stream=True, lattice=  True)
    
mpesa_df = pdf_cleaner_wrangler(dfs)

with sidebar_contents:
    #select the year of interest
    #st.sidebar.title("Features Selection")
    st.sidebar.subheader("Which year would you like to see?")
    year_options = mpesa_df['year'].unique().tolist()
    selected_year = st.sidebar.selectbox('year',year_options,0)

    #creating select box
    st.sidebar.subheader("Which month would you like to see?")
    sorted_month_group = sorted(mpesa_df.month.unique())
    month_group = st.sidebar.multiselect('month', sorted_month_group, sorted_month_group, key = 'selected_month')


    # Sidebar - Group selection selection
    st.sidebar.subheader("Which transaction category would you like to see?")
    sorted_unique_group = sorted(mpesa_df.ACTIVITY.unique())
    selected_group = st.sidebar.multiselect('transaction category', sorted_unique_group, sorted_unique_group, key = 'selected_trans_group')


#Filtering data
df_selected_group = mpesa_df[(mpesa_df['year']==selected_year) & (mpesa_df.month.isin(month_group)) & (mpesa_df.ACTIVITY.isin(selected_group))]


#TOP KPI's
total_inflows = round(df_selected_group['MONEY IN'].sum(),2)
total_outflows = round(df_selected_group['MONEY OUT'].sum(),2)
total_transactions = int(df_selected_group.shape[0])

left_column, middle_column, right_column = st.columns(3)
with left_column:
    st.subheader("Total Transactions:")
    st.subheader(f"{total_transactions} transactions")
with middle_column:
    st.subheader("Total Inflows:")
    st.subheader(f'Kes {total_inflows:,.2f}')

with right_column:
    st.subheader("Total Outflows:")
    st.subheader(f'Kes {total_outflows:,.2f}')

st.markdown("""---""")

#AGGREGATE BY INFLOWS
money_in = df_selected_group.loc[df_selected_group['category']=='Inflow']
all_inflows = sum(money_in['MONEY IN'])
inflows_aggregations = (money_in.groupby(by=["ACTIVITY"]).sum()[["MONEY IN"]].sort_values(by="MONEY IN"))
inflows_aggregations = inflows_aggregations.reset_index()

labels = inflows_aggregations.ACTIVITY
values = inflows_aggregations["MONEY IN"]
#DONUT CHART
fig_money_in = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
fig_money_in.update_layout(title_text="<b>Inflows</b>")


#AGGREGATE BY INFLOWS
money_out = df_selected_group.loc[df_selected_group['category']=='Outflow']
outflows_aggregations = (money_out.groupby(by=["ACTIVITY"]).sum()[["MONEY OUT"]].sort_values(by="MONEY OUT"))
outflows_aggregations = outflows_aggregations.reset_index()

labels = outflows_aggregations.ACTIVITY
values = outflows_aggregations["MONEY OUT"]
#DONUT CHART
fig_money_out = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
fig_money_out.update_layout(title_text="<b>Outflows</b>")


left_column, right_column = st.columns(2)
left_column.plotly_chart(fig_money_in, use_container_width=True)
right_column.plotly_chart(fig_money_out, use_container_width=True)


st.header('Sample Transactions in the selected period')
st.dataframe(df_selected_group.head())

# Group the data frame by month and item and extract a number of stats from each group
mpesa_agg =df_selected_group.groupby(['COHORT','ACTIVITY'], as_index= False).agg({
                                        # Find the min, max, and sum of the duration column
                                        'MONEY OUT': ["count", sum],
                                        # find the number of network type entries
                                        'MONEY IN': [sum],
                                        # find the number of network type entries
                                        'TOTAL AMOUNT': [sum]
                                                            }
                                                            )

mpesa_agg.columns = [' '.join(col).strip(' sum') for col in mpesa_agg.columns.values]
#mpesa_agg.loc['Total']= mpesa_agg.sum(numeric_only=True, axis=0)
mpesa_agg = mpesa_agg.where(pd.notnull(mpesa_agg), None)



# #show bar of each cateory
agree = st.button("Click to see the visualization")
if agree:
    fig= px.bar(mpesa_agg, x ="COHORT", y = "TOTAL AMOUNT", color ="ACTIVITY", hover_name="ACTIVITY")
    fig.update_layout(width=1200,xaxis={'categoryorder':'category ascending'})
    st.write(fig)


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

# ---- HIDE STREAMLIT STYLE ----
# hide_st_style = """
#             <style>
#             #MainMenu {visibility: hidden;}
#             footer {visibility: hidden;}
#             header {visibility: hidden;}
#             </style>
#             """
# st.markdown(hide_st_style, unsafe_allow_html=True)



