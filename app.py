import streamlit as st
import ezc3d
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.interpolate import interp1d
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

# Filtrer uniquement les marqueurs de talon gauche ou droit
    heel_options = [label for label in labels if label in ["LHEE", "RHEE"]]
if heel_options:
    heel_marker = st.selectbox("Marqueur du talon (pour détection du cycle)", heel_options)
else:
        st.warning("Aucun marqueur 'LHEE' ou 'RHEE' trouvé dans ce fichier.")

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

if st.button("Lancer l'analyse CRP complète (avec extraction de cycles normalisés)"):
    if heel_marker != "LHEE":
        st.warning("Cette étape est prévue uniquement avec le marqueur LHEE pour l'instant.")
    else:
        # Recalcul utile dans le contexte Streamlit
        idx_lhee = labels.index("LHEE")
        z_lhee = points[2, idx_lhee, :]
        inverted_z = -z_lhee
        min_distance = int(freq * 0.8)

        peaks, _ = find_peaks(inverted_z, distance=min_distance, prominence=1)
        lhee_cycle_start_indices = peaks[:-1]
        lhee_cycle_end_indices = peaks[1:]
        min_lhee_cycle_duration = int(0.5 * freq)

        lhee_valid_cycles = [
            (start, end) for start, end in zip(lhee_cycle_start_indices, lhee_cycle_end_indices)
            if (end - start) >= min_lhee_cycle_duration
        ]
        lhee_n_cycles = len(lhee_valid_cycles)

# Affichage du signal + détection
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        time = np.arange(n_frames) / freq + first_frame / freq
        ax1.plot(time, z_lhee, label="Z (LHEE)")
        ax1.plot(time[peaks], z_lhee[peaks], "ro", label="Début de cycle")
        ax1.set_title("Détection des cycles via LHEE")
        ax1.set_xlabel("Temps (s)")
        ax1.set_ylabel("Hauteur (axe Z)")
        ax1.grid(alpha=0.3)
        ax1.legend()
        st.pyplot(fig1)

        st.success(f"{lhee_n_cycles} cycles valides détectés.")

# ➕ Extraction des angles LHipAngles pour chaque cycle
        if "LHipAngles" in labels:
            idx_lhip_angle = labels.index("LHipAngles")
            lhip_angle_data = points[:, idx_lhip_angle, :]
            angle_lhip_sagittal = lhip_angle_data[0, :]  # plan sagittal (X)

            lhip_cycles = []

            for start, end in lhee_valid_cycles:
                lhip_angle_cycle = angle_lhip_sagittal[start:end]

                x_original = np.linspace(0, 100, num=len(lhip_angle_cycle))
                x_interp = np.linspace(0, 100, num=100)

                try:
                    f = interp1d(x_original, lhip_angle_cycle, kind='cubic')
                    normalized_lhip_cycle = f(x_interp)
                    lhip_cycles.append(normalized_lhip_cycle)
                except ValueError:
                    st.warning(f"Erreur d'interpolation sur le cycle {start}-{end}. Cycle ignoré.")

            lhip_cycles = np.array(lhip_cycles)

# 🖼️ Visualisation
            if lhip_cycles.size > 0:
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                for i, cycle in enumerate(lhip_cycles):
                    ax2.plot(np.linspace(0, 100, 100), cycle, label=f"Cycle {i+1}")
                ax2.set_title("Angles hanche gauche (LHipAngles) - plan sagittal")
                ax2.set_xlabel("Cycle (%)")
                ax2.set_ylabel("Angle (°)")
                ax2.grid(alpha=0.3)
                st.pyplot(fig2)
            else:
                st.warning("Aucun cycle utilisable n'a pu être normalisé correctement.")
        else:
            st.warning("Le marqueur 'LHipAngles' n'est pas disponible dans ce fichier.")
