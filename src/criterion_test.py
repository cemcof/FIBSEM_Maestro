import tifffile
#from autoscript_sdb_microscope_client.structures import AdornedImage
from fibsem_maestro.image_criteria.criteria import Criterion
from tifffile import imread

import os
import numpy as np

from fibsem_maestro.settings import Settings
from fibsem_maestro.tools.support import Image

settings_yaml_path = 'fibsem_maestro/GUI/settings.yaml'
folder_path = "/home/pavelkrep/data/Cryo INS/standard trench/Image90_map/"

settings = Settings()
settings.load(settings_yaml_path)
#af = settings('autofunction', af_name, 'criterion_name')
af = 'image_acquisition'
criterion = Criterion(af)

for i, filename in enumerate(os.listdir(folder_path)):
    if filename.endswith(".tif") or filename.endswith(".tif"):
        full_filename = os.path.join(folder_path, filename)
        image = Image(imread(full_filename), 2.5e-9)
        #image = Image.from_as(AdornedImage.load(full_filename))
        res, map, tile = criterion(image, generate_map=True, return_best_tile=True)
        #res = criterion(image)
        print(f'{filename}: {res}')

        map = np.array(map)
        map = np.nan_to_num(map, np.nanmax(map))
        map[map==0] = np.nanmax(map)

        print('Min: ',np.min(map))
        print('Max: ',np.max(map))

        map = map - np.nanmin(map)
        map = map / np.nanmax(map) * 255

        tifffile.imwrite((os.path.join(folder_path, f'map_{i}.tiff')), 255-np.asarray(map, dtype=np.uint8))
        tifffile.imwrite((os.path.join(folder_path, f'tile.tiff')), tile)
#         if i == 1:
#             best = c
#         if i == 3:
#             worst = c
#
# print((best - worst)/best * 100)
