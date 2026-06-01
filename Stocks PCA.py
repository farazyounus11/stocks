import streamlit as st
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
# Cache the data loading function
import yfinance as yf
st.set_page_config(layout="wide")
st.markdown("### This is a sample of the stock data. I will use statistical techniques like PCA to learn from the data. The data is already scaled and in chronological order!")

@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    zero_counts = (df == 0).sum()
    columns_to_keep = zero_counts[zero_counts <= 100].index
    df = df[columns_to_keep]
    return df

# List of files to choose from
files = "S&P_Price.csv"

# Create a 
# Path to the selected file
file_path = files

# Load and display the data
if file_path:
    df = load_data(file_path)
    st.write(df.head())

    # Transpose the DataFrame
    X = df.T  # Transpose the DataFrame to perform PCA on columns

    # Apply PCA
    n_components = 8
    pca = PCA(n_components=n_components)  # Compute up to 8 components
    X_pca = pca.fit_transform(X)

    # Debugging: Check the shape of X_pca

    st.markdown("### ")


    st.markdown("### After dealing with missing data, I used PCA to reduce the array from 1289 * 482 to 8 * 482. I choose 8 PCs because that captured 91 percent of the variance!")

    # Show explained variance
    explained_variance = pca.explained_variance_ratio_
    # Cumulative explained variance
    cumulative_explained_variance = explained_variance.cumsum()



    col1, col2 = st.columns([5, 1])  



    # Plot the explained variance ratio
    fig_variance = go.Figure()
    fig_variance.add_trace(go.Bar(x=[f'PC{i+1}' for i in range(len(explained_variance))],
                                  y=explained_variance,
                                  name='Explained Variance Ratio'))
    fig_variance.add_trace(go.Scatter(x=[f'PC{i+1}' for i in range(len(cumulative_explained_variance))],
                                      y=cumulative_explained_variance,
                                      mode='lines+markers',
                                      name='Cumulative Explained Variance'))

    fig_variance.update_layout(title='PCA Explained Variance Ratio',
                               xaxis_title='Principal Component',
                               yaxis_title='Variance Ratio',
                               width=1100,
                               height=600)
    

    with col1:
        st.plotly_chart(fig_variance)
    with col2:
        st.write("Cumulative explained variance:")
        st.write(cumulative_explained_variance)


    st.markdown("### Here you can select number of clusters. You can also choose which principal components to view.")


    # Clustering
    num_clusters = st.slider("Select number of clusters:", min_value=9, max_value=20, value=16)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_pca)

    # Prepare data for plotting
    pca_df = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(n_components)])
    pca_df['Cluster'] = clusters
    pca_df['Name'] = X.index  # Use the original column names as names

    # User selects which PCA columns to plot
    col1, col2 = st.columns(2)

    # Place the select boxes in the respective columns
    with col1:
        pc_x = st.selectbox("Select X-axis PCA component:", options=[f'PC{i+1}' for i in range(n_components)], index=0)

    with col2:
        pc_y = st.selectbox("Select Y-axis PCA component:", options=[f'PC{i+1}' for i in range(n_components)], index=1)

    # Plotting with Plotly
    fig = px.scatter(pca_df, x=pc_x, y=pc_y, color='Cluster', text='Name',
                     labels={pc_x: 'Principal Component X', pc_y: 'Principal Component Y'},
                     width=1200, height=800, color_continuous_scale='Viridis')

    # Update the layout to adjust the text position
    fig.update_traces(textposition='top center')

    # Display the Plotly figure in Streamlit
    st.plotly_chart(fig)

st.markdown("### Here you can learn about the industries/sectors in a particular cluster")


selected_cluster = st.slider('Select Cluster Number:', min_value=0, max_value=num_clusters-1, value=6)
pcafilter = pca_df[pca_df['Cluster'] == selected_cluster]

tickers  = pcafilter['Name'].unique()


col11, col22 = st.columns([2, 4])

# Display line charts in each column
with col11:
 data = []

# Fetch sector and industry for each ticker
 for ticker in tickers:
     stock = yf.Ticker(ticker)
     info = stock.info
     sector = info.get('sector', 'N/A')
     industry = info.get('industry', 'N/A')
     data.append({'Ticker': ticker, 'Sector': sector, 'Industry': industry})

# Convert the data into a DataFrame
 industriesss = pd.DataFrame(data)
 st.write(industriesss)
