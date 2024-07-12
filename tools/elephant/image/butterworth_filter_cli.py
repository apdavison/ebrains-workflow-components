#!/usr/bin/env python

import argparse
from pathlib import Path
from collections import defaultdict

import quantities as pq
from elephant.signal_processing import butter
from utils import (load_data, save_data, prepare_data, select_data,
                   quantity_arg)


CLI = argparse.ArgumentParser()
CLI.add_argument("--input_file", nargs='?', type=Path, required=True,
                 help="path with file with the input data")
CLI.add_argument("--input_format", nargs='?', type=str,
                 default=None,
                 help="format of the input data")
CLI.add_argument("--output_file", nargs='?', type=Path, required=True,
                 help="path to the file where to write data")
CLI.add_argument("--output_format", nargs='?', type=str, required=True,
                 help="format of the output data")
CLI.add_argument("--highpass_frequency", nargs='?', type=quantity_arg,
                 default=None,
                 help="High-pass frequency cutoff")
CLI.add_argument("--lowpass_frequency", nargs='?', type=quantity_arg,
                 default=None,
                 help="Low-pass frequency cutoff")
CLI.add_argument("--order", nargs='?', type=int, required=True,
                 help="Filter order")
CLI.add_argument("--filter_function", nargs='?', type=str, required=True,
                 help="Filter function")
CLI.add_argument("--block_index", nargs='?', type=int, default=0,
                 help="Index of the block to process (default: 0)")
CLI.add_argument("--segment_index", nargs='?', type=int, default=0,
                 help="Index of the segment to process (default: 0)")
CLI.add_argument("--analog_signal_index", nargs='?', type=int, default=0,
                 help="Index of the analog signal to process (default: 0)")
CLI.add_argument("--action", nargs='?', type=str, required=True,
                 help="Action on how to store the results with respect to"
                      "the original data")


def butterworth_filter(input_file, input_format, output_file, output_format,
                       highpass_frequency, lowpass_frequency, order,
                       filter_function, block_index, block_name, segment_index,
                       analog_signal_index, action):

    # Load Block from which AnalogSignals will be selected
    block = load_data(input_file, input_format=input_format,
                      block_index=block_index,
                      block_name=block_name)

    # Select AnalogSignals according to CLI parameters
    signals = select_data(block, segment_index=segment_index,
                          analog_signal_index=analog_signal_index)

    # Iterate over all loaded AnalogSignals
    filtered_signals = [

        # Filter using Elephant butter function
        butter(signal=signal,
               highpass_frequency=highpass_frequency,
               lowpass_frequency=lowpass_frequency,
               order=order,
               filter_function=filter_function)
        for signal in signals
    ]

    # Prepare a Block to save the filtered AnalogSignals
    new_block = prepare_data(block, analog_signal=filtered_signals,
                             action=action)

    # Save Block
    save_data(new_block, output_file, output_format=output_format,
              action=action)


if __name__ == "__main__":
    args, unknown = CLI.parse_known_args()
    butterworth_filter(**vars(args))
