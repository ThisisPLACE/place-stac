#!/bin/bash

python place/place-image/cli_single.py \
    --raw-image sample_data/aerial/tiff_untagged/DSC00393.ARW \
    --output output/aerial/DSC00393-example-rotation.tif \
    --latitude 5.332497779 \
    --longitude -3.990424374 \
    --altitude 222.168 \
    --rotation-matrix 0.399309147 0.916803984 0.004760354 -0.916775226 0.399236683 0.011543703 0.008682805 -0.008973681 0.999922038


python place/place-image/cli_single.py \
    --raw-image "s3://placetrustafrica/Ivory Coast/Abidjan/Drone Imagery/Images_Drones/Drone_V-MAP/Adjame/Flight 2S/geotagged/DSC00562_geotag.JPG" \
    --output output/aerial/DSC00562-example-rotation.tif \
    --latitude 5.370299 \
    --longitude -4.035804 \
    --altitude 175.8 \
    --rotation-matrix 0.0584689982982420 0.2261183855207186 -0.9723434845606282 0.0804137748602547 -0.9719114854061948 -0.2211824797497504 -0.9950452256308375 -0.0652574920222046 -0.0750097239312840

python place/place-image/cli_single.py \
    --raw-image "s3://placetrustafrica/Ivory Coast/Abidjan/Drone Imagery/Images_Drones/Drone_V-MAP/Adjame/Flight 2S/geotagged/DSC01173_geotag.JPG" \
    --output output/aerial/DSC00562-example-rotation.tif \
    --latitude 5.359087 \
    --longitude -4.024535 \
    --altitude 177.28571428571428 \
    --rotation-matrix 0.0584689982982420 0.2261183855207186 -0.9723434845606282 0.0804137748602547 -0.9719114854061948 -0.2211824797497504 -0.9950452256308375 -0.0652574920222046 -0.0750097239312840

python place/place-image/cli_multiple.py \
    --raw-image-dir sample_data/aerial/tiff_untagged \
    --output-dir output/aerial \
    --location-table sample_data/aerial/tiff_untagged/Images_Lat_Long_Ht.xlsx \
    --pko-table sample_data/aerial/Demo\ Camera\ XYZKPO.csv
