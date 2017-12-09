import bmesh
from bpy import context


def randowDeselect():
    i = 0
    mesh=bmesh.from_edit_mesh(bpy.context.object.data)
    for v in mesh.verts:
        if v.select:
             v.select = (i % 2 == 0)
             i = i+1
    bpy.context.scene.objects.active = bpy.context.scene.objects.active

def alignMaxZ():
    i = 0
    mesh=bmesh.from_edit_mesh(bpy.context.object.data)
    max = -10000000000000;
    for v in mesh.verts:
        if v.select and v.co.z > max:
            max = v.co.z
    for v in mesh.verts:
        if v.select:
            v.co.z = max
    bpy.context.scene.objects.active = bpy.context.scene.objects.active


def alignZ(z):
    me = bpy.context.object.data
    bm = bmesh.from_edit_mesh(me)
    for v in bm.verts:
        if v.select:
            v.co.z = z
    bmesh.update_edit_mesh(me, True, False)

def copyWeights():
    src = bpy.context.selected_objects[0];
    dst = bpy.context.active_object;
    for i1 in range(0, len(src.vertex_groups.items())):
        src.vertex_groups.active_index = i1;
        for i2 in range(0, len(dst.vertex_groups.items())):
            dst.vertex_groups.active_index = i2;
            if dst.vertex_groups.active.name == src.vertex_groups.active.name:
                bpy.ops.object.data_transfer(use_reverse_transfer=True, data_type='VGROUP_WEIGHTS')


def adjustBones():
    for bone in bpy.context.selected_bones:
        bone.parent.tail = bone.head

    
class Group:
    scale = 1.0
    groupPrefix = ""
    groupRoot = ""
    edit = False;
    def __init__(self, scale, groupPrefix, groupRoot):
        self.scale = scale
        self.groupPrefix = groupPrefix
        self.groupRoot = groupRoot
        self.edit = bpy.data.objects[self.groupRoot].dimensions.z > 2.0
    def scaleGroup(self, prefix, scale):
        for obj in bpy.data.objects:
            obj.select = obj.name.startswith(prefix)
        bpy.ops.transform.resize(value=(scale, scale, scale), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False)
    def moveToZero(self):
        root = bpy.data.objects[self.groupRoot]
        loc = root.location
        for obj in bpy.data.objects:
            if obj.name.startswith(self.groupPrefix) and obj.name != self.groupRoot:
                obj.location -= loc
        root.location -= loc
    def scaleForEdit(self, prefix):
        self.scaleGroup(prefix, self.scale)
    def scaleForExport(self, prefix):
        self.scaleGroup(prefix, 1.0 / self.scale)
    def prepareForEdit(self):
        if self.edit:
            return
        self.scaleForEdit(self.groupPrefix)
        self.moveToZero()
        self.edit = True
        self.flipNormals()
    def prepareForExport(self):
        if not self.edit:
            return
        self.scaleForExport(self.groupPrefix)
        self.moveToZero()
        self.edit = False
        self.flipNormals()
    def flipNormals(self):
        for obj in bpy.data.objects:
            if obj.name.startswith(self.groupPrefix) and obj.name != self.groupRoot:
                obj.data.flip_normals()

def updateMesh(): 
    bpy.context.scene.objects.active = bpy.context.scene.objects.active

pred = lambda src, ch : src.co.y < ch.co.y

def mergeLoop(pred):
    mesh = bmesh.from_edit_mesh(context.active_object.data);
    src = [v for v in mesh.verts if v.select]
    for v in src:
        v.select = False
    for src_v in src:
        src_v.select = True
        edges = [e for e in mesh.edges if src_v in e.verts]
        verts = []
        for e in edges:
            for v in e.verts:
                if v not in src:
                    verts.append(v)
        max_v = verts[0]
        for v in verts[1:]:
            if pred(v, max_v):
                max_v = v
        max_v.select = True
        bpy.ops.mesh.merge(type='CENTER')
        mesh = bmesh.from_edit_mesh(context.active_object.data);
        for v in mesh.verts:
            v.select = False
    updateMesh()

def tendEdges():
    mesh = bmesh.from_edit_mesh(context.active_object.data);
    for v in mesh.verts:
        v.select = False
        edges = []
        for e in mesh.edges:
            if v in e.verts:
                edges.append(e)
        if len(edges) < 3 and len(edges) > 0:
            for vert in edges[0].verts:
                if vert != v:
                    v.select = True
                    vert.select = True
                    bpy.ops.mesh.merge(type='CENTER')
                    tendEdges()
                    break
y = None
for v in mesh.verts:
    if v.select:
        y = v


#delete 
objs = [o for o in bpy.data.objects if o.name.startswith("l")]
for obj in objs:
    obj.select = True;

bpy.ops.object.delete(use_global = False)



#merge
objs = [o for o in bpy.data.objects if o.select]


for obj in bpy.data.objects:
    if obj.name.startswith("r"):
        bpy.ops.object.delete(use_global = False)


    

def getMiddleVertex():
    mesh = bmesh.from_edit_mesh(context.active_object.data)
    vlist = [v for v in mesh.verts if v.select]
    x = 0.0
    y = 0.0
    z = 0.0
    for v in vlist:
        x += v.co.x
        y += v.co.y
        z += v.co.z
    l = len(vlist)
    r = [x / l, y / l, z / l]
    print ('x: {}; y: {}; z: {}'.format(r[0], r[1], r[2]))
    return r

mesh = bmesh.from_edit_mesh(context.active_object.data)
data = createVolume(0.004)

def createVolume(width = 0.1, oneSided = False):
    newFaces = []
    mesh = bmesh.from_edit_mesh(context.active_object.data)
    flist = [f for f in mesh.faces if f.select]
    normalMap = {}
    for f in flist:
        for v in f.verts:
            l = normalMap.setdefault(v, [])
            l.append(f.normal)
    flatMap = {}
    for v, nlist in normalMap.items():
        n = Vector([0, 0, 0])
        for vec in nlist:
            n += vec.normalized()
        n = n / len(nlist)
        flatMap.setdefault(v, n.normalized().freeze())
    newVerts = []
    count = 0
    vertMap = {}
    for v, n in flatMap.items():
        mesh.verts.new((v.co.x - n.x * width , v.co.y - n.y* width, v.co.z - n.z * width))
        count += 1
    mesh.verts.ensure_lookup_table()
    c = 0
    for v, n in flatMap.items():
        vertMap.setdefault(v, mesh.verts[-count + c])
        c += 1
    #create faces
    for f in flist:
        l = []
        for v in f.verts:
            l.append(vertMap.get(v))
        newFaces.append(mesh.faces.new(l))
    if oneSided:
        return
    #find area edges
    edgeCountMap = {}
    for f in flist:
        for e in f.edges:
            c = edgeCountMap.setdefault(e, 0)
            edgeCountMap[e] = c + 1
    for edge, count in edgeCountMap.items():
        if count == 1:
            list = []
            print('new edge')
            list.append(vertMap.get(edge.verts[1]))
            list.append(vertMap.get(edge.verts[0]))
            list.append(edge.verts[0])
            list.append(edge.verts[1])
            newFaces.append(mesh.faces.new(list))
    for f in mesh.faces:
        f.select = False
    for f in newFaces:
        f.select = True
    bpy.ops.mesh.flip_normals()

def moveByNormal(dist = 0.1):
    newFaces = []
    mesh = bmesh.from_edit_mesh(context.active_object.data)
    flist = [f for f in mesh.faces if f.select]
    normalMap = {}
    for f in flist:
        for v in f.verts:
            l = normalMap.setdefault(v, [])
            l.append(f.normal)
    flatMap = {}
    for v, nlist in normalMap.items():
        n = Vector([0, 0, 0])
        for vec in nlist:
            n += vec.normalized()
        n = n / len(nlist)
        flatMap.setdefault(v, n.normalized().freeze())
    moved = set();
    for f in flist:
        for v in f.verts:
            if not v in moved:
                n = flatMap[v]
                v.co.x -= n.x * dist
                v.co.y -= n.y * dist
                v.co.z -= n.z * dist
                moved.add(v)

def createVolumeEdge(map)
    edges = [e for e in mesh.edges if e.select]
    for e in edges:
        list = []
        list.append(e.verts[0])
        list.append(e.verts[1])
        list.append(map.get(e.verts[1]))
        list.append(map.get(e.verts[0]))
        mesh.faces.new(list)

bpy.ops.mesh.knife_tool(use_occlude_geometry=True, only_selected=False)

for i in range(0, len(f.verts)):
    v = f.verts[i]
    for j in range(i + 1, len(f.verts)):
        bmesh.utils.face_split(f, f.verts[i], f.verts[j], [], True)