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
    marker1 = st.selectbox("Marqueur d’intérêt 1 (ex. hanche)", labels)
    marker2 = st.selectbox("Marqueur d’intérêt 2 (ex. épaule)", labels)

    # Fonction améliorée pour extraire et normaliser les cycles sans NaN
    def extract_and_normalize_cycles(points, labels, marker_name, valid_cycles):
        idx = labels.index(marker_name)
        signal = points[0, idx, :]  # Plan sagittal
        all_cycles = []

        for i, (start, end) in enumerate(valid_cycles):
            segment = signal[start:end]
            x_original = np.linspace(0, 100, num=len(segment))
            x_interp = np.linspace(0, 100, num=100)

            try:
                f = interp1d(x_original, segment, kind='cubic')
                normalized = f(x_interp)
                if not np.isnan(normalized).any():
                    all_cycles.append(normalized)
                else:
                    st.warning(f"⚠️ Cycle {i+1} pour {marker_name} contient des NaN → exclu automatiquement.")
            except Exception as e:
                st.warning(f"⚠️ Erreur d'interpolation cycle {i+1} pour {marker_name} : {e}")

        return np.array(all_cycles)

    if st.button("Lancer la détection + extraction pour les 2 marqueurs"):
        try:
            # --- Détection des cycles ---
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

            # Extraction + nettoyage des cycles pour les 2 marqueurs
            marker1_cycles = extract_and_normalize_cycles(points, labels, marker1, valid_cycles)
            marker2_cycles = extract_and_normalize_cycles(points, labels, marker2, valid_cycles)

            # --- Visualisation pour marker 1 ---
            if marker1_cycles.size > 0:
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                x = np.linspace(0, 100, 100)
                for cycle in marker1_cycles:
                    ax2.plot(x, cycle, alpha=0.5)
                mean1 = np.mean(marker1_cycles, axis=0)
                ax2.plot(x, mean1, color="black", linewidth=2.5, label="Moyenne")
                ax2.set_title(f"{marker1} - Cycles normalisés (plan sagittal)")
                ax2.set_xlabel("Cycle (%)")
                ax2.set_ylabel("Angle (°)")
                ax2.grid(alpha=0.3)
                ax2.legend()
                st.pyplot(fig2)
            else:
                st.warning(f"Aucun cycle valide pour {marker1} après nettoyage.")

            # --- Visualisation pour marker 2 ---
            if marker2_cycles.size > 0:
                fig3, ax3 = plt.subplots(figsize=(10, 5))
                x = np.linspace(0, 100, 100)
                for cycle in marker2_cycles:
                    ax3.plot(x, cycle, alpha=0.5)
                mean2 = np.mean(marker2_cycles, axis=0)
                ax3.plot(x, mean2, color="black", linewidth=2.5, label="Moyenne")
                ax3.set_title(f"{marker2} - Cycles normalisés (plan sagittal)")
                ax3.set_xlabel("Cycle (%)")
                ax3.set_ylabel("Angle (°)")
                ax3.grid(alpha=0.3)
                ax3.legend()
                st.pyplot(fig3)
            else:
                st.warning(f"Aucun cycle valide pour {marker2} après nettoyage.")

        except Exception as e:
            st.error(f"Erreur pendant l'analyse : {e}")
