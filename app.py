import streamlit as st
import ezc3d
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import tempfile

st.set_page_config(page_title="Analyse CRP", layout="centered")
st.title("🧠 Analyse CRP - Interface interactive")

# 1. Upload des fichiers .c3d
st.header("1. Importer un ou plusieurs fichiers .c3d")
uploaded_files = st.file_uploader("Choisissez un ou plusieurs fichiers .c3d", type="c3d", accept_multiple_files=True)

if uploaded_files:
    selected_file = st.selectbox("Choisissez un fichier pour l'analyse", uploaded_files, format_func=lambda x: x.name)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".c3d") as tmp:
        tmp.write(selected_file.read())
        tmp_path = tmp.name

    c3d = ezc3d.c3d(tmp_path)
    labels = c3d['parameters']['POINT']['LABELS']['value']
    st.success("Fichier .c3d chargé avec succès !")

    # 2. Sélection des marqueurs
    st.header("2. Sélection des marqueurs")
    st.write("Labels disponibles :", labels)

    marker1 = st.selectbox("Marqueur 1 (ex. hanche)", labels)
    marker2 = st.selectbox("Marqueur 2 (ex. épaule)", labels)
    heel_marker = st.selectbox("Marqueur du talon (pour détection du cycle)", labels)

    if st.button("Extraire les coordonnées et détecter les contacts"):
        points = c3d['data']['points']  # (4, N_markers, N_frames)
        freq = c3d['header']['points']['frame_rate']
        n_frames = points.shape[2]

        def get_coords(label):
            idx = labels.index(label)
            return points[:3, idx, :].T  # (N_frames, 3)

        coords_1 = get_coords(marker1)
        coords_2 = get_coords(marker2)
        heel_coords = get_coords(heel_marker)

        # Test pour identifier l'axe vertical (Y ou Z)
        st.subheader("Hauteur du talon - vérification")
        avg_range = [np.ptp(heel_coords[:, axis]) for axis in range(3)]
        vertical_axis = np.argmax(avg_range)
        st.write(f"Axe vertical détecté : {'X' if vertical_axis==0 else 'Y' if vertical_axis==1 else 'Z'}")

        heel_height = heel_coords[:, vertical_axis]

        # Détection des minima locaux (contacts talon)
        inverted = -heel_height
        peaks, _ = find_peaks(inverted, distance=int(freq*0.5))
        st.success(f"{len(peaks)} contacts du talon détectés")

        # Affichage de la trajectoire verticale avec contacts
        fig, ax = plt.subplots()
        ax.plot(heel_height, label="Hauteur du talon")
        ax.plot(peaks, heel_height[peaks], "rx", label="Contacts")
        ax.set_title("Trajectoire verticale du talon")
        ax.legend()
        st.pyplot(fig)

        # Extraction d'un cycle complet (entre 2 pics)
        if len(peaks) >= 2:
            start, end = peaks[0], peaks[1]
            vec = coords_2[start:end, [0, 2]] - coords_1[start:end, [0, 2]]  # plan sagittal x-z
            angles = np.arctan2(vec[:, 1], vec[:, 0])
            ang_vel = np.gradient(angles, 1/freq)

            df = pd.DataFrame({
                "Angle (rad)": angles,
                "Vitesse angulaire (rad/s)": ang_vel
            })

            st.header("3. Calcul des angles et vitesses")
            st.line_chart(df)
            st.write(df.head())
        else:
            st.warning("Pas assez de cycles de marche détectés pour extraire un segment.")
