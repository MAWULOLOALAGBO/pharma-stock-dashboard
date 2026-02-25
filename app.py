import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.title("📊 Gestion de Stock Pharmaceutique")

# Données démo
@st.cache_data
def load_data():
    data = {
        'produit': ['Paracétamol 500mg', 'Ibuprofène 400mg', 'Amoxicilline 1g', 'Oméprazole 20mg'],
        'categorie': ['Antalgique', 'Anti-inflammatoire', 'Antibiotique', 'IPP'],
        'quantite': [150, 89, 45, 120],
        'date_peremption': ['2025-06-15', '2025-08-20', '2025-04-10', '2025-12-01'],
        'prix_achat': [2.50, 3.20, 8.50, 4.80],
        'seuil_alerte': [50, 30, 20, 40]
    }
    return pd.DataFrame(data)

df = load_data()
df['date_peremption'] = pd.to_datetime(df['date_peremption'])
df['jours_restant'] = (df['date_peremption'] - datetime.now()).dt.days

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Références totales", len(df))
col2.metric("Alertes péremption", len(df[df['jours_restant'] < 60]))
col3.metric("Stock faible", len(df[df['quantite'] < df['seuil_alerte']]))

# Alertes
st.subheader("🚨 Alertes prioritaires")
alertes = df[(df['jours_restant'] < 60) | (df['quantite'] < df['seuil_alerte'])]
st.dataframe(alertes[['produit', 'quantite', 'jours_restant', 'categorie']])

# Visualisation
fig = px.treemap(df, path=['categorie', 'produit'], values='quantite', 
                 color='jours_restant', color_continuous_scale='RdYlGn')
st.plotly_chart(fig, use_container_width=True)

# Upload fichier client
st.subheader("📁 Importer vos données")
uploaded = st.file_uploader("CSV avec colonnes: produit, categorie, quantite, date_peremption, prix_achat, seuil_alerte")
if uploaded:
    df_client = pd.read_csv(uploaded)
    st.success("Fichier chargé ! Actualisez pour voir vos données.")
