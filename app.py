import streamlit as st
import ezc3d
import numpy as np
import pandas as pd
import tempfile

st.title("Analyse CRP - Interface interactive")

# Étape 1 : Import de fichiers C3D
st.header("1. Importer un ou plusieurs fichiers .c3d")
uploaded_files = st.file_uploader("Choisissez un ou plusieurs fichiers .c3d", type="c3d", accept_multiple_files=True)

if uploaded_files:
    selected_file = st.selectbox("Choisissez un fichier pour l'analyse", uploaded_files, format_func=lambda x: x.name)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".c3d") as tmp:
        tmp.write(selected_file.read())
        tmp_path = tmp.name

    c3d = ezc3d.c3d(tmp_path)
    labels = c3d['parameters']['POINT']['LABELS']['value']
    st.success("Fichier chargé avec succès !")

    # Étape 2 : Affichage des labels disponibles
    st.header("2. Sélection des marqueurs")
    st.write("Labels disponibles :", labels)

    marker1 = st.selectbox("Marqueur 1 (par ex. hanche gauche)", labels)
    marker2 = st.selectbox("Marqueur 2 (par ex. épaule droite)", labels)
    heel_marker = st.selectbox("Marqueur du talon (pour segmentation du cycle de marche)", labels)

    if st.button("Extraire les coordonnées"):
        points = c3d['data']['points']  # (4, N_markers, N_frames)
        freq = c3d['header']['points']['frame_rate']

        def get_coords(label):
            idx = labels.index(label)
            return points[:3, idx, :].T  # shape (N_frames, 3)

        coords_1 = get_coords(marker1)
        coords_2 = get_coords(marker2)
        heel_coords = get_coords(heel_marker)

        df_coord = pd.DataFrame(coords_1, columns=['x1', 'y1', 'z1'])
        df_coord[['x2', 'y2', 'z2']] = coords_2

        st.write("### Coordonnées extraites (premiers 5 frames) :")
        st.write(df_coord.head())

        # Étape 3 : Calcul de la vitesse angulaire
        st.header("3. Calcul de la vitesse angulaire")

        # Vecteurs formés par les deux marqueurs (projection 2D dans le plan sagittal x-z)
        vec = coords_2[:, [0, 2]] - coords_1[:, [0, 2]]  # shape (N_frames, 2)

        # Angle θ = arctan2(z, x)
        angles = np.arctan2(vec[:, 1], vec[:, 0])  # en radians

        # Dérivation de l'angle (vitesse angulaire)
        ang_vel = np.gradient(angles, 1/freq)  # rad/s

        df_angles = pd.DataFrame({
            "angle (rad)": angles,
            "vitesse angulaire (rad/s)": ang_vel
        })

        st.line_chart(df_angles.head(200))
        st.success("Angles et vitesses angulaires calculés !")

        st.write("### Exemple de vitesses angulaires :")
        st.write(df_angles.head())
