import streamlit as st
import ezc3d
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title = "Analyse CRP", layout = "wide")
st.title("🧼 Analyse du Continuous Relative Phase (CRP")

# Etape 1 : Importer un ou plusieurs fichiers .c3d
uploaded_files = st.file_uploader(
    "💾 Importer un ou plusieurs fichiers .c3d",
    type = ["c3d"],
    accept_multiple_files = True
)
st.title("Analyse du CRP à partir de fichiers .c3d")

# Étape 1 : Import des fichiers
uploaded_files = st.file_uploader("Importer un ou plusieurs fichiers .c3d", accept_multiple_files = True, type = "c3d")

if uploaded_files:
    st.success(f"{len(uploaded_files)} fichier(s) chargé(s) avec succès !")

    for file in uploaded_files:
        with open(os.path.join("temp_" + file.name), "wb") as f:
            f.write(file.read())

    selected_file = st.selectbox("📂 Choisir un fichier pour l'analyse", [f.name for f in uploaded_files])

    if selected_file:
        path = "temp_" + selected_file
        c3d = ezc3d.c3d(path)

# Étape 2 : sélection des marqueurs d'intérêt
        st.subheader("✅ Prochaine étape : Sélectionner les marqueurs d'intérêt")
        st.markdown("Sélectionnez deux marqueurs (ex: hanche droite, épaule gauche)")

        marker_1 = st.selectbox("Marqueur 1", labels, key = "marker1")
        marker_2 = st.selectbox("Marqueur 2", labels, key = "marker2")

        if marker_1 != marker_2:
            # Récupération des coordonnées
            idx1 = labels.index(marker_1)
            idx2 = labels.index(marker_2)
            coords1 = c3d['data']['points'][:3, idx1, :].T  # (n_frames, 3)
            coords2 = c3d['data']['points'][:3, idx2, :].T

st.success(f"Coordonnées extraites pour {marker_1} et {marker_2} !")

            # Pour afficher un extrait
            st.write("### Extrait des coordonnées (premiers 5 frames) :")
            st.write(f"**{marker_1}**", coords1[:5])
            st.write(f"**{marker_2}**", coords2[:5])

            st.subheader("🏋️ Prête pour l'étape suivante : calcul de la vitesse angulaire → plan de phase → CRP")
        else:
            st.warning("Merci de sélectionner deux marqueurs différents pour le calcul du CRP.")

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
