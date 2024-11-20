#!/usr/bin/env python

import argparse
from pathlib import Path

import elephant
from utils import load_data, save_data, prepare_data, select_data, quantity_arg

CLI = argparse.ArgumentParser()
CLI.add_argument("--input_file", nargs="?", type=Path, required=True, help="path with file with the input data")
CLI.add_argument("--input_format", nargs="?", type=str, default=None, help="format of the input data")
CLI.add_argument("--output_file", nargs="?", type=Path, required=True, help="path to the file where to write data")
CLI.add_argument("--output_format", nargs="?", type=str, required=True, help="format of the output data")
CLI.add_argument("--block_index", nargs="?", type=int, default=0, help="Index of the block to process (default: 0)")
CLI.add_argument("--block_name", nargs="?", type=str, default=None, help="Name of the block to process (optional)")
CLI.add_argument("--segment_index", nargs="?", type=int, default=0, help="Index of the segment to process (default: 0)")
CLI.add_argument("--analog_signal_index", nargs="?", type=int, default=0, help="Index of the analog signal to process (default: 0)")
CLI.add_argument("--action", nargs="?", type=str, required=True, help="Action on how to store the results with respect to the original data")
CLI.add_argument("--frequency", nargs="?", type=float, required=True, help="Center frequency of the Morlet wavelet in Hz")
CLI.add_argument("--n_cycles", nargs="?", type=float, default=6.0, help="Size of the mother wavelet (default: 6.0)")
CLI.add_argument("--sampling_frequency", nargs="?", type=float, default=1.0, help="Sampling rate of the input data in Hz (default: 1.0)")
CLI.add_argument("--zero_padding", nargs="?", type=bool, default=True, help="Specifies whether the data length is extended by padding zeros (default: True)")


def wavelet_transform(
    input_file,
    input_format,
    output_file,
    output_format,
    block_index,
    block_name,
    segment_index,
    analog_signal_index,
    action,
    frequency,
    n_cycles,
    sampling_frequency,
    zero_padding,
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

    # Save data to pickle
    # save_transform()

    def save_transform():
        # TODO: implement
        pass

    def plot_transform():
        # TODO: implement
        pass
        
        
if __name__ == "__main__":
    args, unknown = CLI.parse_known_args()
    wavelet_transform(**vars(args))
