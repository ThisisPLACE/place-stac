#!/bin/bash

python place/cli_single.py \
    --raw-image sample_data/aerial/tiff_untagged/DSC00393.ARW \
    --output output/aerial/DSC00393-example-rotation.tif \
    --latitude 5.332497779 \
    --longitude -3.990424374 \
    --altitude 222.168 \
    --rotation-matrix 0.399309147 0.916803984 0.004760354 -0.916775226 0.399236683 0.011543703 0.008682805 -0.008973681 0.999922038

python place/cli_multiple.py \
    --raw-image-dir sample_data/aerial/tiff_untagged \
    --output-dir output/aerial \
    --location-table sample_data/aerial/tiff_untagged/Images_Lat_Long_Ht.xlsx \
    --pko-table sample_data/aerial/Demo\ Camera\ XYZKPO.csv