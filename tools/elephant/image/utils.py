import quantities as pq
import neo
import datetime
from nixio.exceptions.exceptions import InvalidFile


def _parse_slice(slice_str):
    if isinstance(slice_str, int):
        return slice_str
    elif isinstance(slice_str, str):
        try:
            if slice_str == 'all':
                slice_str = ':'
            parts = slice_str.split(':')

            start = int(parts[0]) if parts[0] else None
            stop = int(parts[1])+1 if len(parts) > 1 and parts[1] else None
            step = int(parts[2]) if len(parts) > 2 and parts[2] else None

            return slice(start, stop, step)
        except ValueError:
            raise ValueError(f"Invalid slice string: {slice_str}")
    else:
        return slice_str


def select_data(block, segment_index=0,
                spike_train_index=None,
                analog_signal_index=None):
    try:
        if spike_train_index is not None:
            segments = block.segments[_parse_slice(segment_index)]
            if not isinstance(segments, list):
                segments = [segments]
            return [segment.spiketrains[_parse_slice(spike_train_index)] for segment in segments]
        elif analog_signal_index is not None:
            segments = block.segments[_parse_slice(segment_index)]
            if not isinstance(segments, list):
                analog_signals = segments.analogsignals[_parse_slice(analog_signal_index)]
                if not isinstance(analog_signals, list):
                    return [analog_signals]
                return analog_signals
            return [segment.analogsignals[_parse_slice(analog_signal_index)] for segment in segments]
        else:
            raise ValueError("spike_train or analog_signal index not provided")
    except IndexError as e:
        if 'spiketrains' in str(e):
            raise ValueError(f"Provided spike_train_index {spike_train_index} is out of range") from e
        elif 'analogsignals' in str(e):
            raise ValueError(f"Provided analog_signal_index {analog_signal_index} is out of range") from e
        else:
            raise ValueError(f"Provided segment_index {segment_index} is out of range") from e


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
        except IndexError:
            raise ValueError(f"block_index is not valid, provided: {block_index}")
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


def prepare_data(old_block, analog_signal=None, spike_train=None, action=None):
    if action not in {"new", "replace", "add"}:
        raise ValueError("Invalid action. Valid options are 'new', 'replace', 'add'.")
    if (analog_signal is None or len(analog_signal) == 0) and (spike_train is None or len(spike_train) == 0):
        raise ValueError("At least one data element must be provided.")

    if action == "new":
        new_block = neo.Block()
        new_segment = neo.Segment()
        new_block.segments.append(new_segment)
        if analog_signal:
            new_block.segments[0].analogsignals.extend(analog_signal)
        if spike_train:
            new_block.segments[0].spiketrains.extend(spike_train)
        return new_block
    elif action == "replace":
        old_block.segments = []
        if analog_signal:
            old_block.segments[0].analogsignals.extend(analog_signal)
        if spike_train:
            old_block.segments[0].spiketrains.extend(spike_train)
        return old_block
    elif action == "add":
        if analog_signal:
            old_block.segments.analogsignals.extend(analog_signal)
        if spike_train:
            old_block.segments.spiketrains.extend(spike_train)
        return old_block
    return None
