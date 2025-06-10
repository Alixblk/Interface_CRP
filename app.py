import streamlit as st
import ezc3d
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="CRP App", layout="wide")
st.title("🦵 Analyse du CRP à partir de fichiers .c3d")

uploaded_files = st.file_uploader("Importe un ou plusieurs fichiers .c3d", type="c3d", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"Fichier : {file.name}")

        try:
            c3d = ezc3d.c3d(BytesIO(file.read()))
        except Exception as e:
            st.error(f"Erreur de lecture du fichier : {e}")
            continue

        labels = c3d['parameters']['POINT']['LABELS']['value']
        st.write(f"**Labels disponibles ({len(labels)}) :**")
        st.write(labels)

        selected_label_1 = st.selectbox("Sélectionne le premier marqueur (ex: hanche gauche)", labels, key=f"label1_{file.name}")
        selected_label_2 = st.selectbox("Sélectionne le second marqueur (ex: épaule droite)", labels, key=f"label2_{file.name}")
        selected_heel_label = st.selectbox("Sélectionne le marqueur du talon (pour segmentation du cycle)", labels, key=f"heel_{file.name}")

        points = c3d['data']['points']  # shape: (4, N_markers, N_frames)
        freq = c3d['header']['points']['frame_rate']
        n_frames = points.shape[2]

        def get_coords(label):
            idx = labels.index(label)
            return points[:3, idx, :].T  # shape: (n_frames, 3)

        coords1 = get_coords(selected_label_1)
        coords2 = get_coords(selected_label_2)

        # Calcul de l'angle 2D entre les deux marqueurs (plan sagittal : x-z)
        def compute_angle_2d(coord1, coord2):
            dx = coord2[:, 0] - coord1[:, 0]
            dz = coord2[:, 2] - coord1[:, 2]
            return np.arctan2(dz, dx)  # radians

        angle_rad = compute_angle_2d(coords1, coords2)

        # Calcul de la vitesse angulaire
        dt = 1 / freq
        angular_velocity = np.gradient(angle_rad, dt)

        st.write("### Exemple de valeurs (angles en radians)")
        df = pd.DataFrame({
            "Angle (rad)": angle_rad[:100],
            "Vitesse angulaire (rad/s)": angular_velocity[:100]
        })
        st.dataframe(df)

        # Tracer les courbes
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(angle_rad, label="Angle (rad)")
        ax.plot(angular_velocity, label="Vitesse angulaire (rad/s)")
        ax.set_title("Angle et vitesse angulaire entre les marqueurs sélectionnés")
        ax.set_xlabel("Frames")
        ax.set_ylabel("Valeurs")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

        st.success("Angles et vitesses calculés avec succès ✅")
