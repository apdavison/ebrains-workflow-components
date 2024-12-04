#!/usr/bin/env python

import argparse
from pathlib import Path

import numpy as np
import quantities as pq
import matplotlib.pyplot as plt
import elephant
from utils import load_data, select_data


def freq_list(value):
    try:
        frequency = float(value)
        return np.atleast_1d([frequency])
    except ValueError:
        parts = value.split(":")

        start = float(parts[0]) if parts[0] else 0
        step = float(parts[2]) if len(parts) > 2 and parts[2] else 1.0
        stop = float(parts[1]) + step if len(parts) > 1 and parts[1] else step

        return np.arange(start, stop, step, dtype=float)


CLI = argparse.ArgumentParser()
CLI.add_argument("--input_file", nargs="?", type=Path, required=True, help="path with file with the input data")
CLI.add_argument("--input_format", nargs="?", type=str, default=None, help="format of the input data")
CLI.add_argument("--output_file", nargs="?", type=Path, required=True, help="path to the file where to write data")
CLI.add_argument("--block_index", nargs="?", type=int, default=0, help="Index of the block to process (default: 0)")
CLI.add_argument("--block_name", nargs="?", type=str, default=None, help="Name of the block to process (optional)")
CLI.add_argument("--segment_index", nargs="?", type=int, default=0, help="Index of the segment to process (default: 0)")
CLI.add_argument("--analog_signal_index", nargs="?", type=int, default=0, help="Index of the analog signal to process (default: 0)")
CLI.add_argument("--visualization_plots", type=bool, default=True, help="Generate visualization plots for each input signal. It is averaged over channels.")
CLI.add_argument("--frequency", nargs="?", type=freq_list, required=True, help="Center frequency of the Morlet wavelet in Hz")
CLI.add_argument("--n_cycles", nargs="?", type=float, default=6.0, help="Size of the mother wavelet (default: 6.0)")
CLI.add_argument("--sampling_frequency", nargs="?", type=float, default=1.0, help="Sampling rate of the input data in Hz (default: 1.0)")
CLI.add_argument("--zero_padding", nargs="?", type=bool, default=True, help="Specifies whether the data length is extended by padding zeros (default: True)")
CLI.add_argument("--start_time", nargs="?", type=float, default=None, help="Start time of the signal slice in seconds")
CLI.add_argument("--stop_time", nargs="?", type=float, default=None, help="Stop time of the signal slice in seconds")


def _plot_wavelet_transform(input_signal,
                            wavelet_transform_signal,
                            signal_index,
                            frequency):
    wavelet_spectrum = np.abs(np.atleast_3d(wavelet_transform_signal))
    avg_wavelet_spectrum = np.nanmean(wavelet_spectrum, axis=1)

    fig, ax = plt.subplots(figsize=(10, 6))

    im = ax.pcolor(input_signal.times,
                   frequency,
                   np.transpose(avg_wavelet_spectrum),
                   cmap='cividis', shading='auto')
    fig.colorbar(im)

    time_units = input_signal.times.units.dimensionality
    ax.set_ylabel("Frequency [Hz]")
    ax.set_xlabel(f"Time [{time_units}]")
    ax.set_title(f"Wavelet Spectrum - Signal {signal_index}")

    fig.savefig(f"wavelet_spectrum_{signal_index}.pdf",
                format="pdf")


def _save_wavelet_transform(transformed_signals, output_file,
                            frequency):
    arrays = {str(i): array for i, array in enumerate(transformed_signals)}
    np.savez(**arrays, file=output_file, frequency=frequency)


def wavelet_transform(
    input_file,
    input_format,
    output_file,
    block_index,
    block_name,
    segment_index,
    analog_signal_index,
    visualization_plots,
    frequency,
    n_cycles,
    sampling_frequency,
    zero_padding,
    start_time,
    stop_time,
):
    # Load Block from which AnalogSignals will be selected
    block = load_data(
        input_file,
        input_format=input_format,
        block_index=block_index,
        block_name=block_name,
    )

    # Select AnalogSignals according to CLI parameters
    signals = select_data(
        block, segment_index=segment_index, analog_signal_index=analog_signal_index
    )
    # To avoid using too much memory, slice the signals if start and stop times are provided
    if start_time is not None and stop_time is not None:
        signals = [signal.time_slice(start_time * pq.s, stop_time * pq.s) for signal in signals]

    # Iterate over all loaded AnalogSignals
    transformed_signals = [
        # Transform using Elephant wavelet_transform function
        elephant.signal_processing.wavelet_transform(
            signal=signal,
            frequency=frequency,
            n_cycles=n_cycles,
            sampling_frequency=sampling_frequency,
            zero_padding=zero_padding,
        )
        for signal in signals
    ]

    # Save the wavelet coefficients to a pickle file
    _save_wavelet_transform(transformed_signals, output_file, frequency)

    # Plot visualization of the transformed signals
    for index, (input_signal, wt_signal) in \
            enumerate(zip(signals, transformed_signals)):
        _plot_wavelet_transform(input_signal, wt_signal,
                                index, frequency)


if __name__ == "__main__":
    args, unknown = CLI.parse_known_args()
    wavelet_transform(**vars(args))
