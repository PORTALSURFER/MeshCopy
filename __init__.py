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
                edge_seq = tuple(bm.verts[i.index+bm_verts_amount]
                                 for i in edge.verts)
                try:
                    add_edge(edge_seq)
                except ValueError:
                    # edge exists!
                    pass
            bm.edges.index_update()

    if normal_update:
        host_bmesh.normal_update()

    return host_bmesh


def join_meshes(source, target):
    # Get a BMesh representation
    target_bmesh = bmesh.new()   # create an empty BMesh
    source_bmesh = bmesh.new()

    target_bmesh.from_mesh(target.data)
    source_bmesh.from_mesh(source.data)

    mesh_list = [target_bmesh, source_bmesh]
    joined_mesh = bmesh_join(mesh_list)

    joined_mesh.to_mesh(target.data)
    # target_bmesh.free()

    target.data.update()

    return

    wmx = source.matrix_world

    vertices_in_source = len(source_bmesh.verts)

    for vertex in source_bmesh.verts:
        target_bmesh.verts.new(
            (vertex.co + source.location - target.location) @ wmx)

    target_bmesh.to_mesh(target.data)
    target_bmesh.free()

    target.data.update()


class MCPY_OT_copy_mesh_to_active(bpy.types.Operator):
    """Copies selected mesh to active"""
    bl_idname = "mcpy.copy_mesh_to_active"
    bl_label = "Copy Mesh to Active"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.active_object
        # print("TARGET: " + target.name)
        source = None
        for obj in context.selected_objects:
            if obj is not target:
                source = obj

        target_bmesh = bmesh.new()   # create an empty BMesh
        source_bmesh = bmesh.new()
        # print("SOURCE: " + source.name)

        join_meshes(source, target)
        # changer(context.active_object)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MCPY_OT_copy_mesh_to_active)


def unregister():
    bpy.utils.unregister_class(MCPY_OT_copy_mesh_to_active)
