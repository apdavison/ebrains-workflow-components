import quantities as pq
import neo
import datetime


def select_data(data, block_idx=0, segment_idx=0, spike_train_idx=None, analog_signal_idx=None):
    if spike_train_idx is not None:
        return data[block_idx].segments[segment_idx].spiketrains[spike_train_idx]
    elif analog_signal_idx is not None:
        return data[block_idx].segments[segment_idx].analogsignals[analog_signal_idx]
    else:
        raise ValueError("spike_train or analog_signal index not provided")


def load_data(input_file, input_format=None):
    if not input_format:
        candidate_io = neo.list_candidate_ios(input_file)
        if candidate_io:
            io_class = candidate_io[0]
            flags = ["ro"] if io_class.__qualname__ == "NixIO" else []
            io = io_class(input_file, *flags)
        else:
            raise ValueError(f"Please specify the input format, provided: {input_format}")
    else:
        flags = ["ro"] if input_format == "NixIO" else []
        io = getattr(neo.io, input_format)(input_file, *flags)

    return io.read()


def save_data(data, output_file, output_format, action):
    saved_block = neo.Block()
    segment = neo.Segment()
    segment.analogsignals.append(data)
    saved_block.add(segment)

    if output_format == "NixIO":
        neo.NixIO(output_file, "ow").write_block(saved_block)
    elif output_format == "NWBIO":
        saved_block.annotate(session_start_time=datetime.now())
        neo.NWBIO(output_file, "w").write_block(saved_block)


def quantity_arg(arg):
    if not arg:
        return None
    value, unit = arg.split(" ")
    return pq.Quantity(float(value), units=unit)


def prepare_data(arg1):
    raise NotImplementedError("Not yet implemented")