import streamlit as st
import ezc3d
import os
import tempfile
import numpy as np

st.set_page_config(page_title="Analyse CRP", layout="wide")
st.title("Analyse du CRP – Continuous Relative Phase")

st.markdown("""
Cet outil permet d'importer un ou plusieurs fichiers `.c3d`, de visualiser les labels des marqueurs, puis de poursuivre le pipeline d'analyse (calculs d'angle, phase, CRP, etc.).
""")

# ▶️ Importation des fichiers .c3d
uploaded_files = st.file_uploader("Importer un ou plusieurs fichiers .c3d", type=["c3d"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"Fichier importé : {uploaded_file.name}")

        # Créer un fichier temporaire pour charger avec ezc3d
        with tempfile.NamedTemporaryFile(delete=False, suffix=".c3d") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        # Charger le fichier avec ezc3d
        try:
            c3d = ezc3d.c3d(tmp_path)
            labels = c3d['parameters']['POINT']['LABELS']['value']
            st.success("Fichier chargé avec succès !")
            st.markdown("**Labels disponibles :**")
            st.write(labels)
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")

        # Supprimer le fichier temporaire
        os.remove(tmp_path)

st.markdown("""
---

✅ **Prochaine étape** : Sélectionner les marqueurs d'intérêt (ex. hanche droite, épaule gauche) et extraire leurs coordonnées !
""")