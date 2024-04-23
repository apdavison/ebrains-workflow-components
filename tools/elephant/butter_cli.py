#!/usr/bin/env python

import argparse
from pathlib import Path
from datetime import datetime

import quantities as pq
import neo
import neo.io
from elephant.signal_processing import butter


def str_or_none(arg):
    if arg.lower() == "none":
        return None
    return arg


def quantity_or_float(arg):
    arg = str_or_none(arg)
    if not arg:
        return None
    try:
        value, unit = arg.split(" ")
        return pq.Quantity(float(value), units=unit)
    except TypeError:
        return float(arg)


CLI = argparse.ArgumentParser()
CLI.add_argument("--input_file", nargs='?', type=Path, required=True,
                 help="path with file with the input data")
CLI.add_argument("--input_format", nargs='?', type=str_or_none, required=True,
                 help="format of the input data")
CLI.add_argument("--output_file", nargs='?', type=Path, required=True,
                 help="path to the file where to write data")
CLI.add_argument("--output_format", nargs='?', type=str, required=True,
                 help="format of the output data")
CLI.add_argument("--highpass_frequency", nargs='?', type=quantity_or_float,
                 required=True,
                 help="High-pass frequency cutoff")
CLI.add_argument("--lowpass_frequency", nargs='?', type=quantity_or_float,
                 required=True,
                 help="Low-pass frequency cutoff")
CLI.add_argument("--order", nargs='?', type=int, required=True,
                 help="Filter order")
CLI.add_argument("--filter_function", nargs='?', type=str, required=True,
                 help="Filter function")


def load_data(input_file, input_format=None):
    if not input_format:
        candidate_io = neo.list_candidate_ios(input_file)
        if candidate_io:
            io_class = candidate_io[0]
            flags = ['ro'] if io_class.__qualname__ == 'NixIO' else []
            io = io_class(input_file, *flags)
        else:
            print(candidate_io)
            raise ValueError("Please specify the input format.")
    else:
        flags = ['ro'] if input_format == 'NixIO' else []
        io = getattr(neo.io, input_format)(input_file, *flags)

    return io.read_block()


def save_data(data, output_file, output_format):
    saved_block = neo.Block()
    segment = neo.Segment()
    segment.analogsignals.append(data)
    saved_block.add(segment)

    if output_format == "NixIO":
        neo.NixIO(output_file, 'ow').write_block(saved_block)
    elif output_format == "NWBIO":
        saved_block.annotate(session_start_time=datetime.now())
        neo.NWBIO(output_file, 'w').write_block(saved_block)


def butterworth_filter(input_file, input_format, output_file, output_format,
                       highpass_frequency, lowpass_frequency, order,
                       filter_function):

    # Load AnalogSignal
    block = load_data(input_file, input_format)
    #TODO: advanced filtering function from CLI parameters
    signal = block.segments[0].analogsignals[0]

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
