import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io

# Configuration de la page
st.set_page_config(
    page_title="PharmaStock Pro Dashboard",
    page_icon="💊",
    layout="wide"
)

# Titre et description
st.title("💊 PharmaStock Pro - Dashboard Intelligent")
st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    </style>
    <p style='font-size:18px; color: #2E86AB;'>Analyse avancée des stocks pharmaceutiques avec prédictions et alertes intelligentes</p>
""", unsafe_allow_html=True)

# Sidebar pour les paramètres
with st.sidebar:
    st.header("⚙️ Paramètres")
    
    # Mode démo ou upload
    data_source = st.radio(
        "Source de données",
        ["📊 Données démo", "📁 Importer fichier"]
    )
    
    # Paramètres d'alerte
    st.subheader("🚨 Seuils d'alerte")
    alerte_peremption = st.slider("Alerte péremption (jours)", 30, 90, 60)
    alerte_stock = st.slider("Seuil stock faible (%)", 10, 50, 20)
    
    # Paramètres d'affichage
    st.subheader("📈 Options d'affichage")
    show_predictions = st.checkbox("Afficher les prédictions", True)
    show_anomalies = st.checkbox("Détection d'anomalies", True)

# Fonction pour charger les données
@st.cache_data
def load_demo_data():
    np.random.seed(42)
    n_products = 20
    
    categories = ['Antalgique', 'Anti-inflammatoire', 'Antibiotique', 
                  'Cardiologie', 'Gastro-entérologie', 'Dermatologie']
    
    produits = []
    for i in range(n_products):
        cat = np.random.choice(categories)
        produits.append({
            'produit': f"{cat[:3].upper()}-{i+100}",
            'nom_commercial': np.random.choice(['Doliprane', 'Ibuprofène', 'Amoxicilline', 
                                               'Oméprazole', 'Paracétamol', 'Aspirine']),
            'categorie': cat,
            'quantite': np.random.randint(20, 500),
            'date_peremption': (datetime.now() + timedelta(days=np.random.randint(30, 730))).strftime('%Y-%m-%d'),
            'prix_achat': round(np.random.uniform(2, 150), 2),
            'prix_vente': lambda x: round(x * np.random.uniform(1.3, 2.0), 2),
            'seuil_alerte': np.random.randint(20, 100),
            'fournisseur': np.random.choice(['PharmaDistrib', 'OCP', 'CERP', 'Alliance Healthcare']),
            'code_cip': f"{np.random.randint(1000000, 9999999)}",
            'date_derniere_vente': (datetime.now() - timedelta(days=np.random.randint(0, 60))).strftime('%Y-%m-%d'),
            'ventes_journalieres': np.random.randint(0, 20)
        })
    
    df = pd.DataFrame(produits)
    df['prix_vente'] = df['prix_achat'].apply(lambda x: round(x * np.random.uniform(1.3, 2.0), 2))
    return df

# Fonction pour importer fichier
@st.cache_data
def import_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Format non supporté. Utilisez CSV ou Excel.")
            return None
        return df
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return None

# Chargement des données
if data_source == "📊 Données démo":
    df = load_demo_data()
else:
    uploaded_file = st.sidebar.file_uploader(
        "Choisir un fichier",
        type=['csv', 'xlsx', 'xls'],
        help="Format attendu: colonnes avec produit, categorie, quantite, date_peremption, etc."
    )
    if uploaded_file is not None:
        df = import_file(uploaded_file)
        if df is None:
            st.stop()
    else:
        st.info("👈 Veuillez importer un fichier depuis la sidebar")
        st.stop()

# Traitement des données
df['date_peremption'] = pd.to_datetime(df['date_peremption'])
df['date_derniere_vente'] = pd.to_datetime(df['date_derniere_vente'])
df['jours_restant'] = (df['date_peremption'] - datetime.now()).dt.days
df['stock_alerte'] = df['quantite'] < df['seuil_alerte']
df['peremption_alerte'] = df['jours_restant'] < alerte_peremption
df['valeur_stock'] = df['quantite'] * df['prix_achat']
df['marge'] = df['prix_vente'] - df['prix_achat']
df['marge_taux'] = (df['marge'] / df['prix_achat'] * 100).round(1)
df['rotation'] = df['ventes_journalieres'] * 30  # Rotation mensuelle estimée

# Détection d'anomalies (Méthode simple: écart-type)
if show_anomalies:
    mean_quantite = df['quantite'].mean()
    std_quantite = df['quantite'].std()
    df['anomalie'] = abs(df['quantite'] - mean_quantite) > 2 * std_quantite

# 1. KPIs PRINCIPAUX
st.header("📊 Indicateurs Clés de Performance")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "💰 Valeur totale stock",
        f"{df['valeur_stock'].sum():,.0f} €",
        delta=f"{df['valeur_stock'].mean():,.0f} €/réf"
    )

with col2:
    stock_faible = len(df[df['stock_alerte']])
    st.metric(
        "⚠️ Stock faible",
        stock_faible,
        delta=f"{stock_faible/len(df)*100:.1f}% du total",
        delta_color="inverse"
    )

with col3:
    peremption = len(df[df['peremption_alerte']])
    st.metric(
        "⏳ Alerte péremption",
        peremption,
        delta=f"{peremption/len(df)*100:.1f}%",
        delta_color="inverse"
    )

with col4:
    marge_moy = df['marge_taux'].mean()
    st.metric(
        "📈 Marge moyenne",
        f"{marge_moy:.1f}%",
        delta=f"{df['marge_taux'].max():.1f}% max"
    )

with col5:
    rotation_moy = df['rotation'].mean()
    st.metric(
        "🔄 Rotation stock",
        f"{rotation_moy:.0f} unités/mois",
        delta=f"{df['rotation'].max():.0f} max"
    )

# 2. GRAPHIQUES AVANCÉS
st.header("📈 Analyses Graphiques")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Distribution", "📉 Tendances", "💰 Financier", "🎯 Prédictions"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution par catégorie (Treemap amélioré)
        fig1 = px.treemap(
            df, 
            path=['categorie', 'produit'], 
            values='quantite',
            color='valeur_stock',
            color_continuous_scale='RdYlGn',
            title="Répartition du stock par catégorie"
        )
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Boxplot des quantités par catégorie
        fig2 = px.box(
            df, 
            x='categorie', 
            y='quantite',
            color='categorie',
            title="Distribution des quantités par catégorie",
            points="all"
        )
        fig2.update_layout(height=500)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Histogramme des péremptions
    fig3 = px.histogram(
        df, 
        x='jours_restant',
        nbins=30,
        color='categorie',
        title="Distribution des dates de péremption",
        labels={'jours_restant': 'Jours restants avant péremption'}
    )
    fig3.add_vline(x=alerte_peremption, line_dash="dash", line_color="red")
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique en barres des stocks
        top_stocks = df.nlargest(10, 'quantite')[['produit', 'quantite', 'categorie']]
        fig4 = px.bar(
            top_stocks,
            x='quantite',
            y='produit',
            color='categorie',
            orientation='h',
            title="Top 10 produits par quantité"
        )
        fig4.update_layout(height=500)
        st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        # Analyse des ventes
        ventes_par_cat = df.groupby('categorie')['ventes_journalieres'].mean().reset_index()
        fig5 = px.pie(
            ventes_par_cat,
            values='ventes_journalieres',
            names='categorie',
            title="Répartition des ventes par catégorie",
            hole=0.4
        )
        fig5.update_layout(height=500)
        st.plotly_chart(fig5, use_container_width=True)
    
    # Heatmap des corrélations
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    corr_matrix = df[numeric_cols].corr()
    fig6 = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="Matrice de corrélation - Analyses statistiques",
        color_continuous_scale='RdBu'
    )
    fig6.update_layout(height=600)
    st.plotly_chart(fig6, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        # Valeur du stock par catégorie
        stock_value = df.groupby('categorie')['valeur_stock'].sum().reset_index()
        fig7 = px.bar(
            stock_value,
            x='categorie',
            y='valeur_stock',
            color='categorie',
            title="Valeur du stock par catégorie (€)"
        )
        fig7.update_layout(height=500)
        st.plotly_chart(fig7, use_container_width=True)
    
    with col2:
        # Analyse des marges
        fig8 = px.scatter(
            df,
            x='prix_achat',
            y='prix_vente',
            size='quantite',
            color='categorie',
            hover_data=['produit'],
            title="Relation Prix d'achat vs Prix de vente"
        )
        # Ligne de marge nulle
        max_price = max(df['prix_vente'].max(), df['prix_achat'].max())
        fig8.add_trace(
            go.Scatter(
                x=[0, max_price],
                y=[0, max_price],
                mode='lines',
                name='Marge nulle',
                line=dict(dash='dash', color='gray')
            )
        )
        fig8.update_layout(height=500)
        st.plotly_chart(fig8, use_container_width=True)

with tab4:
    if show_predictions:
        col1, col2 = st.columns(2)
        
        with col1:
            # Prédiction simple de rupture de stock
            df_pred = df.copy()
            df_pred['jours_rupture'] = (df_pred['quantite'] / df_pred['ventes_journalieres'].replace(0, 1)).round()
            df_pred = df_pred[df_pred['jours_rupture'] < 30].nlargest(10, 'jours_rupture')
            
            if not df_pred.empty:
                fig9 = px.bar(
                    df_pred,
                    x='produit',
                    y='jours_rupture',
                    color='categorie',
                    title="Produits à risque de rupture (< 30 jours)"
                )
                fig9.update_layout(height=500)
                st.plotly_chart(fig9, use_container_width=True)
        
        with col2:
            # Analyse prédictive des péremptions
            peremption_pred = df[df['jours_restant'] < 90].nlargest(15, 'jours_restant')
            if not peremption_pred.empty:
                fig10 = px.timeline(
                    peremption_pred,
                    x_start=datetime.now(),
                    x_end='date_peremption',
                    y='produit',
                    color='categorie',
                    title="Calendrier des péremptions (90 jours)"
                )
                fig10.update_layout(height=500)
                st.plotly_chart(fig10, use_container_width=True)
    else:
        st.info("Activez les prédictions dans les paramètres pour voir cette section")

# 3. ANALYSES STATISTIQUES AVANCÉES
st.header("🔬 Analyses Statistiques Approfondies")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Statistiques descriptives")
    stats_df = df[['quantite', 'prix_achat', 'prix_vente', 'marge_taux', 'jours_restant']].describe()
    st.dataframe(stats_df.style.format("{:.2f}"), use_container_width=True)

with col2:
    st.subheader("🎯 Analyse par fournisseur")
    fournisseur_stats = df.groupby('fournisseur').agg({
        'valeur_stock': 'sum',
        'produit': 'count',
        'marge_taux': 'mean'
    }).round(2)
    fournisseur_stats.columns = ['Valeur stock (€)', 'Nb produits', 'Marge moyenne (%)']
    st.dataframe(fournisseur_stats.style.format("{:.2f}"), use_container_width=True)

# 4. TABLEAUX DE BORD DÉTAILLÉS
st.header("📋 Gestion détaillée")

# Filtres interactifs
with st.expander("🔍 Filtres avancés", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        categories_filter = st.multiselect("Catégories", options=df['categorie'].unique())
    with col2:
        fournisseur_filter = st.multiselect("Fournisseurs", options=df['fournisseur'].unique())
    with col3:
        alerte_filter = st.selectbox("Filtrer par alerte", ["Tous", "Stock faible", "Péremption", "Anomalies"])

# Application des filtres
df_filtered = df.copy()
if categories_filter:
    df_filtered = df_filtered[df_filtered['categorie'].isin(categories_filter)]
if fournisseur_filter:
    df_filtered = df_filtered[df_filtered['fournisseur'].isin(fournisseur_filter)]
if alerte_filter == "Stock faible":
    df_filtered = df_filtered[df_filtered['stock_alerte']]
elif alerte_filter == "Péremption":
    df_filtered = df_filtered[df_filtered['peremption_alerte']]
elif alerte_filter == "Anomalies":
    df_filtered = df_filtered[df_filtered['anomalie']]

# Affichage du tableau
st.dataframe(
    df_filtered[[
        'produit', 'nom_commercial', 'categorie', 'fournisseur',
        'quantite', 'seuil_alerte', 'jours_restant', 'valeur_stock',
        'marge_taux', 'stock_alerte', 'peremption_alerte'
    ]].style.applymap(
        lambda x: 'background-color: #ffcccc' if x == True else '',
        subset=['stock_alerte', 'peremption_alerte']
    ),
    use_container_width=True,
    height=400
)

# 5. EXPORT ET RAPPORTS
st.header("📥 Export et Rapports")

col1, col2, col3 = st.columns(3)

with col1:
    # Export CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger CSV",
        data=csv,
        file_name=f"pharma_stock_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col2:
    # Rapport des alertes
    alertes_df = df[df['stock_alerte'] | df['peremption_alerte']]
    if not alertes_df.empty:
        st.info(f"📊 {len(alertes_df)} alertes actives")
        if st.button("Voir rapport détaillé"):
            st.dataframe(alertes_df)

with col3:
    # Synthèse exécutive
    if st.button("📑 Générer synthèse"):
        st.success(f"""
        **Synthèse exécutive**:
        - Valeur totale: {df['valeur_stock'].sum():,.0f}€
        - Références: {len(df)}
        - Alertes: {len(alertes_df)}
        - Rotation moyenne: {df['rotation'].mean():.0f} unités/mois
        - Produits à risque: {len(df[df['jours_restant'] < 30])}
        """)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>PharmaStock Pro v2.0 - Dashboard Intelligent pour la Gestion Pharmaceutique</p>
        <p>Développé avec Streamlit • Données temps réel • Analyses prédictives</p>
    </div>
""", unsafe_allow_html=True)
