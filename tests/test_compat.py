# Copyright (c) 2020 Leiden University Medical Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gzip
import itertools
import zlib
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from isal import igzip, isal_zlib

import pytest

DATA_DIR = Path(__file__).parent / "data"
COMPRESSED_FILE = DATA_DIR / "test.fastq.gz"
with gzip.open(str(COMPRESSED_FILE), mode="rb") as file_h:
    DATA = file_h.read()

DATA_SIZES = [2**i for i in range(3, 20)]
# 100 seeds generated with random.randint(0, 2**32-1)
SEEDS_FILE = DATA_DIR / "seeds.txt"
INT_OVERFLOW = 211928379812738912738917238971289378912379823871932719823798123
# Get some negative ints and some really big ints into the mix.
SEEDS = [-INT_OVERFLOW, -3, -1, 0, 1, INT_OVERFLOW] + [
    int(seed) for seed in SEEDS_FILE.read_text().splitlines()]

# Wbits for ZLIB compression, GZIP compression, and RAW compressed streams
WBITS_RANGE = list(range(9, 16)) + list(range(25, 32)) + list(range(-15, -8))


@pytest.mark.parametrize(["data_size", "value"],
                         itertools.product(DATA_SIZES, SEEDS))
def test_crc32(data_size, value):
    data = DATA[:data_size]
    assert zlib.crc32(data, value) == isal_zlib.crc32(data, value)


@pytest.mark.parametrize(["data_size", "value"],
                         itertools.product(DATA_SIZES, SEEDS))
def test_adler32(data_size, value):
    data = DATA[:data_size]
    assert zlib.adler32(data, value) == isal_zlib.adler32(data, value)


@pytest.mark.parametrize(["data_size", "level"],
                         itertools.product(DATA_SIZES, range(4)))
def test_compress(data_size, level):
    data = DATA[:data_size]
    compressed = isal_zlib.compress(data, level=level)
    assert zlib.decompress(compressed) == data


@pytest.mark.parametrize(["data_size", "level"],
                         itertools.product(DATA_SIZES, range(10)))
def test_decompress_zlib(data_size, level):
    data = DATA[:data_size]
    compressed = zlib.compress(data, level=level)
    decompressed = isal_zlib.decompress(compressed)
    assert decompressed == data


@pytest.mark.parametrize(["data_size", "level", "wbits", "memLevel"],
                         itertools.product([128 * 1024], range(4),
                                           WBITS_RANGE, range(1, 10)))
def test_decompress_wbits(data_size, level, wbits, memLevel):
    data = DATA[:data_size]
    compressobj = zlib.compressobj(level=level, wbits=wbits, memLevel=memLevel)
    compressed = compressobj.compress(data) + compressobj.flush()
    decompressed = isal_zlib.decompress(compressed, wbits=wbits)
    assert data == decompressed


@pytest.mark.parametrize(["data_size", "level"],
                         itertools.product(DATA_SIZES, range(4)))
def test_decompress_isal_zlib(data_size, level):
    data = DATA[:data_size]
    compressed = isal_zlib.compress(data, level=level)
    decompressed = isal_zlib.decompress(compressed)
    print(len(decompressed))
    assert decompressed == data


@pytest.mark.parametrize(["data_size", "level", "wbits", "memLevel"],
                         itertools.product([128 * 1024], range(4),
                                           WBITS_RANGE, range(1, 10)))
def test_compress_compressobj(data_size, level, wbits, memLevel):
    data = DATA[:data_size]
    compressobj = isal_zlib.compressobj(level=level,
                                        wbits=wbits,
                                        memLevel=memLevel)
    compressed = compressobj.compress(data) + compressobj.flush()
    if wbits in range(8, 16):
        # TODO: Apparently the wbits level is not correctly implemented in
        # ISA-L for the zlib stuff.
        decompressed = zlib.decompress(compressed, wbits=15)
    else:
        decompressed = zlib.decompress(compressed, wbits=wbits)
    assert data == decompressed


@pytest.mark.parametrize(["data_size", "level", "wbits", "memLevel"],
                         itertools.product([128 * 1024], range(4),
                                           WBITS_RANGE, range(1, 10)))
def test_decompress_decompressobj(data_size, level, wbits, memLevel):
    data = DATA[:data_size]
    compressobj = zlib.compressobj(level=level, wbits=wbits, memLevel=memLevel)
    compressed = compressobj.compress(data) + compressobj.flush()
    decompressobj = isal_zlib.decompressobj(wbits=wbits)
    decompressed = decompressobj.decompress(compressed) + decompressobj.flush()
    assert data == decompressed
    assert decompressobj.unused_data == b""
    assert decompressobj.unconsumed_tail == b""


def test_decompressobj_unconsumed_tail():
    data = DATA[:128*1024]
    compressed = zlib.compress(data)
    decompressobj = isal_zlib.decompressobj()
    output = decompressobj.decompress(compressed, 2048)
    assert len(output) == 2048


@pytest.mark.parametrize(["data_size", "level"],
                         itertools.product(DATA_SIZES, range(4)))
def test_igzip_compress(data_size, level):
    data = DATA[:data_size]
    compressed = igzip.compress(data, compresslevel=level)
    assert gzip.decompress(compressed) == data


@pytest.mark.parametrize(["data_size", "level"],
                         itertools.product(DATA_SIZES, range(10)))
def test_decompress_gzip(data_size, level):
    data = DATA[:data_size]
    compressed = gzip.compress(data, compresslevel=level)
    decompressed = igzip.decompress(compressed)
    assert decompressed == data


@pytest.mark.parametrize(["data_size", "level"],
                         itertools.product(DATA_SIZES, range(4)))
def test_decompress_igzip(data_size, level):
    data = DATA[:data_size]
    compressed = igzip.compress(data, compresslevel=level)
    decompressed = igzip.decompress(compressed)
    print(len(decompressed))
    assert decompressed == data


@pytest.mark.parametrize(["unused_size", "wbits"],
                         itertools.product([26], [-15, 15, 31]))
def test_unused_data(unused_size, wbits):
    unused_data = b"abcdefghijklmnopqrstuvwxyz"[:unused_size]
    compressor = zlib.compressobj(wbits=wbits)
    data = b"A meaningful sentence starts with a capital and ends with a."
    compressed = compressor.compress(data) + compressor.flush()
    decompressor = isal_zlib.decompressobj(wbits=wbits)
    result = decompressor.decompress(compressed + unused_data)
    assert result == data
    assert decompressor.unused_data == unused_data
