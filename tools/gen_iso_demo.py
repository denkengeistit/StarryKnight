#!/usr/bin/env python3
"""Write tools/iso_demo.tmx, the small demo isometric map (14x30, strip_width 2 -> 7 strips)."""
import os
W, H = 14, 30
ground = [[1] * W for _ in range(H)]
walls = [[0] * W for _ in range(H)]
steps = [[0] * W for _ in range(H)]
for x in range(W):
    for y in (10, 11):                 # pit crossing every strip, except...
        if x not in (4, 5, 10, 11):    # ...bridged in strips 3 and 6
            ground[y][x] = 0
for x in range(W):
    for y in (22, 23):                 # a raised block on every strip
        walls[y][x] = 1
    if x % 4 < 2:
        steps[22][x] = 1               # taller on alternate strips
        steps[23][x] = 1
def csv(g): return ",\n".join(",".join(str(v) for v in r) for r in g)
def layer(i, name, e, g):
    return (f' <layer id="{i}" name="{name}" width="{W}" height="{H}">\n'
            f'  <properties><property name="elevation" type="int" value="{e}"/></properties>\n'
            f'  <data encoding="csv">\n{csv(g)}\n</data>\n </layer>\n')
def obj(i, cls, tx, ty, extra=""):
    return f'  <object id="{i}" class="{cls}" x="{tx * 32}" y="{ty * 32}">{extra}</object>\n'
lvl = '<properties><property name="lvl" type="int" value="2"/></properties>'
objs = [obj(1, "spawn", 6, 27)]
oid = 2
for sx in (1, 5, 9, 13):               # strips 1,3,5,7
    objs.append(obj(oid, "skeleton", sx, 16, lvl)); oid += 1
for sx in (3, 7, 11):
    objs.append(obj(oid, "xp", sx, 6)); oid += 1
    objs.append(obj(oid, "heal", sx, 25)); oid += 1
out = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<map version="1.10" orientation="isometric" renderorder="right-down" width="{W}" height="{H}" tilewidth="64" tileheight="32" infinite="0">\n'
       ' <properties><property name="strip_width" type="int" value="2"/></properties>\n'
       + layer(1, "ground", 0, ground) + layer(2, "walls", 1, walls) + layer(3, "steps", 2, steps)
       + ' <objectgroup id="4" name="objects">\n' + "".join(objs) + ' </objectgroup>\n</map>\n')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "iso_demo.tmx"), "w").write(out)
