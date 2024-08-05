import unittest
import sys
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import uuid
from collections import defaultdict
from functools import partial

import numpy as np
import quantities as pq
import neo
from elephant.spike_train_generation import StationaryPoissonProcess

# Get the current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to sys.path
sys.path.append(parent_dir)

from utils import load_data, select_data, prepare_data, save_data


# Data generation functions

np.random.seed(1234)    # Set seed for reproducibility


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
    def _check_block_objects_equal(first, second, *, nwb):
        # Compare names and descriptions of Block, Segment, AnalogSignals,
        # SpikeTrains, according to the hierarchy in the Block.
        # In data from NWB files, descriptions are ignored for Segment,
        # AnalogSignal and SpikeTrain, as the NWBIO does not store them.
        assert isinstance(first, neo.Block)
        assert isinstance(second, neo.Block)
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
    def _check_block_1_data(block, *, nwb):
        # Checks if all data elements in the Block "Data 1" are correct
        # This is the block with index == 0 in all files
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
            # TODO: remove after NWBio supports annotations
            if not nwb:
                assert st.annotations["source"] == "Region 1"
            assert st.name == f"Unit {idx}"

    @staticmethod
    def _check_block_2_data(block, *, nwb):
        # Checks if all data elements in the Block "Data 2" are correct
        # This is the block with index == 1 in the files with 2 blocks
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
            if not nwb: 
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
            if not nwb:
                assert st.annotations["source"] == "ST 2"
            assert st.name == f"Unit {idx}"

    @classmethod
    def setUpClass(cls):
        # Write temporary files:
        # - A dictionary stores the paths to the file names.
        # - Different copies of the Blocks are generated and stored, as NWB
        #   files require change in the name of AnalogSignals and the IO
        #   modifies the input objects.
        # - Copies with different extensions are also made

        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.dataset_files = {}
        cls.blocks = defaultdict(list)

        for file_format in ('nix', 'nwb'):
            for num_blocks in range(1, 3):
                file_stem = f"{file_format}_{num_blocks}"
                dest_file = Path(cls.tmp_dir.name) / f"{file_stem}.{file_format}"
                cls.dataset_files[file_stem] = dest_file

                start_time = datetime.now()
                cls.blocks[file_stem].append(generate_block_1(start_time))
                if num_blocks > 1:
                    cls.blocks[file_stem].append(generate_block_2(start_time))

                WRITE_FUNCTIONS[file_format](dest_file, cls.blocks[file_stem])

        # Copies of NIX and NWB datasets are made with the extension ".data"
        source_nwb = cls.dataset_files['nwb_1']
        cls.new_nwb_file = source_nwb.with_suffix(".data")
        shutil.copy(src=str(source_nwb), dst=str(cls.new_nwb_file))

        source_nix = cls.dataset_files['nix_1']
        cls.new_nix_file = source_nix.with_suffix(".data")
        shutil.copy(src=str(source_nix), dst=str(cls.new_nix_file))

    # Tests to validate the generated data and files

    def test_files(self):
        # Check if data in NIX/NWB files agree with generated objects
        for dataset in ('nwb_1', 'nwb_2', 'nix_1', 'nix_2'):
            with self.subTest(f"File {dataset}", dataset=dataset):
                # FIXME: reading of block descriptions in NWB IO
                if dataset == "nwb_2":
                    self.skipTest("FIXME: NWB files with 2 blocks are read with the description of the first block")
                file_format = dataset.split("_")[0]
                file_blocks = READ_FUNCTIONS[file_format](self.dataset_files[dataset])
                generated_blocks = self.blocks[dataset]
                assert len(file_blocks) == len(generated_blocks)
                for file_block, generated_block in zip(file_blocks,
                                                       generated_blocks):
                    self._check_block_objects_equal(file_block,
                                                    generated_block,
                                                    nwb=(file_format == 'nwb'))

    def test_data(self):
        # Check if generated data has the desired structure and content
        for dataset in ('nwb_1', 'nwb_2', 'nix_1', 'nix_2'):
            with self.subTest(f"Data for {dataset}", dataset=dataset):
                nwb = 'nwb' in dataset
                blocks = self.blocks[dataset]
                self._check_block_1_data(blocks[0], nwb=nwb)
                if len(blocks) > 1:
                    self._check_block_2_data(blocks[1], nwb=nwb)

    # Load data tests
    def test_load_data_invalid_options(self):
        # Checks if the load function raises ValueError if invalid options are
        # specified.

        # Invalid input format
        with self.assertRaises(ValueError):
            load_data(self.new_nix_file, input_format="invalid")

        # Requesting by name and index simultaneously
        with self.assertRaises(ValueError):
            load_data(self.new_nix_file, block_index=0, block_name="Data 1")

    def test_load_data_detect_input_format(self):
        # Checks if the load function can infer NWB or NIX format from the
        # file name, and load the first block using the correct IO
        for dataset in ('nix_1', 'nwb_1'):
            with self.subTest(f"Detect format: {dataset}",
                              file_type=dataset):
                nwb = 'nwb' in dataset
                block = load_data(self.dataset_files[dataset], block_index=0)
                self._check_block_objects_equal(
                    first=block,
                    second=self.blocks[dataset][0],
                    nwb=nwb
                )
                self._check_block_1_data(block, nwb=nwb)

    def test_load_data_failed_detect_input_format(self):
        # Checks if the load function raises ValueError if the input format
        # was not specified and the format could not be inferred when trying
        # to load either a NIX or NWB file
        assert str(self.new_nwb_file.name) == "nwb_1.data"
        with self.assertRaises(ValueError):
            block = load_data(self.new_nwb_file, block_index=0,
                              input_format=None)

        assert str(self.new_nix_file.name) == "nix_1.data"
        with self.assertRaises(ValueError):
            block = load_data(self.new_nix_file, block_index=0,
                              input_format=None)

    def test_load_data_nwb_input_format(self):
        # Checks if the load function loads the first block of an NWB file
        # when the format is specified
        assert str(self.new_nwb_file.name) == "nwb_1.data"
        for dataset in (self.new_nwb_file,
                        self.dataset_files['nwb_1']):
            block = load_data(dataset, block_index=0,
                              input_format="NWBIO")
            self._check_block_objects_equal(first=block,
                                            second=self.blocks['nwb_1'][0],
                                            nwb=True)
            self._check_block_1_data(block, nwb=True)

    def test_load_data_nwb_wrong_input_format(self):
        # Checks if the load function raises ValueError when trying to load
        # an NWB file with wrong input specification
        assert str(self.new_nwb_file.name) == "nwb_1.data"
        for dataset in (self.new_nwb_file,
                        self.dataset_files['nwb_1']):
            with self.assertRaises(ValueError):
                block = load_data(dataset, block_index=0,
                                  input_format="NixIO")

    def test_load_data_nix_input_format(self):
        # Checks if the load function loads the first block of a NIX file
        # when the format is specified
        assert str(self.new_nix_file.name) == "nix_1.data"
        for dataset in (self.new_nix_file,
                        self.dataset_files['nix_1']):
            block = load_data(dataset, block_index=0,
                              input_format="NixIO")
            self._check_block_objects_equal(first=block,
                                            second=self.blocks['nix_1'][0],
                                            nwb=False)
            self._check_block_1_data(block, nwb=False)

    def test_load_data_nix_wrong_input_format(self):
        # Checks if the load function raises ValueError when trying to load
        # a NIX file with wrong input specification
        assert str(self.new_nix_file.name) == "nix_1.data"
        for dataset in (self.new_nix_file,
                        self.dataset_files['nix_1']):
            with self.assertRaises(ValueError):
                block = load_data(dataset, block_index=0,
                                  input_format="NWBIO")

    def test_load_data_nwb_wrong_index(self):
        # Checks if load function raises ValueError if a wrong Block index is
        # passed when trying to load NWB files
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nwb_1'], block_index=1)
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nwb_2'], block_index=2)

    def test_load_data_nix_wrong_index(self):
        # Checks if load function raises ValueError if a wrong Block index is
        # passed when trying to load NIX files
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nix_1'], block_index=1)
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nix_2'], block_index=2)

    def test_load_data_nwb_wrong_name(self):
        # Checks if load function raises ValueError if a wrong Block name is
        # passed when trying to load NWB files
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nwb_1'], block_name="Data 2")
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nwb_2'], block_name="Data 3")

    def test_load_data_nix_wrong_name(self):
        # Checks if load function raises ValueError if a wrong Block name is
        # passed when trying to load NIX files
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nix_1'], block_name="Data 2")
        with self.assertRaises(ValueError):
            block = load_data(self.dataset_files['nix_2'], block_name="Data 3")

    def test_load_data_nwb_by_index_one_block(self):
        # Checks if the load function loads the correct Block from an NWB file
        # with a single block when specifying its index
        block = load_data(self.dataset_files['nwb_1'], block_index=0)
        self._check_block_objects_equal(first=block,
                                        second=self.blocks['nwb_1'][0],
                                        nwb=True)
        self._check_block_1_data(block, nwb=True)

    def test_load_data_nwb_by_index_two_blocks(self):
        # Checks if the load function loads the correct Block from an NWB file
        # with two blocks when specifying its index
        block_1 = load_data(self.dataset_files['nwb_2'], block_index=0)
        self._check_block_objects_equal(first=block_1,
                                        second=self.blocks['nwb_2'][0],
                                        nwb=True)
        self._check_block_1_data(block_1, nwb=True)

        block_2 = load_data(self.dataset_files['nwb_2'], block_index=1)
        # FIXME: second block is read with the description of the first
        assert isinstance(block_2, neo.Block)
        # self._check_block_objects_equal(first=block_2,
        #                                 second=self.blocks['nwb_2'][1],
        #                                 nwb=True)
        self._check_block_2_data(block_2, nwb=True)

    def test_load_data_nwb_by_name_one_block(self):
        # Checks if the load function loads the correct Block from an NWB file
        # with one block when specifying its name
        block = load_data(self.dataset_files['nwb_1'], block_name="Data 1")
        self._check_block_objects_equal(first=block,
                                        second=self.blocks['nwb_1'][0],
                                        nwb=True)
        self._check_block_1_data(block, nwb=True)

    def test_load_data_nwb_by_name_two_blocks(self):
        # Checks if the load function loads the correct Block from an NWB file
        # with two blocks when specifying its name
        block_1 = load_data(self.dataset_files['nwb_2'], block_name="Data 1")
        self._check_block_objects_equal(first=block_1,
                                        second=self.blocks['nwb_2'][0],
                                        nwb=True)
        self._check_block_1_data(block_1, nwb=True)

        block_2 = load_data(self.dataset_files['nwb_2'], block_name="Data 2")
        assert isinstance(block_2, neo.Block)
        # FIXME: second block is read with the description of the first
        # self._check_block_objects_equal(first=block_2,
        #                                 second=self.blocks['nwb_2'][1],
        #                                 nwb=True)
        self._check_block_2_data(block_2, nwb=True)

    def test_load_data_nix_by_index_one_block(self):
        # Checks if the load function loads the correct Block from a NIX file
        # with a single block when specifying its index
        block = load_data(self.dataset_files['nix_1'], block_index=0)
        self._check_block_objects_equal(first=block,
                                        second=self.blocks['nix_1'][0],
                                        nwb=False)
        self._check_block_1_data(block, nwb=False)

    def test_load_data_nix_by_index_two_blocks(self):
        # Checks if the load function loads the correct Block from a NIX file
        # with two blocks when specifying its index
        block_1 = load_data(self.dataset_files['nix_2'], block_index=0)
        self._check_block_objects_equal(first=block_1,
                                        second=self.blocks['nix_2'][0],
                                        nwb=False)
        self._check_block_1_data(block_1, nwb=False)

        block_2 = load_data(self.dataset_files['nix_2'], block_index=1)
        self._check_block_objects_equal(first=block_2,
                                        second=self.blocks['nix_2'][1],
                                        nwb=False)
        self._check_block_2_data(block_2, nwb=False)

    def test_load_data_nix_by_name_one_block(self):
        # Checks if the load function loads the correct Block from a NIX file
        # with one block when specifying its name
        block = load_data(self.dataset_files['nix_1'], block_name="Data 1")
        self._check_block_objects_equal(first=block,
                                        second=self.blocks['nix_1'][0],
                                        nwb=False)
        self._check_block_1_data(block, nwb=False)

    def test_load_data_nix_by_name_two_blocks(self):
        # Checks if the load function loads the correct Block from a NIX file
        # with two blocks when specifying its name
        block_1 = load_data(self.dataset_files['nix_2'], block_name="Data 1")
        self._check_block_objects_equal(first=block_1,
                                        second=self.blocks['nix_2'][0],
                                        nwb=False)
        self._check_block_1_data(block_1, nwb=False)

        block_2 = load_data(self.dataset_files['nix_2'], block_name="Data 2")
        self._check_block_objects_equal(first=block_2,
                                        second=self.blocks['nix_2'][1],
                                        nwb=False)
        self._check_block_2_data(block_2, nwb=False)

    # Select data tests

    def test_select_data_analog_signal_by_single_index(self):
        # Checks if the data selection function loads an analog signal
        # from a block when specifying the index of the segment and the
        # analog signal. The return should be a list with a single item

        # Tests are based on blocks "Data 1" and "Data 2" from the "nix_2"
        # dataset.
        # We check if every analog signal is correctly loaded.
        # The verified attributes are name, description, and shape. They
        # are stored below according to the hierarchy in the block and order
        # in the segment. The expected IDs are also cross-checked.

        # For each block:
        # {Seg0: [(AS0 name, AS0 shape), (AS1 name, AS1 shape),...],
        #  Seg1: [(AS0 name, AS0 shape), (AS1 name, AS1 shape),...],
        #  ...}

        expected_signal_info = {
            "Data 1": {
                0: [("AS 1.1", (2000, 32)),
                    ("AS 1.2", (2000, 8))]
            },

            "Data 2": {
                0: [("AS 1.1", (3000, 32)),
                    ("AS 1.2", (3000, 8)),
                    ("AS 1.3", (3000, 16))],
                1: [("AS 2.1", (2000, 8)),
                    ("AS 2.2", (2000, 16))],
            }
        }

        test_iterations = {
            "Data 1": ((0, 0), (0, 1)),
            "Data 2": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1))
        }
        for block in self.blocks['nix_2']:
            block_name = block.name
            for segment_index, signal_index in test_iterations[block_name]:
                with self.subTest(
                        f"{block_name}, seg {segment_index}, signal {signal_index}",
                        block_name=block_name, seg=segment_index, signal=signal_index):
                    signals = select_data(block,
                                          segment_index=segment_index,
                                          analog_signal_index=signal_index)
                    assert isinstance(signals, list)
                    assert len(signals) == 1
                    assert isinstance(signals[0], neo.AnalogSignal)

                    expected_signal = block.segments[segment_index].analogsignals[signal_index]
                    signal = signals[0]

                    # Check if name, IDs and shape agree with the
                    # directly-loaded signal
                    assert signal.name == expected_signal.name
                    assert signal.description == expected_signal.description
                    assert signal.shape == expected_signal.shape

                    # Check if the expected information match
                    expected_sel_info = expected_signal_info[block_name][segment_index][signal_index]
                    assert signal.name == expected_sel_info[0]    # name
                    assert signal.shape == expected_sel_info[1]   # shape

    def test_select_data_analog_signal_wrong_index(self):
        # Checks if the data selection function raises ValueError when trying
        # to load an analog signal by index and the information is invalid

        block = self.blocks['nix_2'][1]

        # Non-existing segment
        with self.assertRaises(ValueError):
            select_data(block, segment_index=2, analog_signal_index=0)

        # Non-existing analog signal
        with self.assertRaises(ValueError):
            select_data(block, segment_index=0, analog_signal_index=3)
        with self.assertRaises(ValueError):
            select_data(block, segment_index=1, analog_signal_index=2)

        # Both Non-existing
        with self.assertRaises(ValueError):
            select_data(block, segment_index=2, analog_signal_index=3)

    def test_select_data_analog_signal_single_segment_signal_range(self):
        # Checks if the data selection function loads multiple analog signals
        # from a block when specifying the index of a single segment and the
        # range of analog signal indexes.
        # The function is expected to return a list with all the signals.
        # The range is specified by strings "start:end" index, inclusive.
        # "all" is a proxy for the full range of signals.

        # Tests are based on block "Data 2" from the "nix_2" dataset.
        block = self.blocks['nix_2'][1]
        segments = block.segments

        expected_signal_info = {
            0: {
                "0:1": [("AS 1.1", (3000, 32)),
                        ("AS 1.2", (3000, 8))],
                "0:2": [("AS 1.1", (3000, 32)),
                        ("AS 1.2", (3000, 8)),
                        ("AS 1.3", (3000, 16))],
                "1:2": [("AS 1.2", (3000, 8)),
                        ("AS 1.3", (3000, 16))],
                "all": [("AS 1.1", (3000, 32)),
                        ("AS 1.2", (3000, 8)),
                        ("AS 1.3", (3000, 16))],
            },

            1: {
                "0:1": [("AS 2.1", (2000, 8)), ("AS 2.2", (2000, 16))],
                "all": [("AS 2.1", (2000, 8)), ("AS 2.2", (2000, 16))],
            },
        }

        expected_objects = {
            0: {
                "0:1": [segments[0].analogsignals[0],
                        segments[0].analogsignals[1]],
                "0:2": [segments[0].analogsignals[0],
                        segments[0].analogsignals[1],
                        segments[0].analogsignals[2]],
                "1:2": [segments[0].analogsignals[1],
                        segments[0].analogsignals[2]],
                "all": [segments[0].analogsignals[0],
                        segments[0].analogsignals[1],
                        segments[0].analogsignals[2]],
            },

            1: {
                "0:1": [segments[1].analogsignals[0],
                        segments[1].analogsignals[1]],
                "all": [segments[1].analogsignals[0],
                        segments[1].analogsignals[1]],
            },
        }

        test_iterations = [(1, "0:1"), (1, "all"),
                           (0, "0:1"), (0, "0:2"), (0, "1:2"), (0, "all")]
        for segment_index, signal_index in test_iterations:
            with self.subTest(
                    f"Seg {segment_index}, multiple signal {signal_index}",
                    seg=segment_index, signal=signal_index):
                signals = select_data(self.blocks['nix_2'][1],
                                      segment_index=segment_index,
                                      analog_signal_index=signal_index)
                assert isinstance(signals, list)
                assert all([isinstance(signal, neo.AnalogSignal)
                            for signal in signals])

                expected_signals = expected_objects[segment_index][signal_index]
                expected_infos = expected_signal_info[segment_index][signal_index]
                assert len(signals) == len(expected_signals)

                for idx, signal in signals:
                    # Check if name, IDs and shape agree with the
                    # directly-loaded signal
                    assert signal.name == expected_signals[idx].name
                    assert signal.description == expected_signals[idx].description
                    assert signal.shape == expected_signals[idx].shape

                    # Check if the expected information match
                    expected_sel_info = expected_infos[idx]
                    assert signal.name == expected_sel_info[0]    # name
                    assert signal.shape == expected_sel_info[1]   # shape

    def test_select_data_analog_signal_segment_range_single_signal(self):
        # Checks if the data selection function loads multiple analog signals
        # from a block with multiple segments when specifying a range for
        # segment indexes and a single index for the analog signal inside
        # each segment.
        # The function is expected to return a list with all the signals.
        # The range is specified by strings "start:end" index, inclusive.
        # "all" is a proxy for the full range of segments.

        # Tests are based on block "Data 2" from the "nix_2" dataset.
        block = self.blocks['nix_2'][1]
        segments = block.segments

        expected_signal_info = {
            "0:1": {
                0: [("AS 1.1", (3000, 32)), ("AS 2.1", (2000, 8))],
                1: [("AS 1.2", (3000, 8)), ("AS 2.2", (2000, 16))],
            },
            "all": {
                0: [("AS 1.1", (3000, 32)), ("AS 2.1", (2000, 8))],
                1: [("AS 1.2", (3000, 8)), ("AS 2.2", (2000, 16))],
            },
        }

        expected_objects = {
            "0:1": {
                0: [segments[0].analogsignals[0],
                    segments[1].analogsignals[0]],
                1: [segments[0].analogsignals[1],
                    segments[1].analogsignals[1]],
            },
            "all": {
                0: [segments[0].analogsignals[0],
                    segments[1].analogsignals[0]],
                1: [segments[0].analogsignals[1],
                    segments[1].analogsignals[1]],
            },
        }

        expected_errors = [("0:1", 3), ("all", 3)]

        test_iterations = [("0:1", 0), ("0:1", 1), ("all", 0), ("all", 1)]
        for segment_index, signal_index in test_iterations:
            with self.subTest(
                    f"Multiple Seg {segment_index}, signal {signal_index}",
                    seg=segment_index, signal=signal_index):
                signals = select_data(self.blocks['nix_2'][1],
                                      segment_index=segment_index,
                                      analog_signal_index=signal_index)
                assert isinstance(signals, list)
                assert all([isinstance(signal, neo.AnalogSignal)
                            for signal in signals])

                expected_signals = expected_objects[segment_index][signal_index]
                expected_infos = expected_signal_info[segment_index][signal_index]
                assert len(signals) == len(expected_signals)

                for idx, signal in enumerate(signals):
                    # Check if name, IDs and shape agree with the
                    # directly-loaded signal
                    assert signal.name == expected_signals[idx].name
                    assert signal.description == expected_signals[idx].description
                    assert signal.shape == expected_signals[idx].shape

                    # Check if the expected information match
                    expected_sel_info = expected_infos[idx]
                    assert signal.name == expected_sel_info[0]    # name
                    assert signal.shape == expected_sel_info[1]   # shape

        # Check expected failures, i.e., requesting a signal index that does
        # not exist across all segments
        for segment_index, signal_index in expected_errors:
            with self.subTest(
                    f"Error mult seg {segment_index}, signal {signal_index}",
                    seg=segment_index, signal=signal_index):
                with self.assertRaises(ValueError):
                    select_data(self.blocks['nix_2'][1],
                                segment_index=segment_index,
                                signal_index=signal_index)

    @unittest.skip
    def test_select_data_analog_signal_by_name(self):
        # Checks if the data selection function loads an analog signal
        # from a block when specifying its name
        pass

    @unittest.skip
    def test_select_data_spike_train_by_index(self):
        # Checks if the data selection function loads a spike train
        # from a block when specifying the index of the segment and the
        # spike train
        pass

    @unittest.skip
    def test_select_data_spike_train_by_name(self):
        # Checks if the data selection function loads a spike train
        # from a block when specifying the name of the segment and the
        # spike train
        pass

    # Update data tests

    def test_prepare_data_invalid_options(self):
        # Checks if the function fails with ValueError for incorrect write
        # options. No block should be generated.
        # Valid options are "new", "replace", "add".
        # At least one data element must be provided.

        old_block = self.blocks['nix_1'][0]
        new_block = None
        new_signal = get_analog_signal(40 * pq.Hz, 8, 0.5 * pq.s, "new")
        generated_data = [new_signal]

        # Invalid actions
        with self.assertRaises(ValueError):
            new_block = prepare_data(old_block, analog_signal=generated_data,
                                     action="invalid")
        with self.assertRaises(ValueError):
            new_block = prepare_data(old_block, analog_signal=generated_data,
                                     action=None)
        # No data
        with self.assertRaises(ValueError):
            new_block = prepare_data(old_block, action="new")
        with self.assertRaises(ValueError):
            new_block = prepare_data(old_block, analog_signal=[],
                                     action="new")
        with self.assertRaises(ValueError):
            new_block = prepare_data(old_block, spike_train=[],
                                     action="new")
        assert new_block is None
        self._check_block_1_data(old_block, nwb=False)

    def test_prepare_data_new_block_single_analog_signal(self):
        # Checks if the function that prepares the block for saving generates
        # a new block storing the analog signal produced by the component.
        # The old block should not change, and a single segment with all the
        # signals should be generated.

        new_signal = [get_analog_signal(40 * pq.Hz, 8, 0.5 * pq.s, "new")]

        old_block = self.blocks['nix_1'][0]
        new_block = prepare_data(old_block, analog_signal=new_signal,
                                 action='new')
        assert new_block is not old_block

        # Old block (loaded at the beginning) should not change
        self._check_block_1_data(old_block, nwb=False)
        self._check_block_objects_equal(first=old_block,
                                        second=self.blocks['nix_1'][0],
                                        nwb=False)

        # New block should be generated with a single segment and the
        # analog signal is the only element
        assert len(new_block.segments) == 1
        assert len(new_block.segments[0].analogsignals) == 1
        assert len(new_block.segments[0].spiketrains) == 0
        assert new_block.segments[0].analogsignals[0].name == "new"
        assert new_block.segments[0].analogsignals[0].shape == (500, 8)
        assert new_block.segments[0].analogsignals[0].t_stop == 0.5 * pq.s

    def test_prepare_data_new_block_multiple_analog_signals(self):
        # Checks if the function that prepares the block for saving generates
        # a new block storing the analog signals produced by the component.
        # The old block should not change, and a single segment with all the
        # signals should be generated.
        new_signals = [
            get_analog_signal(40 * pq.Hz, 16, 0.5 * pq.s, "dual 1"),
            get_analog_signal(30 * pq.Hz,  4, 0.5 * pq.s, "dual 2")
        ]

        old_block = self.blocks['nix_1'][0]
        new_block = prepare_data(old_block, analog_signal=new_signals,
                                 action='new')
        assert new_block is not old_block

        # Old block (loaded at the beginning) should not change
        self._check_block_1_data(old_block, nwb=False)
        self._check_block_objects_equal(first=old_block,
                                        second=self.blocks['nix_1'][0],
                                        nwb=False)

        # New block should be generated with a single segment and 2
        # analog signals
        assert len(new_block.segments) == 1
        assert len(new_block.segments[0].analogsignals) == 2
        assert len(new_block.segments[0].spiketrains) == 0
        assert new_block.segments[0].analogsignals[0].name == "dual 1"
        assert new_block.segments[0].analogsignals[0].shape == (500, 16)
        assert new_block.segments[0].analogsignals[0].t_stop == 0.5 * pq.s
        assert new_block.segments[0].analogsignals[1].name == "dual 2"
        assert new_block.segments[0].analogsignals[1].shape == (500, 4)
        assert new_block.segments[0].analogsignals[1].t_stop == 0.5 * pq.s

    # Save data tests

    def test_save_data_invalid_options(self):
        # Checks if the function fails with ValueError for incorrect write
        # options. Actions allowed are "new", "replace", "update".
        # File must not be saved in case of invalid options.

        new_block = generate_block_1(datetime.now())
        new_file = Path(self.tmp_dir.name) / f"{uuid.uuid4()}.data"
        assert not new_file.exists()

        with self.assertRaises(ValueError):
            save_data(new_block, new_file, action="invalid")
        with self.assertRaises(ValueError):
            save_data(new_block, new_file, action=None)
        assert not new_file.exists()

        # Invalid output format
        with self.assertRaises(ValueError):
            save_data(new_block, new_file, output_format="invalid")
        assert not new_file.exists()

    def test_save_data_failed_detect_output_format(self):
        # Checks if the save function raises ValueError if the output format
        # was not specified and the format could not be inferred when trying
        # to save a block
        output_file = Path(self.tmp_dir.name) / "new_block.data"
        new_block = generate_block_1(datetime.now())
        assert not output_file.exists()
        with self.assertRaises(ValueError):
            save_data(new_block, output_file=output_file, output_format=None,
                      action="new")

    def test_save_data_new_non_existing(self):
        # Checks if the save function saves the block to a file that does not
        # exist with the "new" action. The new file will have only the saved
        # block. The behavior should be the same with or without format
        # specification.

        for file_format, output_format in (("data", "NixIO"),
                                           ("data", "NWBIO"),
                                           ("nix", None),
                                           ("nwb", None)):
            nwb = ((file_format == "nwb") or
                   ((file_format == "data") and (output_format == "NWBIO")))

            with self.subTest(f"Save new non existing file",
                              file_format=file_format,
                              output_format=output_format,
                              nwb=nwb):
                file_name = f"{uuid.uuid4()}.{file_format}"
                output_file = Path(self.tmp_dir.name) / file_name
                new_block = generate_block_1(datetime.now())

                assert not output_file.exists()
                save_data(new_block, output_file=output_file,
                          output_format=output_format, action="new")

                function_key = 'nwb' if nwb else 'nix'

                # Check if file was saved correctly
                saved_blocks = READ_FUNCTIONS[function_key](output_file)
                assert len(saved_blocks) == 1
                self._check_block_objects_equal(
                    first=new_block,
                    second=saved_blocks[0],
                    nwb=nwb
                )
                self._check_block_1_data(saved_blocks[0], nwb=nwb)

                # Load should fail for incorrect format
                with self.assertRaises(ValueError):
                    load_data(output_file,
                              input_format="NWBIO" if nwb else "NixIO")

    @unittest.skip
    def test_save_data_new_existing_nix(self):
        # Checks if the save function saves the block to a NIX file that exists
        # with the "new" action. The new file will have all the existing blocks
        # and the new block will be appended. The behavior should be the same
        # with or without format specification.
        pass

    @unittest.skip
    def test_save_data_new_existing_nwb(self):
        # Checks if the save function saves the block to an NWB file that
        # exits with the "new" action. The new file will have all the existing
        # blocks and the new block will be appended. The behavior should be the
        # same with or without format specification.
        pass

    @unittest.skip
    def test_save_data_replace_existing_file_nix_single_block(self):
        # Checks if the save function saves a new block to an existing NIX file
        # with a single block. This should replace the existing data in the
        # file with the new data provided.
        pass

    @unittest.skip
    def test_save_data_replace_existing_file_nix_multiple_block(self):
        # Checks if the save function saves a new block to an existing NIX file
        # with multiple blocks. This should replace only the existing
        # block whose new data is being provided.
        pass

    @unittest.skip
    def test_save_data_replace_existing_file_nwb_single_block(self):
        # Checks if the save function saves a new block to an existing NWB file
        # with a single block. This should replace the existing data in the
        # file with the new data provided.
        pass

    @unittest.skip
    def test_save_data_replace_existing_file_nwb_multiple_block(self):
        # Checks if the save function saves a new block to an existing NWB file
        # with multiple blocks. This should replace only the existing
        # block whose new data is being provided.
        pass

    @unittest.skip
    def test_save_data_update_existing_file_nix_single_block(self):
        # Checks if the save function saves the block to an existing NIX file
        # with a single block when using the "update" action.
        # This should update the block in the file to add any new data.
        pass

    @unittest.skip
    def test_save_data_update_existing_file_nix_multiple_block(self):
        # Checks if the save function saves the block to an existing NIX file
        # with multiple block when using the "update" action.
        # This should update the modified block in the file to add any new
        # data.
        pass

    @unittest.skip
    def test_save_data_update_existing_file_nwb_single_block(self):
        # Checks if the save function saves the block to an existing NWB file
        # with a single block when using the "update" action.
        # This should update the block in the file to add any new data.
        pass

    @unittest.skip
    def test_save_data_update_existing_file_nwb_multiple_block(self):
        # Checks if the save function saves the block to an existing NWB file
        # with multiple block when using the "update" action.
        # This should update the modified block in the file to add any new
        # data.
        pass

    @classmethod
    def tearDownClass(cls):
        # Clean temporary folder
        cls.tmp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
