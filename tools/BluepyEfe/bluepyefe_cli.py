"""
Detect trigger times (i.e., state transition / local wavefronts onsets) 
by finding crossing of a set phase-value in the channel signals.
"""

import argparse
from pathlib import Path

from bluepyefe.cell import Cell


# CLI parsing

CLI = argparse.ArgumentParser()
CLI.add_argument("--input_file_current", nargs='?', type=Path, required=True,
                 help="path with current measurement of the recording")
CLI.add_argument("--input_file_voltage", nargs='?', type=Path, required=True,
                 help="path with voltage measurement of the recording")
CLI.add_argument("--output_file", nargs='?', type=Path, required=True,
                 help="save file with extracted features to path")
CLI.add_argument("--features", nargs='?', type=str, required=True,
                 default=None, help="features to extract, separated by comma")
CLI.add_argument("--current_unit", nargs='?', type=str,
                 default='pA',
                 help='units of the current measurement')
CLI.add_argument("--voltage_unit", nargs='?', type=str,
                 default='mV',
                 help='units of the voltage measurement')
CLI.add_argument("--time_unit", nargs='?', type=str,
                 default='s',
                 help='units of the time measurement')
CLI.add_argument("--time_step", nargs='?', type=float,
                 default=0.00025,
                 help='sampling period')
CLI.add_argument("--ljp", nargs='?', type=float,
                 default=14.0,
                 help='ljp')
CLI.add_argument("--protocol_name", nargs='?', type=str, required=True,
                 help='name of the experimental protocol')


def extract_features(input_file_current, input_file_voltage,
                     output_file, features, current_unit,
                     voltage_unit, time_unit, time_step,
                     ljp, protocol_name):

    # Create Cell component to load the recordings
    cell = Cell(name="Default Cell")

    # Metadata dictionary to load the recordings
    files_metadata = {
        "i_file": input_file_current,
        "v_file": input_file_voltage,
        "i_unit": current_unit,
        "v_unit": voltage_unit,
        "t_unit": time_unit,
        "dt": time_step,
        "ljp": ljp,
    }

    cell.read_recordings(protocol_data=[files_metadata],
                         protocol_name=protocol_name)

    cell.extract_efeatures(protocol_name=protocol_name,
                           efeatures=features)

    print(cell.recordings[0].efeatures)


if __name__ == '__main__':
    args, unknown = CLI.parse_known_args()
    extract_features(**vars(args))
