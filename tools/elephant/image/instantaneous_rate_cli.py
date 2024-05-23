#!/usr/bin/env python

import argparse
from pathlib import Path
from datetime import datetime

import quantities as pq
import neo
import neo.io
from elephant import instantaneous_rate as elephant_instantaneous_rate


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
CLI.add_argument("--sampling_period", nargs='?', type=quantity, required=True,
                 help="Time stamp resolution of the spike times.")
CLI.add_argument("--kernel", nargs='?', type=str,
                 default="auto",
                 help="The string ‘auto’ or callable object of class kernels.Kernel.")
CLI.add_argument("--cutoff", nargs='?', type=float,
                 default=5.0,
                 help="This factor determines the cutoff of the probability distribution of the kernel")
CLI.add_argument("--t_start", nargs='?', type=quantity, default=None,
                 help="Start time of the interval used to compute the firing rate.")
CLI.add_argument("--t_stop", nargs='?', type=quantity, default=None,
                 help="End time of the interval used to compute the firing rate. If None, t_stop is assumed equal to t_stop attribute of spiketrain.")
CLI.add_argument("--trim", nargs='?', type=bool, default=False,
                 help="Accounts for the asymmetry of a kernel. If False, the output is reduced back to the original size. If True, only the region of complete overlap is returned.")
CLI.add_argument("--center_kernel", nargs='?', type=bool, default=True,
                 help="If True, the kernel will be centered on the spike. If False, no adjustment is performed.")
CLI.add_argument("--border_correction", nargs='?', type=bool, default=False,
                 help="Apply a border correction to prevent underestimating firing rates at the borders.")
CLI.add_argument("--pool_trials", nargs='?', type=bool, default=False,
                 help="If true, calculate firing rates averaged over trials if spiketrains is of type elephant.trials.Trials.")
CLI.add_argument("--pool_spike_trains", nargs='?', type=bool, default=False,
                 help="If true, calculate firing rates averaged over spike trains.")


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


def instantaneous_rate(input_file, input_format, output_file, output_format,
                       sampling_period, kernel, cutoff,
                       t_start, t_stop, trim, center_kernel, border_correction,
                       pool_trials, pool_spike_trains):

    # Load Spike Train
    block = load_data(input_file, input_format)

    spiketrain = block.segments[0].spiketrains[0]

    # Estimate rate using Elephant function
    estimated_rate = elephant_instantaneous_rate(
        spiketrains=spiketrain, sampling_period=sampling_period,
        kernel=kernel, cutoff=cutoff, t_start=t_start, t_stop=t_stop,
        trim=trim, center_kernel=center_kernel,
        border_correction=border_correction, pool_trials=pool_trials,
        pool_spike_trains=pool_spike_trains)

    # Save filtered AnalogSignal to file
    save_data(estimated_rate, output_file, output_format)


if __name__ == "__main__":
    args, unknown = CLI.parse_known_args()
    instantaneous_rate(**vars(args))
