import streamlit as st
import ezc3d
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.title("Analyse du CRP à partir de fichiers .c3d")

# Étape 1 : Import des fichiers
uploaded_files = st.file_uploader("Importer un ou plusieurs fichiers .c3d", accept_multiple_files=True, type="c3d")

if uploaded_files:
    st.success("Fichier(s) importé(s) avec succès ✅")

    # Chargement du premier fichier pour lecture des labels
    file = uploaded_files[0]
    c3d = ezc3d.c3d(BytesIO(file.read()))
    labels = c3d['parameters']['POINT']['LABELS']['value']
    st.write("Labels disponibles :", labels)

    # Étape 2 : Sélection des marqueurs pour le CRP
    st.subheader("Sélection des marqueurs pour le calcul du CRP")
    marker_1 = st.selectbox("Sélectionnez le premier marqueur (ex: hanche)", labels)
    marker_2 = st.selectbox("Sélectionnez le second marqueur (ex: épaule)", labels)
    heel_marker = st.selectbox("Sélectionnez le marqueur du talon (RHEE ou LHEE)", labels)

    # Extraction des coordonnées des marqueurs
    index_1 = labels.index(marker_1)
    index_2 = labels.index(marker_2)
    heel_index = labels.index(heel_marker)

    points = c3d['data']['points']
    freq = c3d['header']['points']['frame_rate']
    n_frames = points.shape[2]
    time = np.linspace(0, n_frames / freq, n_frames)

    coords_1 = points[:3, index_1, :].T  # shape (n_frames, 3)
    coords_2 = points[:3, index_2, :].T
    coords_heel = points[:3, heel_index, :].T

    st.success("Coordonnées extraites. Prêtes pour la suite ✅")

    st.write("Aperçu coordonnées marqueur 1:", pd.DataFrame(coords_1[:5], columns=["x", "y", "z"]))
    st.write("Aperçu coordonnées marqueur 2:", pd.DataFrame(coords_2[:5], columns=["x", "y", "z"]))
    st.write("Aperçu coordonnées talon:", pd.DataFrame(coords_heel[:5], columns=["x", "y", "z"]))

    # Message d'étape suivante
    st.info("🔜 Prochaine étape : Calcul de la vitesse angulaire et plan de phase !")
else:
    st.warning("Veuillez importer au moins un fichier .c3d pour commencer.")
