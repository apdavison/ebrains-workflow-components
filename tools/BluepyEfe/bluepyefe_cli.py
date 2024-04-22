"""
Detect trigger times (i.e., state transition / local wavefronts onsets) 
by finding crossing of a set phase-value in the channel signals.
"""

import argparse
from pathlib import Path

CLI = argparse.ArgumentParser()
CLI.add_argument("--input-file-current", nargs=1, type=Path, required=True,
                 help="path with current measurement of the recording")
CLI.add_argument("--input-file-voltage", nargs=1, type=Path, required=True,
                 help="path with voltage measurement of the recording")
CLI.add_argument("--output-file", nargs=1, type=Path, required=True,
                 help="save file with extracted features to path")
CLI.add_argument("--features", nargs=1, type=str, required=True,
                 default=None, help="features to extract, separated by comma")
CLI.add_argument("--current-unit", nargs='?', type=str,
                 default='pA',
                 help='units of the current measurement')
CLI.add_argument("--voltage-unit", nargs='?', type=str,
                 default='mV',
                 help='units of the voltage measurement')
CLI.add_argument("--time-unit", nargs='?', type=str,
                 default='s',
                 help='units of the time measurement')
CLI.add_argument("--time-step", nargs='?', type=float,
                 default=0.00025,
                 help='sampling period')
CLI.add_argument("--ljp", nargs='?', type=float,
                 default=14.0,
                 help='ljp')
CLI.add_argument("--protocol-name", nargs=1, type=str, required=True,
                 help='name of the experimental protocol')

if __name__ == '__main__':
    args, unknown = CLI.parse_known_args()
    print(args, unknown)
