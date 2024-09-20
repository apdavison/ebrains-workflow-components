from pathlib import Path
from typing import List, Optional, Union
import quantities as pq
import neo
from nixio.exceptions.exceptions import InvalidFile


def _parse_slice(slice_str: Union[str, int]) -> Union[slice, int]:
    """
    Parse a slice string or integer into a slice object.

    Parameters
    ----------
    slice_str : str or int
        A string representation of a slice (e.g., '1:5:2') or an integer.

    Returns
    -------
    slice or int
        A slice object if the input is a valid slice string, or the input
        integer if it's an integer.

    Raises
    ------
    ValueError
        If the input string is not a valid slice representation.

    Notes
    -----
    - If the input is 'all', it's treated as ':' (full slice).
    - For slice strings, the format is 'start:stop:step', where:
      * start and step are optional
      * stop is exclusive (consistent with Python's slice behavior)
    - Empty parts in the slice string are treated as None.

    Examples
    --------
    >>> _parse_slice('1:5')
    slice(1, 6, None)
    >>> _parse_slice('all')
    slice(None, None, None)
    >>> _parse_slice(3)
    3
    """
    if isinstance(slice_str, int):
        return slice_str
    elif isinstance(slice_str, str):
        try:
            if slice_str == "all":
                slice_str = ":"
            parts = slice_str.split(":")

            start = int(parts[0]) if parts[0] else None
            stop = int(parts[1]) + 1 if len(parts) > 1 and parts[1] else None
            step = int(parts[2]) if len(parts) > 2 and parts[2] else None

            return slice(start, stop, step)
        except ValueError:
            raise ValueError(f"Invalid slice string: {slice_str}")
    else:
        return slice_str


def select_data(
    block: neo.core.Block,
    segment_index: Union[int, str] = 0,
    spike_train_index: Optional[Union[int, str]] = None,
    analog_signal_index: Optional[Union[int, str]] = None,
) -> List[Union[neo.core.SpikeTrain, neo.core.AnalogSignal]]:
    """
    Select data from a Neo Block object based on specified indices.

    Parameters
    ----------
    block : neo.core.Block
        The Neo Block object containing the data.
    segment_index : int or str, optional
        Index or slice string for selecting segments. Default is 0.
    spike_train_index : int or str, optional
        Index or slice string for selecting spike trains.
    analog_signal_index : int or str, optional
        Index or slice string for selecting analog signals.

    Returns
    -------
    list
        A list of selected spike trains or analog signals.

    Raises
    ------
    ValueError
        If neither spike_train_index nor analog_signal_index is provided,
        or if the provided indices are out of range.

    Notes
    -----
    This function allows for flexible selection of data from a Neo Block.
    It can return either spike trains or analog signals based on the provided indices.
    The indices can be integers, slice objects, or slice strings (e.g., '1:5').
    """
    try:
        if spike_train_index is not None:
            segments = block.segments[_parse_slice(segment_index)]
            if not isinstance(segments, list):
                segments = [segments]
            return [
                segment.spiketrains[_parse_slice(spike_train_index)]
                for segment in segments
            ]
        elif analog_signal_index is not None:
            segments = block.segments[_parse_slice(segment_index)]
            if not isinstance(segments, list):
                analog_signals = segments.analogsignals[
                    _parse_slice(analog_signal_index)
                ]
                if not isinstance(analog_signals, list):
                    return [analog_signals]
                return analog_signals
            return [
                segment.analogsignals[_parse_slice(analog_signal_index)]
                for segment in segments
            ]
        else:
            raise ValueError("spike_train or analog_signal index not provided")
    except IndexError as e:
        if "spiketrains" in str(e):
            raise ValueError(
                f"Provided spike_train_index {spike_train_index} is out of range"
            ) from e
        elif "analogsignals" in str(e):
            raise ValueError(
                f"Provided analog_signal_index {analog_signal_index} is out of range"
            ) from e
        else:
            raise ValueError(
                f"Provided segment_index {segment_index} is out of range"
            ) from e


def load_data(
    input_file: Union[str, Path],
    input_format: Optional[str] = None,
    block_index: Optional[int] = None,
    block_name: Optional[str] = None,
) -> Union[neo.core.Block, List[neo.core.Block]]:
    """
    Load data from a file using Neo IO classes.

    Parameters
    ----------
    input_file : str or Path
        Path to the input file.
    input_format : str, optional
        Name of the Neo IO class to use for reading the file. If None,
        the function will attempt to determine the format automatically.
    block_index : int, optional
        Index of the block to load if multiple blocks are present.
    block_name : str, optional
        Name of the block to load if multiple blocks are present.

    Returns
    -------
    neo.core.Block or list of neo.core.Block
        The loaded data as a Neo Block object or a list of Block objects.

    Raises
    ------
    ValueError
        If the input format is not supported, if the file and format don't match,
        if both block_index and block_name are provided, or if the specified
        block cannot be found.

    Notes
    -----
    This function uses Neo IO classes to read various neurophysiology file formats.
    If input_format is not specified, it attempts to determine the format automatically.
    Either block_index or block_name can be used to load a specific block, but not both.
    If neither is provided, all blocks are returned.
    """
    if input_format is None:
        candidate_io = neo.list_candidate_ios(input_file)
        if candidate_io:
            io_class = candidate_io[0]
            flags = ["ro"] if io_class.__qualname__ == "NixIO" else []
            io = io_class(input_file, *flags)
        else:
            raise ValueError(
                f"Please specify a valid input format, provided: {input_format}"
            )
    else:
        flags = ["ro"] if input_format == "NixIO" else []
        try:
            io = getattr(neo.io, input_format)(input_file, *flags)
        except AttributeError:
            raise ValueError(
                f"Input_format is not supported by neo, provided: {input_format}"
            )
        except InvalidFile:
            raise ValueError(
                "input_file and input_format do not match, please provide valid file and correct input format"
            )
    if block_index and block_name:
        raise ValueError("Can not load by name and index simultaneously")
    elif block_index is not None:
        try:
            return io.read()[block_index]
        except TypeError:
            raise ValueError(
                "input_file and input_format do not match, please provide valid file and correct input format"
            )
        except IndexError:
            raise ValueError(f"block_index is not valid, provided: {block_index}")
    elif block_name is not None:
        try:
            block = next(
                (block for block in io.read() if block.name == block_name), None
            )
            if not block:
                raise ValueError("No block with block_name found")
            else:
                return block
        except TypeError:
            raise ValueError(
                "input_file and input_format do not match, please provide valid file and correct input format"
            )
    else:
        try:
            return io.read()
        except TypeError:
            raise ValueError(
                "input_file and input_format do not match, please provide valid file and correct input format"
            )


def save_data(
    data: Union[neo.AnalogSignal, neo.SpikeTrain, neo.Block, neo.Segment],
    output_file: Union[str, Path],
    output_format: Optional[str] = None,
    action: str = "new",
) -> None:
    """
    Save data to a file in a specified format.

    Parameters
    ----------
    data : neo.AnalogSignal, neo.SpikeTrain, neo.Block, or neo.Segment
        The data to be saved.
    output_file : str or pathlib.Path
        The path to the output file.
    output_format : str, optional
        The format to save the data in. Valid options are "NixIO" or "NWBIO".
        If None, the format will try to be inferred from the file extension.
    action : str, optional
        The action to take if the file already exists. Valid options are:
        - "new": Create a new file, raise an error if it already exists.
        - "replace": Replace the existing file.
        - "update": Update the existing file.
        Default is "new".

    Raises
    ------
    ValueError
        If the action is invalid, the output format is invalid, the file exists
        and action is "new", the file doesn't exist and action is "replace" or
        "update", or if the output format can't be inferred.

    Notes
    -----
    This function supports saving neo.AnalogSignal, neo.SpikeTrain, neo.Block,
    and neo.Segment objects. For AnalogSignal and SpikeTrain, a new Block and
    Segment are created to contain the data before saving.
    """
    valid_actions = {"new", "replace", "update"}
    valid_output_formats = {"NixIO", "NWBIO"}
    if action not in valid_actions:
        raise ValueError(f"Invalid action: {action}. Valid actions are {valid_actions}")
    if output_format and output_format not in valid_output_formats:
        raise ValueError(
            f"Invalid output format: {output_format}. Valid formats are {valid_output_formats}"
        )
    if output_format is None:
        ext = output_file.suffix.lower()
        if ext == ".nix":
            output_format = "NixIO"
        elif ext == ".nwb":
            output_format = "NWBIO"
        else:
            raise ValueError(
                "Could not infer output format from file extension and none was provided."
            )

    if action == "new" and output_file.exists():
        raise ValueError(f"File {output_file} already exists and action is 'new'.")
    elif action == "replace" and not output_file.exists():
        raise ValueError(f"File {output_file} does not exist and action is 'replace'.")
    elif action == "update" and not output_file.exists():
        raise ValueError(f"File {output_file} does not exist and action is 'update'.")

    if isinstance(data, (neo.AnalogSignal, neo.SpikeTrain)):
        saved_block = neo.Block()
        segment = neo.Segment()
        if isinstance(data, neo.AnalogSignal):
            segment.analogsignals.append(data)
        if isinstance(data, neo.SpikeTrain):
            segment.spiketrains.append(data)
        saved_block.add(segment)
    elif isinstance(data, neo.Block):
        saved_block = data
    elif isinstance(data, neo.Segment):
        saved_block = neo.Block()
        saved_block.add(data)

    if output_format == "NixIO":
        with neo.NixIO(
            output_file, mode="ow" if action in ["replace", "new"] else "rw"
        ) as io:
            io.write_block(saved_block)
    elif output_format == "NWBIO":
        with neo.NWBIO(
            output_file, mode="w" if action in ["replace", "new"] else "?"
        ) as io:
            io.write_block(saved_block)


def quantity_arg(arg: Optional[str]) -> Optional[pq.Quantity]:
    """
    Convert a string argument to a Quantity object.

    Parameters
    ----------
    arg : str or None
        A string containing a value and a unit, separated by a space.
        For example, "10 mV" or "5 ms".

    Returns
    -------
    pq.Quantity or None
        If arg is not None or an empty string, returns a Quantity object
        with the value and unit specified in the input string.
        If arg is None or an empty string, returns None.

    Raises
    ------
    ValueError
        If the input string cannot be parsed into a value and a unit.

    Examples
    --------
    >>> quantity_arg("10 mV")
    array(10.) * mV
    >>> quantity_arg("5 ms")
    array(5.) * ms
    >>> quantity_arg(None)
    None
    >>> quantity_arg("")
    None
    """
    if not arg:
        return None
    value, unit = arg.split(" ")
    return pq.Quantity(float(value), units=unit)


def prepare_data(
    old_block: Optional[neo.Block],
    analog_signal: Optional[List[neo.AnalogSignal]] = None,
    spike_train: Optional[List[neo.SpikeTrain]] = None,
    action: Optional[str] = None,
) -> neo.Block:
    """
    Prepare data for saving or updating a Neo Block.

    Parameters
    ----------
    old_block : neo.Block or None
        Existing Neo Block to be updated. Required for 'replace' and 'add' actions.
    analog_signal : list of neo.AnalogSignal or None, optional
        List of AnalogSignals to be added or used for replacement.
    spike_train : list of neo.SpikeTrain or None, optional
        List of SpikeTrains to be added or used for replacement.
    action : {'new', 'replace', 'add'}, optional
        Action to perform on the data:
        - 'new': Create a new Block with provided data.
        - 'replace': Replace all data in the existing Block.
        - 'add': Add new data to the existing Block.

    Returns
    -------
    neo.Block
        The resulting Neo Block after applying the specified action.

    Raises
    ------
    ValueError
        If an invalid action is provided, no data is provided, or if the action
        is incompatible with the provided data.

    Notes
    -----
    At least one of `analog_signal` or `spike_train` must be provided.
    """
    if action not in {"new", "replace", "add"}:
        raise ValueError("Invalid action. Valid options are 'new', 'replace', 'add'.")
    if (analog_signal is None or len(analog_signal) == 0) and (
        spike_train is None or len(spike_train) == 0
    ):
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
