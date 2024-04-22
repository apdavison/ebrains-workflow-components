"""
Detect trigger times (i.e., state transition / local wavefronts onsets) 
by finding crossing of a set phase-value in the channel signals.
"""

import argparse
from pathlib import Path

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

def extract_features(input_file_current=PosixPath('B95_Ch0_IDRest_107.ibw'),
                     input_file_voltage=PosixPath('B95_Ch3_IDRest_107.ibw'),
                     output_file=PosixPath('test.json'),
                     features='Spikecount,mean_frequency,ISI_CV,AP1_amp,AP_width',
                     current_unit='pA',
                     voltage_unit='mV',
                     time_unit='s',
                     time_step=0.00025,
                     ljp=14.0,
                     protocol_name='IDRest')

if __name__ == '__main__':
    args, unknown = CLI.parse_known_args()
    print(args, unknown)
