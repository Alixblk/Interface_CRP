import streamlit as st
import ezc3d
import numpy as np
import os
import tempfile

st.set_page_config(page_title="Analyse CRP", layout="wide")
st.title("🧼 Analyse du Continuous Relative Phase (CRP)")

# Étape 1 : Importer un ou plusieurs fichiers .c3d
uploaded_files = st.file_uploader(
    "💾 Importer un ou plusieurs fichiers .c3d",
    type=["c3d"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} fichier(s) chargé(s) avec succès !")

    for file in uploaded_files:
        with open(os.path.join("temp_" + file.name), "wb") as f:
            f.write(file.read())

    selected_file = st.selectbox("📂 Choisir un fichier pour l'analyse", [f.name for f in uploaded_files])

    if selected_file:
        path = "temp_" + selected_file
        c3d = ezc3d.c3d(path)

        labels = c3d['parameters']['POINT']['LABELS']['value']
        st.write("### 🌍 Liste des marqueurs disponibles :")
        st.write(labels)

        # Étape suivante : sélection des marqueurs d'intérêt
        st.subheader("✅ Prochaine étape : Sélectionner les marqueurs d'intérêt")
        st.markdown("Sélectionnez deux marqueurs (ex: hanche droite, épaule gauche)")

        marker_1 = st.selectbox("Marqueur 1", labels, key="marker1")
        marker_2 = st.selectbox("Marqueur 2", labels, key="marker2")

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
