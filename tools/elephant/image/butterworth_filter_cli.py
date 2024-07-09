#!/usr/bin/env python

import argparse
from pathlib import Path

import quantities as pq
from elephant.signal_processing import butter
from utils import load_data, save_data, select_data


def quantity(arg):
    if not arg:
        return None
    value, unit = arg.split(" ")
    return pq.Quantity(float(value), units=unit)


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
CLI.add_argument("--highpass_frequency", nargs='?', type=quantity,
                 default=None,
                 help="High-pass frequency cutoff")
CLI.add_argument("--lowpass_frequency", nargs='?', type=quantity,
                 default=None,
                 help="Low-pass frequency cutoff")
CLI.add_argument("--order", nargs='?', type=int, required=True,
                 help="Filter order")
CLI.add_argument("--filter_function", nargs='?', type=str, required=True,
                 help="Filter function")
CLI.add_argument("--block_idx", nargs='?', type=int, default=0,
                 help="Index of the block to process (default: 0)")
CLI.add_argument("--segment_idx", nargs='?', type=int, default=0,
                 help="Index of the segment to process (default: 0)")
CLI.add_argument("--analog_signal_idx", nargs='?', type=int, default=0,
                 help="Index of the analog signal to process (default: 0)")


def butterworth_filter(input_file, input_format, output_file, output_format,
                       highpass_frequency, lowpass_frequency, order,
                       filter_function, block_idx, segment_idx, analog_signal_idx):

    # Load AnalogSignal
    blocks = load_data(input_file, input_format)
    # TODO: advanced filtering function from CLI parameters
    signal = select_data(blocks, block_idx=block_idx, segment_idx=segment_idx, analog_signal_idx=analog_signal_idx)

    # Filter using Elephant butter function
    signal_filtered = butter(signal=signal,
                             highpass_frequency=highpass_frequency,
                             lowpass_frequency=lowpass_frequency,
                             order=order,
                             filter_function=filter_function)

    # Save filtered AnalogSignal
    save_data(signal_filtered, output_file, output_format)


if __name__ == "__main__":
    args, unknown = CLI.parse_known_args()
    butterworth_filter(**vars(args))
