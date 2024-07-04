import unittest
import tempfile
from pathlib import Path
import itertools
from datetime import datetime

import numpy as np
import quantities as pq
import neo
from elephant.spike_train_generation import StationaryPoissonProcess
#TODO: import load data from utils


np.random.seed(1234)


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


def generate_neo_data():
    # Block 1: 1 Segment with 2 AnSigs + 1 SpikeTrain list
    block_1 = neo.Block(name="Data 1")
    signals = [get_analog_signal(freq, n_channels, t_stop=2*pq.s, name=name)
               for freq, n_channels, name in ((20*pq.Hz, 32, "AS 1.1"),
                                              (30*pq.Hz, 8, "AS 1.2"))]
    spiketrains = get_spike_trains(15 * pq.Hz, 30, t_stop=2*pq.s,
                                   source="Region 1")
    segment = neo.Segment(name="Segment 1")
    segment.analogsignals.extend(signals)
    segment.spiketrains.extend(spiketrains)
    block_1.segments.append(segment)

    # Block 2: 1 Segment with 3 AnSigs + 2 SpikeTrain lists and
    # 1 Segment with 2 AnSigs + 1 SpikeTrain list
    block_2 = neo.Block(name="Data 2")
    signals = [get_analog_signal(freq, n_channels, t_stop, name=name)
               for freq, n_channels, name, t_stop in
               ((10*pq.Hz, 32, "AS 1.1", 3*pq.s),
                (20*pq.Hz,  8, "AS 1.2", 3*pq.s),
                (30*pq.Hz,  16, "AS 1.3", 3*pq.s),
                (15*pq.Hz, 8, "AS 2.1", 2*pq.s),
                (25*pq.Hz, 16, "AS 2.2", 2*pq.s))]
    spiketrains = [get_spike_trains(firing_rate, n_spiketrains, t_stop=t_stop,
                                    source=source)
                   for firing_rate, n_spiketrains, source, t_stop in
                   ((30*pq.Hz, 15, "ST 1.1", 3*pq.s),
                    (15*pq.Hz, 30, "ST 1.2", 3*pq.s),
                    (20*pq.Hz, 10, "ST 2", 2*pq.s))]

    seg_2_1 = neo.Segment(name="Segment 1")
    seg_2_1.analogsignals.extend(signals[:3])
    for sts in spiketrains[:2]:
        seg_2_1.spiketrains.extend(sts)
    seg_2_2 = neo.Segment(name="Segment 2")
    seg_2_2.analogsignals.extend(signals[3:])
    seg_2_2.spiketrains.extend(spiketrains[2])
    block_2.segments.append(seg_2_1)
    block_2.segments.append(seg_2_2)

    # Group into return list, add NWB-required annotations and create all
    # relationships
    blocks = [block_1, block_2]
    for block in blocks:
        block.annotate(session_start_time=datetime.now())
        block.create_relationship()
    return blocks


# File IO funtions


WRITE_ARGS = {
    'nwb': {'io_type': neo.NWBIO, 'io_args': ('w',)},
    'nix': {'io_type': neo.NixIO, 'io_args': ('ow',)},
}


def write_dataset(filename, blocks, io_type, io_args):
    io = io_type(filename, *io_args)
    for block in blocks:
        io.write_block(block)


# Unit tests


class ElephantUtilsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Generate Neo data blocks
        cls.blocks = generate_neo_data()

        # Write temporary files
        # A dictionary stores the paths to the file names
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.data_files = {}
        for file_format in ('nwb', 'nix'):
            for num_blocks in range(1, 3):
                file_stem = f"{file_format}_{num_blocks}"
                dest_file = Path(cls.tmp_dir.name) / f"{file_stem}.{file_format}"
                cls.data_files[file_stem] = dest_file
                write_args = WRITE_ARGS[file_format]
                write_dataset(dest_file, cls.blocks[:num_blocks], **write_args)

    def test_data(self):
        # TODO: ensure block structure is as expected
        block_1 = self.blocks[0]
        assert len(block_1.segments) == 1
        assert block_1.name == "Data 1"
        seg_1 = block_1.segments[0]
        assert seg_1.name == "Segment 1"
        assert seg_1.t_stop == 2*pq.s
        assert len(seg_1.analogsignals) == 2

    @classmethod
    def tearDownClass(cls):
        # Clean temporary folder
        cls.tmp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
