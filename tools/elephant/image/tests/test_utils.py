import unittest
import tempfile
from pathlib import Path
from datetime import datetime
import uuid
from collections import defaultdict
from functools import partial
import logging

import numpy as np
import quantities as pq
import neo
from elephant.spike_train_generation import StationaryPoissonProcess

# TODO: import functions from utils
import sys
import os
# Get the current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to sys.path
sys.path.append(parent_dir)

from utils import load_data, select_data

np.random.seed(1234)
logging.basicConfig(level=logging.DEBUG)


# Data generation functions

def get_spike_trains(firing_rate, n_spiketrains, t_stop, source):
    sts = StationaryPoissonProcess(
        firing_rate, t_stop=t_stop).generate_n_spiketrains(n_spiketrains)
    for idx, st in enumerate(sts, start=1):
        st.name = f"Unit {idx}"
        st.annotate(source=source)
    return sts


def get_analog_signal(frequency, n_channels, t_stop, name,
                      amplitude=3*pq.V, sampling_rate=1000*pq.Hz):
    end_time = t_stop.rescale(pq.s).magnitude
    period = 1/sampling_rate.rescale(pq.Hz).magnitude
    freq = frequency.rescale(pq.Hz).magnitude

    samples = np.arange(0, end_time, period)
    base_signal = np.sin(2*np.pi*freq*samples) * amplitude.magnitude

    signal = np.tile(base_signal, (n_channels, 1))
    noise = np.random.normal(0, 1, size=signal.shape)
    signal += noise

    array_annotations = {
        'channel_names': np.array([f"chan{ch+1}" for ch in range(n_channels)])
    }
    return neo.AnalogSignal(signal.T, units=amplitude.units,
                            sampling_rate=sampling_rate, name=name,
                            array_annotations=array_annotations)


def add_ids_and_metadata(block, start_time):
    block.annotate(session_start_time=start_time)
    block.create_relationship()

    # Storing UUIDs as description since NWBIO does not save Neo annotations
    block.description = str(uuid.uuid4())
    for seg in block.segments:
        seg.description = str(uuid.uuid4())
        for signal in seg.analogsignals:
            signal.description = str(uuid.uuid4())
        for st in seg.spiketrains:
            st.description = str(uuid.uuid4())


def generate_block_1(start_time):
    # Block 1: 1 Segment with 2 AnSigs + 1 SpikeTrain list
    block = neo.Block(name="Data 1")

    signals = [get_analog_signal(freq, n_channels, t_stop=2*pq.s, name=name)
               for freq, n_channels, name in
               ((20 * pq.Hz, 32, "AS 1.1"),
                (30 * pq.Hz,  8, "AS 1.2"))]

    spiketrains = get_spike_trains(15 * pq.Hz, 30, t_stop=2*pq.s,
                                   source="Region 1")

    segment = neo.Segment(name="Segment 1")
    segment.analogsignals.extend(signals)
    segment.spiketrains.extend(spiketrains)

    block.segments.append(segment)
    add_ids_and_metadata(block, start_time)

    return block


def generate_block_2(start_time=None):
    # Block 2: 1 Segment with 3 AnSigs + 2 SpikeTrain lists and
    # 1 Segment with 2 AnSigs + 1 SpikeTrain list
    block = neo.Block(name="Data 2")

    signals = [get_analog_signal(freq, n_channels, t_stop, name=name)
               for freq, n_channels, name, t_stop in
               ((10 * pq.Hz, 32, "AS 1.1", 3 * pq.s),
                (20 * pq.Hz,  8, "AS 1.2", 3 * pq.s),
                (30 * pq.Hz, 16, "AS 1.3", 3 * pq.s),
                (15 * pq.Hz,  8, "AS 2.1", 2 * pq.s),
                (25 * pq.Hz, 16, "AS 2.2", 2 * pq.s))]

    spiketrains = [get_spike_trains(firing_rate, n_spiketrains, t_stop=t_stop,
                                    source=source)
                   for firing_rate, n_spiketrains, source, t_stop in
                   ((30 * pq.Hz, 15, "ST 1.1", 3 * pq.s),
                    (15 * pq.Hz, 30, "ST 1.2", 3 * pq.s),
                    (20 * pq.Hz, 10,   "ST 2", 2 * pq.s))]

    seg_2_1 = neo.Segment(name="Segment 2.1")
    seg_2_1.analogsignals.extend(signals[:3])
    for sts in spiketrains[:2]:
        seg_2_1.spiketrains.extend(sts)

    seg_2_2 = neo.Segment(name="Segment 2.2")
    seg_2_2.analogsignals.extend(signals[3:])
    seg_2_2.spiketrains.extend(spiketrains[2])

    block.segments.append(seg_2_1)
    block.segments.append(seg_2_2)
    add_ids_and_metadata(block, start_time)

    return block


# File IO functions

def write_dataset(filename, blocks, io_type, io_args):
    io = io_type(filename, *io_args)
    io.write_all_blocks(blocks)

def read_dataset(filename, io_type, io_args):
    io = io_type(filename, *io_args)
    blocks = io.read_all_blocks(lazy=False)
    return blocks

WRITE_FUNCTIONS = {
    'nwb': partial(write_dataset, io_type=neo.NWBIO, io_args=('w',)),
    'nix': partial(write_dataset, io_type=neo.NixIO, io_args=('ow',)),
}

READ_FUNCTIONS = {
    'nwb': partial(read_dataset, io_type=neo.NWBIO, io_args=('r',)),
    'nix': partial(read_dataset, io_type=neo.NixIO, io_args=('ro',)),
}

# Unit tests


class ElephantUtilsTestCase(unittest.TestCase):

    @staticmethod
    def _check_block_objects_equal(first, second, nwb=False):
        # Compare names and descriptions of Block, Segment, AnalogSignals,
        # SpikeTrains, according to the hierarchy in the Block.
        # In data from NWB files, descriptions are ignored for Segment,
        # AnalogSignal and SpikeTrain, as the NWBIO does not store them.
        assert first.name == second.name
        assert first.description == second.description

        for seg_first, seg_second in zip(first.segments, second.segments):
            assert seg_first.name == seg_second.name
            if not nwb:
                assert seg_first.description == seg_second.description

            for signal_first, signal_second in zip(seg_first.analogsignals,
                                                   seg_second.analogsignals):
                assert signal_first.name == signal_second.name
                if not nwb:
                    assert signal_first.description == signal_second.description

            for st_first, st_second in zip(seg_first.spiketrains,
                                           seg_second.spiketrains):
                assert st_first.name == st_second.name
                if not nwb:
                    assert st_first.description == st_second.description

    @staticmethod
    def _check_block_1_data(block, nwb=False):
        assert len(block.segments) == 1
        assert block.name == "Data 1"

        seg_1 = block.segments[0]
        assert seg_1.name == "Segment 1"
        assert seg_1.t_stop == 2 * pq.s

        assert len(seg_1.analogsignals) == 2
        assert seg_1.analogsignals[0].shape == (2000, 32)
        assert (seg_1.analogsignals[0].name ==
                "AS 1.1" if not nwb else "Segment 1 AS 1.1 0")
        assert seg_1.analogsignals[1].shape == (2000, 8)
        assert (seg_1.analogsignals[1].name ==
                "AS 1.2" if not nwb else "Segment 1 AS 1.2 1")

        assert len(seg_1.spiketrains) == 30
        for idx, st in enumerate(seg_1.spiketrains, start=1):
            assert st.annotations["source"] == "Region 1"
            assert st.name == f"Unit {idx}"

    @staticmethod
    def _check_block_2_data(block, nwb=False):
        assert len(block.segments) == 2
        assert block.name == "Data 2"

        seg_2_1, seg_2_2 = block.segments
        assert seg_2_1.name == "Segment 2.1"
        assert seg_2_2.name == "Segment 2.2"
        assert seg_2_1.t_stop == 3 * pq.s
        assert seg_2_2.t_stop == 2 * pq.s

        assert len(seg_2_1.analogsignals) == 3
        assert seg_2_1.analogsignals[0].shape == (3000, 32)
        assert (seg_2_1.analogsignals[0].name ==
                "AS 1.1" if not nwb else "Segment 2.1 AS 1.1 0")
        assert seg_2_1.analogsignals[1].shape == (3000, 8)
        assert (seg_2_1.analogsignals[1].name ==
                "AS 1.2" if not nwb else "Segment 2.1 AS 1.2 1")
        assert seg_2_1.analogsignals[2].shape == (3000, 16)
        assert (seg_2_1.analogsignals[2].name ==
                "AS 1.3" if not nwb else "Segment 2.1 AS 1.3 2")

        assert len(seg_2_1.spiketrains) == 45
        for idx, st in enumerate(seg_2_1.spiketrains, start=1):
            source = "ST 1.2" if idx > 15 else "ST 1.1"
            unit_id = idx - 15 if idx > 15 else idx
            assert st.annotations["source"] == source
            assert st.name == f"Unit {unit_id}"

        assert len(seg_2_2.analogsignals) == 2
        assert seg_2_2.analogsignals[0].shape == (2000, 8)
        assert (seg_2_2.analogsignals[0].name ==
                "AS 2.1" if not nwb else "Segment 2.2 AS 2.1 0")
        assert seg_2_2.analogsignals[1].shape == (2000, 16)
        assert (seg_2_2.analogsignals[1].name ==
                "AS 2.2" if not nwb else "Segment 2.2 AS 2.2 1")

        assert len(seg_2_2.spiketrains) == 10
        for idx, st in enumerate(seg_2_2.spiketrains, start=1):
            assert st.annotations["source"] == "ST 2"
            assert st.name == f"Unit {idx}"

    @classmethod
    def setUpClass(cls):
        # Write temporary files:
        # - A dictionary stores the paths to the file names.
        # - Different copies of the Blocks are generated and stored, as NWB
        #   files require change in the name of AnalogSignals and the IO
        #   modifies the input objects.

        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.data_files = {}
        cls.blocks = defaultdict(list)

        for file_format in ('nix', 'nwb'):
            for num_blocks in range(1, 3):
                file_stem = f"{file_format}_{num_blocks}"
                dest_file = Path(cls.tmp_dir.name) / f"{file_stem}.{file_format}"
                cls.data_files[file_stem] = dest_file

                start_time = datetime.now()
                cls.blocks[file_stem].append(generate_block_1(start_time))
                if num_blocks > 1:
                    cls.blocks[file_stem].append(generate_block_2(start_time))

                WRITE_FUNCTIONS[file_format](  dest_file, cls.blocks[file_stem])

    def test_files(self):
        # Check if data in NIX/NWB files agree with generated objects
        for file in ('nwb_1', 'nwb_2', 'nix_1', 'nix_2'):
            with self.subTest(f"File {file}", file=file):
                if file == "nwb_2":
                    self.skipTest("TODO: NWB files with 2 blocks are read with the description of the first block")
                file_format = file.split("_")[0]
                file_blocks = READ_FUNCTIONS[file_format](self.data_files[file])
                generated_blocks = self.blocks[file]
                assert len(file_blocks) == len(generated_blocks)
                for file_block, generated_block in zip(file_blocks,
                                                       generated_blocks):
                    self._check_block_objects_equal(file_block,
                                                    generated_block,
                                                    nwb=(file_format == 'nwb'))

    def test_data(self):
        # Check if generated data has the desired structure
        for file in ('nwb_1', 'nwb_2', 'nix_1', 'nix_2'):
            with self.subTest(f"Data for {file}", file=file):
                file_format = file.split("_")[0]
                blocks = self.blocks[file]
                self._check_block_1_data(blocks[0],
                                         nwb=(file_format == 'nwb'))
                if len(blocks) > 1:
                    self._check_block_2_data(blocks[1],
                                             nwb=(file_format == 'nwb'))

    def test_load_data_load_nix(self):
        blocks = load_data(self.data_files['nix_1'], input_format='NixIO')
        assert blocks[0].name == "Data 1"

    def test_select_data_analog_signal(self):
        analog_signal = select_data(self.blocks['nix_1'], block_idx=0, segment_idx=0, analog_signal_idx=0)
        assert isinstance(analog_signal, neo.AnalogSignal)

    def test_select_data_spike_train(self):
        spike_train = select_data(self.blocks['nix_1'], block_idx=0, segment_idx=0, spike_train_idx=0)
        assert isinstance(spike_train, neo.SpikeTrain)


    @classmethod
    def tearDownClass(cls):
        # Clean temporary folder
        cls.tmp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
