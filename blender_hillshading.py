# no shebang line because this does not run autonomously

import argparse
from math import radians
from os import path
import sys

from osgeo import gdal
gdal.UseExceptions()

import rasterio

import bpy


def get_metadata(filepath):
    # dataset = gdal.OpenEx(filepath, gdal.OF_READONLY|gdal.OF_RASTER|gdal.OF_VERBOSE_ERROR)

    # x = dataset.RasterXSize
    # y = dataset.RasterYSize



    # projection = dataset.GetProjection()

    # dataset.Close()

    with rasterio.open(filepath) as dataset:
        width  = dataset.width
        height = dataset.height

        # no need, the transform provides all this data
        # ullr = dataset.bounds

        crs = dataset.crs
        transform = dataset.transform

    return width, height, crs, transform


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--render-samples', '-s', type=int, default=200)
    parser.add_argument('--render-scale',         type=int, default=100)
    parser.add_argument('--height-scale',   '-x', type=float)
    parser.add_argument('--render-tile-size',     type=int, default=512)

    # these two are needed to avoid this error:
    # blender: error: unrecognized arguments: --background --python
    parser.add_argument('--background', action='store_true')
    parser.add_argument('--python')

    parser.add_argument('file', metavar='FILE')

    opts = parser.parse_args()

    # opts.path, opts.filename = path.split(path.abspath(path.expanduser(opts.file)))
    opts.path, opts.filename = path.split(path.expanduser(opts.file))

    return opts

opts = parse_args()
print(opts)

width, height, crs, transform = get_metadata(opts.file)

print((width, height, crs, transform))
# sys.exit(0)

# Namespace(render_samples=None, render_scale=100, height_scale=None,
#           file='data/height/mapzen/N46E005-reprojected-compensated.tif', background=True, python='blender.py',
#           path='/home/mdione/src/projects/elevation/data/height/mapzen',
#           filename='N46E005-reprojected-compensated.tif')

# print(opts)

# sys.exit(0)

# RENDER_SAMPLES = 20
# RENDER_SCALE = 100
# HEIGHT_SCALE = 10
# FILE_PATH = '/home/mdione/src/projects/elevation/data/height/mapzen'

# image witdh is constant
# IMAGE_X = 3601

# height varies by latitude
# FILE_NAME = 'N45E007-reprojected-compensated.tif'
# IMAGE_Y = 5137
# FILE_NAME = 'N44E005-reprojected-compensated.tif'
# IMAGE_Y = 5049
# FILE_NAME = 'N43E005-reprojected-compensated.tif'
# IMAGE_Y = 4964
# FILE_NAME = 'N28E083-reprojected-compensated.tif'
# IMAGE_Y = 4097

SUN_SIZE = 45
SUN_STRENGTH = 15

## Sidequest: delete default cube

    # See https://k3no.medium.com/the-basics-of-using-python-in-blender-46831fd094e6

bpy.ops.object.select_all(action='DESELECT')

try:
    ### Select the default cube
    cube = bpy.data.objects['Cube']
    cube.select_set(True)

    ### Delete the default cube
    bpy.ops.object.delete()
except KeyError:
    pass

## Getting set up

    # nothing to do, really

## Blender Basics

### Render -> Render Engine -> Cycles
scene = bpy.data.scenes['Scene']

scene.render.engine = 'CYCLES'

### Render -> Feature Set -> Experimental
scene.cycles.feature_set = 'EXPERIMENTAL'
scene.cycles.samples = opts.render_samples
scene.cycles.tile_size = opts.render_tile_size

## The Plane

### Add -> Mesh -> Plane

    # TODO: add more planes with the other tiles

    # TODO: get the scale from the file's metadada
bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
central_plane = bpy.data.objects['Plane']
central_plane.scale = (width / 1000, height / 1000, 1.0)

    # Select it so it becomes te context for many of the following ops
    # central_plane.select_set(True)

### Object -> Transform -> Location

#### already happens because we set it on creation

### Object -> Transform -> Scale

#### also already set

### Material -> New

    # thanks intrac_#blender@libera.chat and Andrej/Andrej730#python@blender.chat

    # this way we only get an empty material shader graph, and I don't know how to add stuff
bpy.data.materials.new('Surface')
central_material = bpy.data.materials['Surface']
central_plane.active_material = central_material

    # ugh
central_material.use_nodes = True

    # some shortcuts
central_output = central_material.node_tree.nodes["Material Output"]

    # bpy.ops.node.add_node(use_transform=True, type="ShaderNodeOutputMaterial")
    # RuntimeError: Operator bpy.ops.node.add_node.poll() failed, context is incorrect

    # but I don't know how to set the context, maybe
    # bpy.context.area.ui_type = 'ShaderNodeTree'
    # this chages _this_ area (the python console), maybe I need to select another area?

    # TODO: I don't really like setting context, but really, for the moment, the API is so opaque,
    # it's the easiest way to do it

    # bpy.context.space_data.context = 'MATERIAL'
    # AttributeError: 'SpaceConsole' object has no attribute 'context'

    # bpy.ops.material.new()
    # central_material = bpy.data.materials['Material.001']


## Shader Editor

### Add -> Texture -> Image Texture

    # bpy.ops.node.add_node(use_transform=True, type="ShaderNodeTexImage")
central_texture = central_material.node_tree.nodes.new('ShaderNodeTexImage')

### Image Texture -> Open
bpy.ops.image.open(filepath=opts.filename,
                   directory=opts.path,
                   files=[{ "name": opts.filename, "name": opts.filename }],
                   relative_path=True, show_multiview=False)

image = bpy.data.images[opts.filename]
# image.colorspace_settings.name = 'Linear'
image.colorspace_settings.name = 'XYZ'
central_texture.image = image

### Add -> Vector -> Displacement

    # bpy.ops.node.add_node(use_transform=True, type="ShaderNodeDisplacement")
central_displacement = central_material.node_tree.nodes.new('ShaderNodeDisplacement')
central_displacement.inputs[2].default_value = opts.height_scale

### Texture -> Outputs -> Color -> Link -> Material -> Inputs -> Displacement

    # >>> print(central_texture.outputs[0])
    # <bpy_struct, NodeSocketColor("Color") at 0x7f8934d10c08>
src_1 = central_texture.outputs[0]
dst_1 = central_displacement.inputs[0]
central_material.node_tree.links.new(src_1, dst_1)

    # >>> print(central_output.inputs[2])
    # <bpy_struct, NodeSocketVector("Displacement") at 0x7f8969049a08>
src_2 = central_displacement.outputs[0]
dst_2 = central_output.inputs[2]
central_material.node_tree.links.new(src_2, dst_2)

### Texture -> Interpolation -> Smart
central_texture.interpolation = 'Smart'

### Texture -> Extrapolation -> Extend
central_texture.extension = 'EXTEND'

### Modifiers -> Add Modifier → Subdivision Surface
bpy.ops.object.modifier_add(type='SUBSURF')

### Subdivision Type -> Simple
bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'

### Adaptative Subdivision
bpy.context.object.cycles.use_adaptive_subdivision = True

### Material -> Surface -> Displacement -> Displacement Only
    # Seems to automatically be done in Material -> Displacement
central_material.cycles.displacement_method = 'DISPLACEMENT'
    
### Fun with Materials

shader = central_material.node_tree.nodes["Principled BSDF"]

    # color
shader.inputs[0].default_value = (0.402, 0.402, 0.402, 1)
    # specular
shader.inputs[7].default_value = 0
    # Roughness
shader.inputs[9].default_value = 1

## The Camera

### Positioning the Camera

    # z is not that important
camera = bpy.data.objects['Camera']
camera.location = (0, 0, 5)
camera.rotation_euler = (0, 0, 0)

### Set Aspect Ratio

    # Size is 7201, 4884
scene.render.resolution_x = width
scene.render.resolution_y = height

### Camera -> Lens -> Type -> Orthographic

    # now the camera's specific properties
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2 * max((width, height)) / 1000

## The Sun


### Choose Light Type and Strength


sun = bpy.data.objects['Light']
sun.data.type = 'SUN'

# bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
# sun = bpy.data.objects['Sun']

sun.data.energy = SUN_STRENGTH

### Set Sun Angle

sun.rotation_euler = (0, radians(45), radians(135))

### Sun Size

sun.data.angle = radians(SUN_SIZE)

## Render

scene.render.image_settings.file_format = 'TIFF'
scene.render.image_settings.color_mode = 'BW'

basename = path.splitext(opts.filename)[0]
output_filename = f"{opts.path}/{basename}-x{opts.height_scale}-{opts.render_samples}_samples-{opts.render_scale}%_{SUN_SIZE}x{SUN_STRENGTH}sun.tiff"
scene.render.filepath = output_filename

scene.render.resolution_percentage = opts.render_scale
scene.cycles.use_denoising = False

from datetime import datetime

start = datetime.now()
bpy.ops.render.render(write_still=1)
end = datetime.now()

print(end-start)

    # copy GeoTIFF metadata

# dataset = rasterio.open(output_filename, 'w')
# rasterio is not useful for just modifying the metadada
# so we load all the data, change the metadata, and write again :(((

# NotGeoreferencedWarning: Dataset has no geotransform, gcps, or rpcs. The identity matrix will be returned.
in_dataset  = rasterio.open(output_filename)

# read everything
data = in_dataset.read()
in_dataset.close()

out_dataset = rasterio.open(output_filename, 'w', driver='GTiff', height=height, width=width,
                            count=1, dtype=data.dtype, crs=crs, transform=transform)
out_dataset.write(data)
out_dataset.close()
