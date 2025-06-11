import streamlit as st
import ezc3d
import numpy as np
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
    freq = c3d['header']['points']['frame_rate']
    first_frame = c3d['header']['points']['first_frame']
    points = c3d['data']['points']
    n_frames = points.shape[2]
    time = np.arange(n_frames) / freq + first_frame / freq

    st.success("Fichier .c3d chargé avec succès !")

    # 2. Sélection des marqueurs
    st.header("2. Sélection des marqueurs")
    st.write("Labels disponibles :", labels)

    heel_marker = st.selectbox("Marqueur du talon (pour détection des cycles)", labels)
    interest_marker = st.selectbox("Marqueur d’intérêt (ex. hanche, épaule...)", labels)

    if st.button("Lancer la détection + extraction normalisée"):
        # --- Détection des cycles à partir du marqueur talon choisi ---
        try:
            idx_heel = labels.index(heel_marker)
            z_heel = points[2, idx_heel, :]
            inverted_z = -z_heel
            min_distance = int(freq * 0.8)
            peaks, _ = find_peaks(inverted_z, distance=min_distance, prominence=1)

            cycle_starts = peaks[:-1]
            cycle_ends = peaks[1:]
            min_duration = int(0.5 * freq)
            valid_cycles = [(start, end) for start, end in zip(cycle_starts, cycle_ends) if (end - start) >= min_duration]
            n_cycles = len(valid_cycles)

            # Visualisation du signal Z + détection
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            ax1.plot(time, z_heel, label=f"Z ({heel_marker})")
            ax1.plot(time[peaks], z_heel[peaks], "ro", label="Début de cycle")
            ax1.set_title(f"Détection des cycles via {heel_marker}")
            ax1.set_xlabel("Temps (s)")
            ax1.set_ylabel("Hauteur (Z)")
            ax1.grid(alpha=0.3)
            ax1.legend()
            st.pyplot(fig1)
            st.success(f"{n_cycles} cycles valides détectés.")

            # --- Extraction et normalisation des cycles pour le marqueur choisi ---
            idx_interest = labels.index(interest_marker)
            interest_data = points[:, idx_interest, :]  # (4, n_frames)
            interest_sagittal = interest_data[0, :]  # plan sagittal (X)

            normalized_cycles = []
            for start, end in valid_cycles:
                segment = interest_sagittal[start:end]
                x_original = np.linspace(0, 100, num=len(segment))
                x_interp = np.linspace(0, 100, num=100)

                try:
                    f = interp1d(x_original, segment, kind='cubic')
                    norm = f(x_interp)
                    normalized_cycles.append(norm)
                except ValueError:
                    st.warning(f"Erreur d'interpolation : cycle {start}-{end} ignoré.")

            normalized_cycles = np.array(normalized_cycles)

            # --- Visualisation des cycles ---
            if normalized_cycles.size > 0:
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                for i, cycle in enumerate(normalized_cycles):
                    ax2.plot(np.linspace(0, 100, 100), cycle, label=f"Cycle {i+1}")
                ax2.set_title(f"Signal du marqueur {interest_marker} - Normalisé sur 100% du cycle")
                ax2.set_xlabel("Cycle (%)")
                ax2.set_ylabel("Signal (plan sagittal)")
                ax2.grid(alpha=0.3)
                st.pyplot(fig2)
            else:
                st.warning("Aucun cycle utilisable n'a pu être normalisé.")
        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")
