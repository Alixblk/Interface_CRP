import streamlit as st
import ezc3d
import numpy as np
import pandas as pd
import tempfile
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
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

    # Étape 2 : Affichage des labels disponibles et sélection
    st.header("2. Sélection des marqueurs")
    st.write("Labels disponibles :", labels)

    marker1 = st.selectbox("Marqueur 1 (par ex. hanche gauche)", labels)
    marker2 = st.selectbox("Marqueur 2 (par ex. épaule droite)", labels)
    heel_marker = st.selectbox("Marqueur du talon (pour segmentation du cycle de marche)", labels)

    points = c3d['data']['points']  # (4, N_markers, N_frames)
    freq = c3d['header']['points']['frame_rate']
    time = np.arange(points.shape[2]) / freq

    def get_coords(label):
        idx = labels.index(label)
        return points[:3, idx, :].T  # shape (N_frames, 3)

    coords_1 = get_coords(marker1)
    coords_2 = get_coords(marker2)
    heel_coords = get_coords(heel_marker)

    # Étape 3 : Segmentation du cycle de marche à partir du talon (sur l'axe z)
    st.header("3. Segmentation du cycle de marche")
    heel_z = heel_coords[:, 2]  # axe vertical
    threshold = np.percentile(heel_z, 5)  # proche du sol
    contact_frames = np.where(heel_z < threshold)[0]

    # On détecte les frames où le talon touche le sol
    gait_events = []
    for i in range(1, len(contact_frames)):
        if contact_frames[i] - contact_frames[i - 1] > freq * 0.3:
            gait_events.append(contact_frames[i])

    st.write(f"{len(gait_events)} événements de contact détectés")

    if len(gait_events) >= 2:
        start, end = gait_events[0], gait_events[1]
        st.write(f"Cycle choisi : frames {start} à {end} ({(end - start)/freq:.2f} sec)")

        # On coupe les données au cycle choisi
        coords_1 = coords_1[start:end]
        coords_2 = coords_2[start:end]
        time = time[start:end]

        # Étape 4 : Calcul des angles et vitesses angulaires
        st.header("4. Calcul des angles et vitesses angulaires")

        vec = coords_2[:, [0, 2]] - coords_1[:, [0, 2]]
        angles = np.arctan2(vec[:, 1], vec[:, 0])
        ang_vel = np.gradient(angles, 1/freq)

        df_angles = pd.DataFrame({
            "temps (s)": time,
            "angle (rad)": angles,
            "vitesse angulaire (rad/s)": ang_vel
        })

        st.write("### Tableau interactif")
        st.dataframe(df_angles.round(3))

        # Graphique
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(time, angles, label="Angle (rad)")
        ax.plot(time, ang_vel, label="Vitesse angulaire (rad/s)", linestyle="--")
        ax.set_xlabel("Temps (s)")
        ax.set_ylabel("Valeurs")
        ax.legend()
        ax.grid()
        st.pyplot(fig)

        st.success("Calcul et affichage terminés !")

    else:
        st.warning("Pas assez de cycles de marche détectés pour l'analyse.")
