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
st.set_page_config(layout="wide")

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

with header:
    #setting up the title
    st.title("ANALYSE  YOUR M-PESA TRANSACTIONS")
    
    st.markdown("""
    This helps you understand your M-Pesa inflows and outflows within a specified period. The Goal is to answer the following:
    * Where does majority of my inflows come from?
    * Where does my outflows go to?
    * Who are top merchants I transact with?
    * Which bills do I pay often?
    """
    )

with dataset:
    st.sidebar.title("FILE UPLOAD:")
    
    #insert file uploading sidebar
    uploaded_file = st.sidebar.file_uploader("Upload your M-Pesa statement", type=["pdf"]) 

    #input the pdf password
    password = st.sidebar.text_input("Input your pdf password","Type Here",type = 'password')

    if uploaded_file is not None:
        
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


        with data_headline:
            inc_col, exp_col = st.columns(2)
            inc_col.markdown(f'''<div class="card text-blue bg-info mb-3" style="width: 20rem">
                                <div class="card-body">
                                    <h5 class="card-title">TOTAL INFLOWS</h5>
                                    <p class="card-text">{sum(df_selected_group['MONEY IN']):,.2f}</p>
                                </div>
                                </div>''', unsafe_allow_html=True)

            exp_col.markdown(f'''<div class="card text-white bg-info mb-3" style="width: 20rem">
                                    <div class="card-body">
                                        <h5 class="card-title">TOTAL OUTFLOWS</h5>
                                        <p class="card-text">{sum(df_selected_group['MONEY OUT']):,.2f}</p>
                                    </div>
                                    </div>''', unsafe_allow_html=True)



        st.header('TRANSACTIONS IN THE SELECTED PERIOD(s)')
        st.write('There are : ' + str(df_selected_group.shape[0]) + ' transactions.')
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



