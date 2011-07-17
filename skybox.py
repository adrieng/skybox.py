#!/usr/bin/env python
# Copyright (c) 2011 Adrien Guatto <adrien@ludics.eu>
# Licensed under the MIT License, see COPYING in top-level directory

from PIL import Image, ImageColor
import sys
import os

if len(sys.argv) == 1:
    print("Usage: %s FILE" % sys.argv[0])
    exit(1)

dest = sys.argv[1]
(basename, ext) = os.path.splitext(dest)

# Load each face

print("Loading faces")

east = 0
west = 1
south = 2
north = 3
up = 4
down = 5

suffixes = ["east", "west", "south", "north", "up", "down"]
faces = [Image.open(basename + "_" + suffix + ext).convert('RGB')
         for suffix in suffixes]

# Check that they all have the same dimensions

(w, h) = faces[0].size
mode = faces[0].mode

if w != h:
    print("The faces should be square")
    exit(1)

for img in faces:
    if img.mode != mode:
        print("All the faces should have the same mode, here %s" % mode)
        exit(1)
    if img.size != (w, h):
        print("All the faces should have the same dimensions.")
        exit(1)

print("Face dimensions: %dx%d" % (w, h))

# Rotate the faces according to their position in the skybox
#    W
#  S B N U
#    E

print("Rotating faces")

# East
faces[ east] = faces[ east].transpose(Image.ROTATE_180)
# South
faces[south] = faces[south].transpose(Image.ROTATE_90)
# North
faces[north] = faces[north].transpose(Image.ROTATE_270)
# Up
faces[   up] = faces[   up].transpose(Image.ROTATE_270)
# Down
faces[ down] = faces[ down].transpose(Image.ROTATE_270)



# Fix borders to hide visible seams

print("Fixing borders")

left = 0
right = 1

def copy_edge(dest, dest_edge, src, src_edge, traversal):
    if(dest_edge == left):
        (de, dx) = (0,     0)
    elif(dest_edge == right):
        (de, dx) = (0, h + 1)
    elif(dest_edge == up):
        (de, dx) = (1,     0)
    elif(dest_edge == down):
        (de, dx) = (1, w + 1)

    if(src_edge == left):
        (se, sx) = (0,     0)
    elif(src_edge == right):
        (se, sx) = (0, h - 1)
    elif(src_edge == up):
        (se, sx) = (1,     0)
    elif(src_edge == down):
        (se, sx) = (1, w - 1)

    newpix = dest.load()
    pix = src.load()

    for i in range(0, w):
        dest_x = (1 - de) * dx + de * (1 + i)
        dest_y = de * dx + (1 - de) * (1 + i)
        src_x = (1 - se) * sx + se * \
            (traversal * (w - 1 - i) + (1 - traversal) * i)
        src_y = se * sx + (1 - se) * \
            (traversal * (h - 1 - i) + (1 - traversal) * i)
        newpix[dest_x, dest_y] = pix[src_x, src_y]

newfaces = [Image.new('RGB', (w + 2, h + 2)) for i in range(0, 6)]

for i in range(0, 6):
    newfaces[i].paste(faces[i], (1, 1))

# East: South / North / Down / Up

copy_edge(newfaces[east],  left, faces[south], down, 1)
copy_edge(newfaces[east], right, faces[north], down, 0)
copy_edge(newfaces[east],    up, faces[ down], down, 0)
copy_edge(newfaces[east],  down, faces[   up], down, 0)

# West: South / North / Up / Down

copy_edge(newfaces[west], left,  faces[south], up, 0)
copy_edge(newfaces[west], right, faces[north], up, 1)
copy_edge(newfaces[west], up,    faces[   up], up, 1)
copy_edge(newfaces[west], down,  faces[ down], up, 0)

# South: Up / Down / West / East

copy_edge(newfaces[south], left,  faces[  up], right, 0)
copy_edge(newfaces[south], right, faces[down],  left, 0)
copy_edge(newfaces[south], up,    faces[west],  left, 0)
copy_edge(newfaces[south], down,  faces[east],  left, 1)

# North: Down / Up / West / East

copy_edge(newfaces[north], left,  faces[down], right, 0)
copy_edge(newfaces[north], right, faces[  up],  left, 0)
copy_edge(newfaces[north], up,    faces[west], right, 1)
copy_edge(newfaces[north], down,  faces[east], right, 0)

# Up: North / South / West / East

copy_edge(newfaces[up], left,  faces[north], right, 0)
copy_edge(newfaces[up], right, faces[south],  left, 0)
copy_edge(newfaces[up], up,    faces[ west],    up, 1)
copy_edge(newfaces[up], down,  faces[ east],  down, 0)

# Down: South / North / West / East

copy_edge(newfaces[down], left,  faces[south], right, 0)
copy_edge(newfaces[down], right, faces[north],  left, 0)
copy_edge(newfaces[down], up,    faces[ west],  down, 0)
copy_edge(newfaces[down], down,  faces[ east],    up, 0)

faces = newfaces
w = w + 2
h = h + 2

# Stitch the faces together in the skybox
# Final dimensions: 4 * width x 3 * height

print("Stitching everything together")

skybox = Image.new('RGB', (4 * w, 3 * h))

# East
skybox.paste(faces[east], (w, 2 * h, 2 * w, 3 * h))
# West
skybox.paste(faces[west], (w, 0, 2 * w, h))
# South
skybox.paste(faces[south], (0, h, w, 2 * h))
# North
skybox.paste(faces[north], (2 * w, h, 3 * w, 2 * h))
# Up
skybox.paste(faces[up], (3 * w, h, 4 * w, 2 * h))
# Down
skybox.paste(faces[down], (w, h, 2 * w, 2 * h))

# Save into the file specified via the command-line
skybox.save(dest)

# Printing OBJ file

obj = open(basename + ".obj", "w")

obj.write("mtllib " + basename + ".mtl\n")
obj.write("o Skybox\n")
obj.write("usemtl Sky\n")

for i in [1, -1]:
    for j in [1, -1]:
        for k in [1, -1]:
            obj.write("v %d %d %d\n" % (i, j, k))

# UV coordinates:
#
#               1/4,3/3       2/4,3/3
#
#                         W
#
# 0/4,2/3       1/4,2/3       2/4,2/3       3/4,2/3       4/4,2/3
#
#          S              B             N             U
#
# 0/4,1/3       1/4,1/3       2/4,1/3       3/4,1/3       4/4,1/3
#
#                         E
#
#               1/4,0/3       2/4,0/3

# CCW orientation
uv_coords = [
    # W
    (2./4., 3./3.),
    (1./4., 3./3.),
    (1./4., 2./3.),
    (2./4., 2./3.),
    # S
    (1./4., 2./3.),
    (0./4., 2./3.),
    (0./4., 1./3.),
    (1./4., 1./3.),
    # B
    (2./4., 2./3.),
    (1./4., 2./3.),
    (1./4., 1./3.),
    (2./4., 1./3.),
    # N
    (3./4., 2./3.),
    (2./4., 2./3.),
    (2./4., 1./3.),
    (3./4., 1./3.),
    # U
    (4./4., 2./3.),
    (3./4., 2./3.),
    (3./4., 1./3.),
    (4./4., 1./3.),
    # E
    (2./4., 1./3.),
    (1./4., 1./3.),
    (1./4., 0./3.),
    (2./4., 0./3.),
    ]

# Fix the UV coordinates for leaving out the border
du = 1. / (4 * w)
dt = 1. / (3 * h)
for i in range(0, 6):
    uv_coords[i * 4 + 0] = (uv_coords[i * 4 + 0][0] - du,
                            uv_coords[i * 4 + 0][1] - dt)
    uv_coords[i * 4 + 1] = (uv_coords[i * 4 + 1][0] + du,
                            uv_coords[i * 4 + 1][1] - dt)
    uv_coords[i * 4 + 2] = (uv_coords[i * 4 + 2][0] + du,
                            uv_coords[i * 4 + 2][1] + dt)
    uv_coords[i * 4 + 3] = (uv_coords[i * 4 + 3][0] - du,
                            uv_coords[i * 4 + 3][1] + dt)

for (u, v) in uv_coords:
    obj.write("vt %f %f\n" % (u, v))

# UV coordinates:
#
#            LUB/5      LUF/6
#
#
# LUB/5      LDB/7      LDF/8      LUF/6      LUB/5
#
#
# RUB/1      RDB/3      RDF/4      RUF/2      RUB/1
#
#
#            RUB/1      RUF/2
#
# where  pos |   coords   | idx in declarations
#        RUB |  1,  1,  1 | 1
#        RUF |  1,  1, -1 | 2
#        RDB |  1, -1,  1 | 3
#        RDF |  1, -1, -1 | 4
#        LUB | -1,  1,  1 | 5
#        LUF | -1,  1, -1 | 6
#        LDB | -1, -1,  1 | 7
#        LDF | -1, -1, -1 | 8

faces = [
    (6, 5, 7, 8),
    (7, 5, 1, 3),
    (8, 7, 3, 4),
    (6, 8, 4, 2),
    (5, 6, 2, 1),
    (4, 3, 1, 2)
    ]

j = 0
for face in faces:
    obj.write("f ");
    for i in range(0, 4):
        obj.write("%d/%d" % (face[i], 1 + j * 4 + i))
        if i != 3:
            obj.write(" ")
    j = j + 1
    obj.write("\n")

obj.close()

mtl = open(basename + ".mtl", "w")
mtl.write("newmtl Sky\n")
mtl.write("map_Ka " + sys.argv[1] + "\n")
mtl.write("map_Kd " + sys.argv[1] + "\n")
mtl.close()
