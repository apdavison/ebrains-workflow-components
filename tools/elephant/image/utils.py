import quantities as pq
import neo
import datetime
from nixio.exceptions.exceptions import InvalidFile

def select_data(data, block_idx=0, segment_idx=0, spike_train_idx=None, analog_signal_idx=None):
    if spike_train_idx is not None:
        return data[block_idx].segments[segment_idx].spiketrains[spike_train_idx]
    elif analog_signal_idx is not None:
        return data[block_idx].segments[segment_idx].analogsignals[analog_signal_idx]
    else:
        raise ValueError("spike_train or analog_signal index not provided")


def load_data(input_file, input_format=None, block_index=None, block_name=None):
    if input_format is None:
        candidate_io = neo.list_candidate_ios(input_file)
        if candidate_io:
            io_class = candidate_io[0]
            flags = ["ro"] if io_class.__qualname__ == "NixIO" else []
            io = io_class(input_file, *flags)
        else:
            raise ValueError(f"Please specify a valid input format, provided: {input_format}")
    else:
        flags = ["ro"] if input_format == "NixIO" else []
        try:
            io = getattr(neo.io, input_format)(input_file, *flags)
        except AttributeError:
            raise ValueError(f"Input_format is not supported by neo, provided: {input_format}")
        except InvalidFile:
            raise ValueError("input_file and input_format do not match, please provide valid file and correct input format")
    if block_index and block_name:
        raise ValueError("Can not load by name and index simultaneously")
    elif block_index is not None:
        try:
            return io.read()[block_index]
        except TypeError:
            raise ValueError("input_file and input_format do not match, please provide valid file and correct input format")
    elif block_name is not None:
        try:
            block = next((block for block in io.read() if block.name == block_name), None)
            if not block:
                raise ValueError("No block with block_name found")
            else: 
                return block
        except TypeError:
            raise ValueError("input_file and input_format do not match, please provide valid file and correct input format")


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