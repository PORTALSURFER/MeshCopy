# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import bmesh
import mathutils

bl_info = {
    "name": "MeshCopy",
    "author": "PORTALSURFER",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}


def bmesh_join(list_of_bmeshes, normal_update=False):
    """ takes as input a list of bm references and outputs a single merged bmesh
    allows an additional 'normal_update=True' to force _normal_ calculations.
    """
    # create a bmesh host object
    host_bmesh = bmesh.new()

    # function pointers
    add_vert = host_bmesh.verts.new
    add_face = host_bmesh.faces.new
    add_edge = host_bmesh.edges.new

    # look through all bmeshes to join
    for bm_to_add in list_of_bmeshes:

        # get the amount of vertices in the bmesh currently being looked at
        host_bmesh_verts_amount = len(host_bmesh.verts)

        # add vertices of the current bmesh to the host object
        for vertex in bm_to_add.verts:
            # adds vert to the host and sets the coordinates
            add_vert(vertex.co)

        # Initialize the index values of this sequence.
        # This is the equivalent of looping over all elements and assigning the index values.
        host_bmesh.verts.index_update()

        # Ensure internal data needed for int subscription is initialized with verts/edges/faces, eg bm.verts[index].
        # This needs to be called again after adding/removing data in this sequence.
        host_bmesh.verts.ensure_lookup_table()

        # if the source object has faces
        if bm_to_add.faces:
            # look at all the faces
            for face in bm_to_add.faces:
                # add a new face to the host mesh
                # using a tuple of
                # every vert in the host mesh
                # where the vert chosen is the index added by the amount of vertices in the host mesh, which will grow every time a new mesh is added
                # the index is taken from each vertex in the source face, which would assume they are the same

                new_face = add_face(tuple(host_bmesh.verts[i.index+host_bmesh_verts_amount]
                                          for i in face.verts))

                new_face.material_index = face.material_index
            host_bmesh.faces.index_update()

        if bm_to_add.edges:
            for edge in bm_to_add.edges:
                edge_seq = tuple(host_bmesh.verts[i.index+host_bmesh_verts_amount]
                                 for i in edge.verts)
                try:
                    add_edge(edge_seq)
                except ValueError:
                    # edge exists!
                    pass
            host_bmesh.edges.index_update()

    if normal_update:
        host_bmesh.normal_update()

    return host_bmesh


def join_meshes(source_mesh, target_mesh, remap_material_index_table, source_wmx, target_offset, source_offset):

    # create a new bmesh to modify,
    # this will hold all the new bmesh data resulting in the final joined mesh
    host_bmesh = bmesh.new()

    # function pointers, for the lazy
    add_vert = host_bmesh.verts.new
    add_face = host_bmesh.faces.new
    add_edge = host_bmesh.edges.new

    # add mesh data from the original 'target' mesh data-block to the host_bmesh
    # add vertices of the current bmesh to the host object
    host_bmesh.from_mesh(target_mesh)

    # create a bmesh from the source mesh, used to look at the data which makes up this mesh
    source_bmesh = bmesh.new()
    source_bmesh.from_mesh(source_mesh)

    # get the amount of vertices in the bmesh currently being looked at, this is needed to append mesh data if mesh already exists.
    host_bmesh_verts_amount = len(host_bmesh.verts)

    ### VERTEX ###
    # add vertices from the source mesh
    for vertex in source_bmesh.verts:
        # adds vert to the host and sets the coordinates
        add_vert((vertex.co + source_offset - target_offset) @ source_wmx)

    # Initialize the index values of this sequence.
    # This is the equivalent of looping over all elements and assigning the index values.
    host_bmesh.verts.index_update()

    # Ensure internal data needed for int subscription is initialized with verts/edges/faces, eg bm.verts[index].
    # This needs to be called again after adding/removing data in this sequence.
    host_bmesh.verts.ensure_lookup_table()

    # TODO, this grabs the very first uv layer, need to add support for multiple UV layers
    uv_layer = host_bmesh.loops.layers.uv[0]
    source_uv_layer = source_bmesh.loops.layers.uv[0]
    print(uv_layer)

    ### FACES ###
    # look at all the faces
    for face in source_bmesh.faces:
        # add a new face to the host mesh
        # using a tuple of
        # every vert in the host mesh
        # where the vert chosen is the index added by the amount of vertices in the host mesh, which will grow every time a new mesh is added
        # the index is taken from each vertex in the source face, which would assume they are the same

        new_face = add_face(tuple(host_bmesh.verts[i.index+host_bmesh_verts_amount]
                                  for i in face.verts))

        # reassing material index
        for remap_index in remap_material_index_table:
            if remap_index[0] == face.material_index:
                new_face.material_index = remap_index[1]

        # print("NEW - " + str(new_loop[uv_layer].uv))
        #     print("OLD - " + str(face.loops[i][source_uv_layer].uv))

        for i, new_loop in enumerate(new_face.loops):
            new_loop[uv_layer].uv = face.loops[i][source_uv_layer].uv
            # for loop in face.loops:
            #     print(loop)
            #     print(loop[uv_layer].uv)

            # new_face.loops

            # for i, loop in enumerate(face.loops):

    host_bmesh.faces.index_update()
    host_bmesh.faces.ensure_lookup_table()

    ### EDGES ###
    for edge in source_bmesh.edges:
        edge_seq = tuple(host_bmesh.verts[i.index+host_bmesh_verts_amount]
                         for i in edge.verts)
        try:
            add_edge(edge_seq)
        except ValueError:
            # edge exists!
            pass
    host_bmesh.edges.index_update()
    host_bmesh.edges.ensure_lookup_table()

    ### custom data ###
    print(source_bmesh.loops.layers.uv.keys())
    print(source_bmesh.loops.layers.uv['UVMap'])

    # for layprint(face)er in enumerate(source_bmesh.loops.layers):
    # TODO uv_list is a list of uv tuples? need to grab this from the source mesh
    # loop[uv_layer].uv = uv_list[i]
    # print(uv)
    # uv = loop[uv_layer].uv

    # if normal_update:
    host_bmesh.normal_update()

    # put the bmesh data back into the target mesh block
    host_bmesh.to_mesh(target_mesh)
    host_bmesh.free()

    # update the mesh, so it will redraw
    target_mesh.update()


def join_objects(source, target):
    """
    joins a copy of the source object mesh with the target object mesh
    """

    remap_material_index_table = copy_materials(source, target)

    join_meshes(source.data, target.data,
                remap_material_index_table, source.matrix_world, target.location, source.location)

    bpy.data.objects.remove(source)


def simple_join(source, target):
    """
    Very simple joins function.
    Joins a copy of the source object's mesh with the target mesh. 
    Does not transfer CustomData etc.
    """
    target_bmesh = bmesh.new()

    target_bmesh.from_mesh(target.data)
    target_bmesh.from_mesh(source.data)

    target_bmesh.to_mesh(target.data)
    target_bmesh.free()

    target.data.update()


def copy_materials(source_object, target_object):
    """
    adds slots and links materials from one object to another
    """
    source_object_materials_count = len(source_object.data.materials)
    targetobject_materials_count = len(target_object.data.materials)

    # list of tuples for remapping, source index, new index on target
    remap_index_table = []

    for material_index in range(source_object_materials_count):
        current_source_material = None
        current_target_material = None

        if source_object.data.materials[material_index]:
            print("source.ID - " + str(material_index) + " : " +
                  source_object.data.materials[material_index].name)
            current_source_material = source_object.data.materials[material_index]

        else:
            print("source.ID - " + str(material_index) + " : " +
                  "NONE")

        if material_index < targetobject_materials_count:
            if target_object.data.materials[material_index]:
                print("target.ID - " + str(material_index) + " : " +
                      target_object.data.materials[material_index].name)
                current_target_material = target_object.data.materials[material_index]
            else:
                print("target.ID - " + str(material_index) + " : " +
                      "NONE")

        if current_source_material:
            if current_source_material:
                # both are not none
                if current_source_material != current_target_material:
                    # and they are not the same
                    # append the source to the end of target
                    target_object.data.materials.append(
                        source_object.data.materials[material_index])
                    remap_index_table.append(
                        (material_index, len(target_object.data.materials) - 1))

    for remap in remap_index_table:
        # print(remap)
        print("original index : " +
              str(remap[0]) + " - new index : " + str(remap[1]))

    return remap_index_table


class MCPY_OT_copy_mesh_to_active(bpy.types.Operator):
    """Copies selected mesh to active"""
    bl_idname = "mcpy.copy_mesh_to_active"
    bl_label = "Copy Mesh to Active"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.active_object
        # print("TARGET: " + target.name)
        source_objects = []

        for obj in context.selected_objects:
            if obj is not target:
                source_objects.append(obj)

        for source in source_objects:
            join_objects(source, target)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MCPY_OT_copy_mesh_to_active)


def unregister():
    bpy.utils.unregister_class(MCPY_OT_copy_mesh_to_active)
