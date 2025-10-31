import maya.cmds as cmds
import random

# ---------------------- bounding box helper ----------------------
def getBoundingBoxOffset(obj):
    """Return Y-offset based on bounding box height"""
    bbox = cmds.exactWorldBoundingBox(obj)
    height = bbox[4] - bbox[1]
    return [0, height * 0.5, 0]

# ---------------------- random point on face ----------------------
def randomPointOnFace(face):
    """Return a random point inside a polygon face"""
    verts = cmds.polyListComponentConversion(face, toVertex=True)
    verts = cmds.ls(verts, fl=True)
    if len(verts) < 3:
        return cmds.pointPosition(verts[0], w=True)
    p1 = cmds.pointPosition(verts[0], w=True)
    p2 = cmds.pointPosition(verts[1], w=True)
    p3 = cmds.pointPosition(verts[2], w=True)
    r1, r2 = random.random(), random.random()
    if r1 + r2 > 1:
        r1, r2 = 1 - r1, 1 - r2
    r3 = 1 - r1 - r2
    return [p1[0]*r1 + p2[0]*r2 + p3[0]*r3,
            p1[1]*r1 + p2[1]*r2 + p3[1]*r3,
            p1[2]*r1 + p2[2]*r2 + p3[2]*r3]

# ---------------------- scatter ----------------------
def scatterObjects(target, sources, num=10, scatterMode="Vertex",
                   alignNormal=True, useBoundingBox=True,
                   rotRange=((0, 360), (0, 360), (0, 360)), scaleRange=(1,1),
                   parentName=None):
    """Main scatter function (returns list of created objects)"""
    if not cmds.objExists(target):
        cmds.warning("Target geometry not found.")
        return []

    if not sources:
        cmds.warning("No source objects to scatter.")
        return []

    if not parentName:
        parentName = "_GeoScatter_" + target.replace("|", "_")

    if not cmds.objExists(parentName):
        parentGroup = cmds.group(empty=True, name=parentName)
    else:
        parentGroup = parentName

    verts = cmds.ls(target + ".vtx[*]", fl=True)
    faces = cmds.ls(target + ".f[*]", fl=True)
    created = []

    cmds.progressWindow(title="Geo Scatter Pro", progress=0, maxValue=num,
                        status='Scattering...', isInterruptable=True)

    try:
        for i in range(num):
            if cmds.progressWindow(query=True, isCancelled=True):
                break

            if scatterMode == "Vertex":
                v = random.choice(verts)
                pos = cmds.pointPosition(v, w=True)
                normal = cmds.polyNormalPerVertex(v, query=True, xyz=True)[:3]
            else:
                f = random.choice(faces)
                pos = randomPointOnFace(f)
                vert_ids = cmds.polyListComponentConversion(f, toVertex=True)
                vert_ids = cmds.ls(vert_ids, fl=True)
                normals = [cmds.polyNormalPerVertex(v, query=True, xyz=True)[:3] for v in vert_ids]
                normal = [sum([n[j] for n in normals])/len(normals) for j in range(3)]

            dup = cmds.duplicate(random.choice(sources), rr=True)[0]
            cmds.xform(dup, ws=True, t=pos)

            if useBoundingBox:
                offset = getBoundingBoxOffset(dup)
                cmds.move(offset[0], offset[1], offset[2], dup, relative=True, objectSpace=True)

            if alignNormal:
                tempAim = cmds.aimConstraint(target, dup, aimVector=(0, 1, 0),
                                             upVector=(0, 0, 1),
                                             worldUpType="vector",
                                             worldUpVector=(normal[0], normal[1], normal[2]))
                cmds.delete(tempAim)

            rx = random.uniform(rotRange[0][0], rotRange[0][1])
            ry = random.uniform(rotRange[1][0], rotRange[1][1])
            rz = random.uniform(rotRange[2][0], rotRange[2][1])
            cmds.rotate(rx, ry, rz, dup, relative=True, objectSpace=True)

            s = random.uniform(scaleRange[0], scaleRange[1])
            cmds.scale(s, s, s, dup)

            cmds.parent(dup, parentGroup)
            created.append(dup)
            cmds.progressWindow(edit=True, step=1)

    finally:
        if cmds.progressWindow(query=True, exists=True):
            cmds.progressWindow(endProgress=True)

    return created

# ---------------------- clear scatter ----------------------
def clearScatter(scatteredObjects, parentName=""):
    """Delete scattered objects and parent group"""
    removed = 0
    for obj in scatteredObjects:
        if cmds.objExists(obj):
            try:
                cmds.delete(obj)
                removed += 1
            except:
                pass

    if parentName and cmds.objExists(parentName):
        try:
            cmds.delete(parentName)
            removed += 1
        except:
            pass

    return removed
