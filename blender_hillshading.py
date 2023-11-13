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
    with rasterio.open(filepath) as dataset:
        width  = dataset.width
        height = dataset.height

        crs = dataset.crs
        transform = dataset.transform

    return width, height, crs, transform


def plane(x, y, lat, lon, opts):
    # print(locals())

    filename = opts.filename.format(**locals())

    # I wish I could use f-strings for pattern
    width, height, crs, transform = get_metadata(opts.pattern.format(**locals()))

    print((width, height, crs, transform))

    # The Plane
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    central_plane = bpy.data.objects['Plane']
    central_plane.scale = (width / 1000, height / 1000, 1.0)

    # thanks intrac_#blender@libera.chat and Andrej/Andrej730#python@blender.chat
    bpy.data.materials.new('Surface')
    central_material = bpy.data.materials['Surface']
    central_plane.active_material = central_material

    # ugh
    central_material.use_nodes = True

    # some shortcuts
    central_output = central_material.node_tree.nodes["Material Output"]

    # Shader Editor
    central_texture = central_material.node_tree.nodes.new('ShaderNodeTexImage')
    bpy.ops.image.open(filepath=filename,
                       directory=opts.path,
                       files=[{ "name": filename, "name": filename }],
                       relative_path=True, show_multiview=False)

    image = bpy.data.images[filename]
    # image.colorspace_settings.name = 'Linear'
    image.colorspace_settings.name = 'XYZ'
    central_texture.image = image

    central_displacement = central_material.node_tree.nodes.new('ShaderNodeDisplacement')
    central_displacement.inputs[2].default_value = opts.height_scale

    # connect them
    src_1 = central_texture.outputs[0]
    dst_1 = central_displacement.inputs[0]
    central_material.node_tree.links.new(src_1, dst_1)

    src_2 = central_displacement.outputs[0]
    dst_2 = central_output.inputs[2]
    central_material.node_tree.links.new(src_2, dst_2)

    central_texture.interpolation = 'Smart'
    central_texture.extension = 'EXTEND'
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'
    bpy.context.object.cycles.use_adaptive_subdivision = True
    central_material.cycles.displacement_method = 'DISPLACEMENT'

    # Fun with Materials
    shader = central_material.node_tree.nodes["Principled BSDF"]
    shader.inputs[0].default_value = (0.402, 0.402, 0.402, 1)  # color
    shader.inputs[7].default_value = 0  # specular
    shader.inputs[9].default_value = 1  # Roughness

    return height, width, crs, transform


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--render-samples', '-s', type=int, default=200)
    parser.add_argument('--render-scale',         type=int, default=100)
    parser.add_argument('--height-scale',   '-x', type=float, required=True)
    parser.add_argument('--render-tile-size',     type=int, default=512)
    parser.add_argument('--lat',            '-l', type=int, required=True)
    parser.add_argument('--lon', '--long',  '-L', type=int, required=True)
    parser.add_argument('--pattern',        '-p', required=True)

    # these two are needed to avoid this error:
    # blender: error: unrecognized arguments: --background --python
    parser.add_argument('--background', action='store_true')
    parser.add_argument('--python')

    # parser.add_argument('file', metavar='FILE')

    opts = parser.parse_args()

    # opts.path, opts.filename = path.split(path.abspath(path.expanduser(opts.file)))
    opts.path, opts.filename = path.split(path.expanduser(opts.pattern))

    return opts


opts = parse_args()
print(opts)

SUN_SIZE = 45
SUN_STRENGTH = 15

bpy.ops.object.select_all(action='DESELECT')

try:
    # select the default cube
    cube = bpy.data.objects['Cube']
    cube.select_set(True)

    # delete it
    bpy.ops.object.delete()
except KeyError:
    pass

scene = bpy.data.scenes['Scene']

scene.render.engine = 'CYCLES'
scene.cycles.feature_set = 'EXPERIMENTAL'
scene.cycles.samples = opts.render_samples
scene.cycles.tile_size = opts.render_tile_size

# TODO: add more planes with the other tiles
height, width, crs, transform = plane(0, 0, opts.lat, opts.lon, opts)

# The Camera
camera = bpy.data.objects['Camera']
camera.location = (0, 0, 5)  # z is not that important
camera.rotation_euler = (0, 0, 0)

scene.render.resolution_x = width
scene.render.resolution_y = height

camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2 * max((width, height)) / 1000

# The Sun
sun = bpy.data.objects['Light']
sun.data.type = 'SUN'

# bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
# sun = bpy.data.objects['Sun']

sun.data.energy = SUN_STRENGTH
sun.rotation_euler = (0, radians(45), radians(135))
sun.data.angle = radians(SUN_SIZE)

# Render
scene.render.image_settings.file_format = 'TIFF'
scene.render.image_settings.color_mode = 'BW'

filename = opts.filename.format(lat=opts.lat, lon=opts.lon)
basename = path.splitext(filename)[0]
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
