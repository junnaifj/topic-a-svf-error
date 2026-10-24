"""Small checks for the acceptance threshold and native-grid clipping."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from prepare_cedd_rasters import pair_check, snap_window, write_raster


class RasterPreparationChecks(unittest.TestCase):
    def test_tolerance_and_strictly_more_than_99_percent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            terrain = np.zeros((10, 10), dtype='float32')
            transform = Affine(.5, 0, 100, 0, -.5, 200)
            write_raster(root/'dtm.tif', terrain, transform, -9999)
            # Every pixel is slightly negative: strict ordering fails, tolerance passes.
            surface = np.full_like(terrain, -.1)
            for below, expected in [(0, True), (1, False), (2, False)]:
                surface[:] = -.1
                surface.ravel()[:below] = -.4
                write_raster(root/'dsm.tif', surface, transform, -9999)
                result = pair_check(root/'dsm.tif', root/'dtm.tif')
                self.assertEqual(result['passes_core_tolerance'], expected)
                self.assertEqual(result['below_minus_0p3_pixels'], below)
                self.assertEqual(result['negative_pixels'], 100)
                self.assertFalse(result['passes_strictly_over_99_percent'])

    def test_snap_outward_and_reject_missing_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'grid.tif'
            write_raster(path, np.ones((10, 10), dtype='float32'), Affine(.5, 0, 100, 0, -.5, 200), -9999)
            with rasterio.open(path) as ds:
                self.assertEqual(snap_window([100.1, 195.2, 104.8, 199.9], ds), rasterio.windows.Window(0, 0, 10, 10))
                with self.assertRaises(ValueError):
                    snap_window([99, 195, 105, 200], ds)

    def test_half_pixel_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            z = np.ones((10, 10), dtype='float32')
            write_raster(root/'dsm.tif', z, Affine(.5, 0, 100, 0, -.5, 200), -9999)
            write_raster(root/'dtm.tif', z, Affine(.5, 0, 100.25, 0, -.5, 200), -9999)
            with self.assertRaises(ValueError):
                pair_check(root/'dsm.tif', root/'dtm.tif')


if __name__ == '__main__':
    unittest.main()
