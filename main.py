# -*- coding: utf-8 -*-

# usage: python main.py
# e.g. python main.py
# to enable inline tests, python main.py --tests

IMAGE_SCALE  = 24

import math, random, sys

from classes import *
from hull import *

if sys.platform == "darwin":
    from PIL import Image
else:
    import Image

'''rendering code'''

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# http://www.de-brauwer.be/wiki/wikka.php?wakka=PyOpenGLSierpinski
window_id = -1

# a global variable used for debugging
# stores a list of point coordinate pairs
point_list = []

def draw_pixel_centre(x,y):
    # draw centre of each pixel
    global im
    w, h = im.size
    r, g, b = get_node(x, h-y-1, im).rgb
    glColor3ub(r, g, b)
    perturb = 0.075

    points = [(IMAGE_SCALE*(x+0.5-perturb), IMAGE_SCALE*(y+0.5-perturb)),
              (IMAGE_SCALE*(x+0.5-perturb), IMAGE_SCALE*(y+0.5+perturb)),
              (IMAGE_SCALE*(x+0.5+perturb), IMAGE_SCALE*(y+0.5+perturb)),
              (IMAGE_SCALE*(x+0.5+perturb), IMAGE_SCALE*(y+0.5-perturb))]

    # fill
    glBegin(GL_POLYGON)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()

    # stroke
    glColor3ub(255-r, 255-g, 255-b)
    glBegin(GL_LINE_LOOP)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()

def init_original():
    global w,h
    ww = w * IMAGE_SCALE
    hh = h * IMAGE_SCALE
    glClearColor(1.0, 1.0, 1.0, 0.0)
    glColor3f(0.0, 0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, ww, 0, hh)
    glPointSize(3)

def display_original():
    global im
    w, h = im.size
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    for x in xrange(w):
        for y in xrange(h):
            r, g, b = get_node(x, y, im).rgb
            y = h - y - 1
            glColor3ub(r, g, b)
            glBegin(GL_QUADS)
            glVertex2f(IMAGE_SCALE*x, IMAGE_SCALE*y)
            glVertex2f(IMAGE_SCALE*(x+1), IMAGE_SCALE*y)
            glVertex2f(IMAGE_SCALE*(x+1), IMAGE_SCALE*(y+1))
            glVertex2f(IMAGE_SCALE*x, IMAGE_SCALE*(y+1))
            glEnd()
    glFlush()

# note: exits program on mac
def keyboard_original(key, x, y):
    global window_id
    if key == chr(27):
        glutDestroyWindow(window_id)
        if sys.platform == "darwin":
            exit(0)

def display_voronoi():
    global im
    w, h = im.size
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    for x in xrange(w):
        for y in xrange(h):
            n = get_node(x, y, im)
            r, g, b = n.rgb
            glColor3ub(r, g, b)
            if '--lines' in sys.argv:
                glBegin(GL_LINE_LOOP)
            else:
                glBegin(GL_POLYGON)
            for pt in n.vor_pts:
                x_pt, y_pt = pt
                y_pt = h - y_pt
                glVertex2f(IMAGE_SCALE*x_pt, IMAGE_SCALE*y_pt)
            glEnd()
    if '--centres' in sys.argv:
        display_pixel_centres(w, h)
    display_point_list()
    glFlush()

def display_pixel_centres(w, h):
    for x in xrange(w):
        for y in xrange(h):
            draw_pixel_centre(x, h - y - 1)

def set_random_color():
    glColor3ub(random.randint(0,255), random.randint(0,255), random.randint(0,255))

def display_visible_edges():
    global im, vedges
    w, h = im.size
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    for v in vedges:
        set_random_color()
        glBegin(GL_LINE_STRIP)
        for p in v.points:
            x, y = p.get_xy()
            glVertex2f(IMAGE_SCALE*x, IMAGE_SCALE*(h-y))
        glEnd()
    if '--centres' in sys.argv:
        display_pixel_centres(w, h)
    display_point_list()
    glFlush()

def display_point_list():
    global point_list
    glColor3ub(0, 0, 255)
    glBegin(GL_POINTS)
    for p in point_list:
        x, y = p.get_xy()
        glVertex2f(IMAGE_SCALE*x, IMAGE_SCALE*(h-y))
    glEnd()

def display_similarity():
    global im
    w, h = im.size
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3ub(0, 0, 0)
    glBegin(GL_LINES)
    for x in xrange(w):
        for y in xrange(h):
            n = get_node(x, y, im)
            for ne in n.neighbours:
                nx, ny = n.get_xy()
                nex, ney = ne.get_xy()
                ny, ney = h-ny-1, h-ney-1
                glVertex2f(IMAGE_SCALE*(nx+0.5), IMAGE_SCALE*(ny+0.5))
                glVertex2f(IMAGE_SCALE*(nex+0.5), IMAGE_SCALE*(ney+0.5))
    glEnd()
    glFlush()

def display_bsplines():
    global im, vedges
    w, h = im.size
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3ub(0, 0, 0)
    for v in vedges:
        if v.bspline is None:
            continue
        set_random_color()
        glBegin(GL_LINE_STRIP)
        for x,y in v.bspline:
            y = h-y
            glVertex2f(IMAGE_SCALE*x, IMAGE_SCALE*y)
        glEnd()
    display_point_list()
    glFlush()

def display_optimized():
    pass

def render(render_stage):
    global window_id, im, imagename
    w, h = im.size
    glutInit()
    glutInitWindowSize(w * IMAGE_SCALE, h * IMAGE_SCALE)
    window_id = glutCreateWindow(render_stage + ' - '  + imagename)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    if render_stage == 'original':
        glutDisplayFunc(display_original)
    elif render_stage == 'similarity':
        glutDisplayFunc(display_similarity)
    elif render_stage == 'voronoi':
        glutDisplayFunc(display_voronoi)
    elif render_stage == 'vedges':
        glutDisplayFunc(display_visible_edges)
    elif render_stage == 'bsplines':
        glutDisplayFunc(display_bsplines)
    elif render_stage == 'optimized':
        glutDisplayFunc(display_optimized)
    else:
        glutDisplayFunc(display_original)
    glutKeyboardFunc(keyboard_original)
    init_original()
    glutMainLoop()

''' rendering over'''

def process_command_line_arg(argname, necessary=False, missing_error=''):
    if argname not in sys.argv:
        if necessary:
            sys.stderr.write(missing_error + '\n')
            exit(1)
        else:
            return None
    index = sys.argv.index(argname)
    if len(sys.argv) < index + 2:
        sys.stderr.write(argname + ' needs an argument\n')
        exit(1)
    return sys.argv[index+1]

imagename = process_command_line_arg('--image', True, 'need an image to convert')

im = Image.open(imagename)
w, h = im.size

nodes = []

# im = image object
def get_node(x, y, im):
    w, h = im.size
    if x < 0 or y < 0 or x >= w or y >= h:
        return None
    index = x + y * w
    return nodes[index]

# create nodes
for row in xrange(h):
    for col in xrange(w):
        n = Node(image=im, x=col, y=row, rgb=im.getpixel((col, row)))
        nodes.append(n)

# initialize similarity graph
for row in xrange(h):
    for col in xrange(w):
        n = get_node(col, row, im)
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                if x != 0 or y != 0:
                    neighbour = get_node(col+x, row+y, im)
                    n.make_conn(neighbour)

def test_node_corresponds_to_image(im):
    for x in xrange(col):
        for y in xrange(row):
            assert get_node(x,y,im).rgb == im.getpixel((x,y))

def test_neighbours_are_mutual(im):
    for x in xrange(col):
        for y in xrange(row):
            n = get_node(x,y,im)
            for ne in n.neighbours:
                assert n in ne.neighbours

def test_number_of_neighbours_is_correct(im):
    w, h = im.size
    # corner nodes have 3 neighbours
    assert len(get_node(0,   0,   im).neighbours) == 3
    assert len(get_node(w-1, 0,   im).neighbours) == 3
    assert len(get_node(0,   h-1, im).neighbours) == 3
    assert len(get_node(w-1, h-1, im).neighbours) == 3
    # border nodes have 5 neighbours
    for x in xrange(1, w-1):
        assert len(get_node(x, 0,   im).neighbours) == 5
        assert len(get_node(x, h-1, im).neighbours) == 5
    for y in xrange(1, h-1):
        assert len(get_node(0,   y, im).neighbours) == 5
        assert len(get_node(w-1, y, im).neighbours) == 5
    # interior nodes have 8 neighbours
    for x in xrange(1, w-1):
        for y in xrange(1, h-1):
            assert len(get_node(x, y, im).neighbours) == 8

if '--tests' in sys.argv:
    test_node_corresponds_to_image(im)
    test_number_of_neighbours_is_correct(im)
    test_neighbours_are_mutual(im)

'''colour comparisons'''

# convert rgb to yuv
def rgb2yuv(r,g,b):
    r1 = r / 255.0
    g1 = g / 255.0
    b1 = b / 255.0
    y = (0.299 * r1) + (0.587 * g1) + (0.114 * b1)
    u = 0.492 * (b1 - y)
    v = 0.877 * (r1 - y)
    return (y, u, v)

# compare YUV values of two pixels, return
# True if they are different, else False
def pixels_are_dissimilar(rgb1, rgb2):
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    y1, u1, v1 = rgb2yuv(r1, g1, b1)
    y2, u2, v2 = rgb2yuv(r2, g2, b2)
    ydiff = abs(y1 - y2) > 48.0/255
    udiff = abs(u1 - u2) > 7.0/255
    vdiff = abs(v1 - v2) > 6.0/255
    return ydiff or udiff or vdiff

def shading_edge(rgb1, rgb2):
    y1, u1, v1 = rgb2yuv(*rgb1)
    y2, u2, v2 = rgb2yuv(*rgb2)
    dist = (y1 - y2)**2 +(u1 - u2)**2 + (v1 - v2)**2
    return (dist <= (float(100)/255)**2)

'''comparisons over'''

# remove dissimilar edges by yuv metric
for x in xrange(w):
    for y in xrange(h):
        n = get_node(x, y, im)
        neighbours_to_remove = [ne for ne in n.neighbours if pixels_are_dissimilar(n.rgb, ne.rgb)]
        for ne in neighbours_to_remove:
            n.remove_conn(ne)

# to measure the curve length that a diagonal is part of
# start from one end of the diagonal and move away from its neighbour in the other direction
# measure the length of that curve. similarly, measure the length of the other curve
# then add the two half-curve lengths (plus 1) to get the length of the entire curve
def overall_curve_len(node1, node2):
    assert node1 in node2.neighbours
    assert node2 in node1.neighbours
    curve_len = int(half_curve_len(node1, node2) + half_curve_len(node2, node1) + 1)
    return curve_len

# node1 is the node we start exploring from
# node2 is the other node
def half_curve_len(node1, node2):
    assert node1 in node2.neighbours
    assert node2 in node1.neighbours
    # early exit - node1 does not have valence 2
    # so no point exploring further
    if len(node1.neighbours) != 2:
        return 0
    assert len(node1.neighbours) == 2
    current, previous = node1, node2
    # we store the nodes encountered thus far to detect cycles
    # otherwise, we would loop forever if we enter a cycle
    encountered = set([node2])
    result = 0
    while len(current.neighbours) == 2:
        # get the neighbours of the current pixel
        neighb1, neighb2 = current.neighbours
        # and update current and previous
        old_current_x, old_current_y = current.get_xy()
        if neighb1 == previous:
            current = neighb2
        else:
            current = neighb1
        previous = get_node(old_current_x, old_current_y, im)
        result += 1
        if current not in encountered:
            encountered.add(current)
        else:
            # cycle detected, divide by half to avoid double-counting
            result /= 2.0
            break
    return result

def largest_connected_components(topleft, topright, bottomleft, bottomright, window_edge_len, im):
    w, h = im.size
    half_window_minus_one = window_edge_len/2 - 1
    # any pixel we encounter should not exceed these bounds
    max_x = min(w-1, bottomright.x + half_window_minus_one)
    min_x = max(0,   topleft.x     - half_window_minus_one)
    max_y = min(h-1, bottomleft.y  + half_window_minus_one)
    min_y = max(0,   topleft.y     - half_window_minus_one)
    # use depth-first search
    component1_size = dfs_connected_component_size(topleft, max_x, min_x, max_y, min_y)
    component2_size = dfs_connected_component_size(topright, max_x, min_x, max_y, min_y)
    return component1_size, component2_size

def dfs_connected_component_size(node, max_x, min_x, max_y, min_y):
    encountered = set([node])
    stack = [node]
    while len(stack) > 0:
        current = stack.pop()
        for ne in current.neighbours:
            if ne not in encountered and min_x <= ne.x <= max_x and min_y <= ne.y <= max_y:
                encountered.add(ne)
                stack.append(ne)
    return len(encountered)

# apply heuristics to make graph planar
for x in xrange(w-1):
    for y in xrange(h-1):
        n = get_node(x, y, im)
        right = get_node(x+1, y, im) # node to the right of the curr node
        down = get_node(x, y+1, im) # node directly below the curr node
        rightdown = get_node(x+1, y+1, im) # node directly below and to the right of the curr node

        # edges
        self_to_right = right in n.neighbours
        self_to_down = down in n.neighbours
        right_to_rightdown = right in rightdown.neighbours
        down_to_rightdown = down in rightdown.neighbours
        # diagonals
        diag1 = rightdown in n.neighbours
        diag2 = down in right.neighbours

        # check if fully connected
        vert_and_horiz_edges = self_to_right and self_to_down and right_to_rightdown and down_to_rightdown
        no_vert_horiz_edges = not (self_to_right or self_to_down or right_to_rightdown or down_to_rightdown)
        both_diagonals = diag1 and diag2

        fully_connected = vert_and_horiz_edges and both_diagonals # all 6 connections are present
        only_diagonals = no_vert_horiz_edges and both_diagonals # only the diagonals are present

        # we increase this each time a heuristic votes to keep diagonal 1
        # and decrease this each time a heuristic votes to keep diagonal 2
        keep_diag1 = 0.0
        # at the end of the three heuristics, if it is > 0, we keep diagonal 2
        # and if it is < 0, we keep diagonal 2
        # no clue what we should do if it equals 0, though

        if fully_connected:
            n.remove_conn(rightdown)
            right.remove_conn(down)

        if only_diagonals:
            # curves heuristic
            # the longer curve should be kept
            diag1_curve_len = overall_curve_len(n, rightdown)
            diag2_curve_len = overall_curve_len(right, down)
            curve_len_difference = abs(diag1_curve_len - diag2_curve_len)
            if diag1_curve_len > diag2_curve_len:
                keep_diag1 += curve_len_difference
            else:
                keep_diag1 -= curve_len_difference
            # sparse pixels heuristic
            # for each diagonal, find the length of the largest connected component
            # while making sure that we stay within a window of, say, 8
            window_edge_len = 8
            component1_size, component2_size = largest_connected_components(n, right, down, rightdown, window_edge_len, im)
            component_size_difference = abs(component1_size - component2_size)
            if component1_size < component2_size:
                keep_diag1 += component_size_difference
            else:
                keep_diag1 -= component_size_difference
            # islands heuristic
            if (len(n.neighbours) == 1 or len(rightdown.neighbours) == 1) and \
                    len(right.neighbours) != 1 and len(down.neighbours) != 1:
                keep_diag1 += 5
            elif len(n.neighbours) != 1 and len(rightdown.neighbours) != 1 and \
                    (len(right.neighbours) == 1 or len(down.neighbours) == 1):
                keep_diag1 -= 5

            if keep_diag1 >= 0:
                right.remove_conn(down)
            else:
                n.remove_conn(rightdown)

# test that the graph is planar
def test_graph_is_planar(im, nodes):
    for x in xrange(w-1):
        for y in xrange(h-1):
            n = get_node(x, y, im)
            right = get_node(x+1, y, im)
            down = get_node(x, y+1, im)
            rightdown = get_node(x+1, y+1, im)
            # if n in rightdown.neighbours and right in down.neighbours:
            #     print n.get_xy()

if '--tests' in sys.argv:
    test_graph_is_planar(im, nodes)

def find_all_voronoi_points(x, y, im):
    # x, y = 0, 0 is the topleft pixel
    n = get_node(x, y, im)

    x_center = x + 0.5
    y_center = y + 0.5

    # for each of the eight directions, decide
    # where to put points, if at all
    # first, the up, down, left, right edges
    up = get_node(x, y-1, im)
    if up is not None:
        if up not in n.neighbours:
            n.vor_pts.append((x_center, y_center - 0.25))
    else:
        n.vor_pts.append((x_center, y_center - 0.5))

    dn = get_node(x, y+1, im)
    if dn is not None:
        if dn not in n.neighbours:
            n.vor_pts.append((x_center, y_center + 0.25))
    else:
        n.vor_pts.append((x_center, y_center + 0.5))

    lt = get_node(x-1, y, im)
    if lt is not None:
        if lt not in n.neighbours:
            n.vor_pts.append((x_center - 0.25, y_center))
    else:
        n.vor_pts.append((x_center - 0.5, y_center))

    rt = get_node(x+1, y, im)
    if rt is not None:
        if rt not in n.neighbours:
            n.vor_pts.append((x_center + 0.25, y_center))
    else:
        n.vor_pts.append((x_center + 0.5, y_center))

    # next, the diagonal neighbours
    up_in_neighbours = up is not None and up in n.neighbours
    dn_in_neighbours = dn is not None and dn in n.neighbours
    lt_in_neighbours = lt is not None and lt in n.neighbours
    rt_in_neighbours = rt is not None and rt in n.neighbours

    uplt = get_node(x-1, y-1, im)
    if uplt is not None:
        if uplt in n.neighbours:
            n.vor_pts.append((x_center - 0.75, y_center - 0.25))
            n.vor_pts.append((x_center - 0.25, y_center - 0.75))
            if (up_in_neighbours and not lt_in_neighbours) or \
                    (lt_in_neighbours and not up_in_neighbours):
                n.vor_pts.append((x_center - 0.5, y_center - 0.5))
        else:
            if up in lt.neighbours:
                n.vor_pts.append((x_center - 0.25, y_center - 0.25))
            else:
                n.vor_pts.append((x_center - 0.5, y_center - 0.5))
    else:
        n.vor_pts.append((x_center - 0.5, y_center - 0.5))

    dnlt = get_node(x-1, y+1, im)
    if dnlt is not None:
        if dnlt in n.neighbours:
            n.vor_pts.append((x_center - 0.75, y_center + 0.25))
            n.vor_pts.append((x_center - 0.25, y_center + 0.75))
            if (dn_in_neighbours and not lt_in_neighbours) or \
                    (lt_in_neighbours and not dn_in_neighbours):
                n.vor_pts.append((x_center - 0.5, y_center + 0.5))
        else:
            if dn in lt.neighbours:
                n.vor_pts.append((x_center - 0.25, y_center + 0.25))
            else:
                n.vor_pts.append((x_center - 0.5, y_center + 0.5))
    else:
        n.vor_pts.append((x_center - 0.5, y_center + 0.5))

    uprt = get_node(x+1, y-1, im)
    if uprt is not None:
        if uprt in n.neighbours:
            n.vor_pts.append((x_center + 0.75, y_center - 0.25))
            n.vor_pts.append((x_center + 0.25, y_center - 0.75))
            if (up_in_neighbours and not rt_in_neighbours) or \
                    (rt_in_neighbours and not up_in_neighbours):
                n.vor_pts.append((x_center + 0.5, y_center - 0.5))
        else:
            if up in rt.neighbours:
                n.vor_pts.append((x_center + 0.25, y_center - 0.25))
            else:
                n.vor_pts.append((x_center + 0.5, y_center - 0.5))
    else:
        n.vor_pts.append((x_center + 0.5, y_center - 0.5))

    dnrt = get_node(x+1, y+1, im)
    if dnrt is not None:
        if dnrt in n.neighbours:
            n.vor_pts.append((x_center + 0.75, y_center + 0.25))
            n.vor_pts.append((x_center + 0.25, y_center + 0.75))
            if (dn_in_neighbours and not rt_in_neighbours) or \
                    (rt_in_neighbours and not dn_in_neighbours):
                n.vor_pts.append((x_center + 0.5, y_center + 0.5))
        else:
            if dn in rt.neighbours:
                n.vor_pts.append((x_center + 0.25, y_center + 0.25))
            else:
                n.vor_pts.append((x_center + 0.5, y_center + 0.5))
    else:
        n.vor_pts.append((x_center + 0.5, y_center + 0.5))

def find_potentially_useless_points(n):
    num_pts = len(n.vor_pts)
    result = set()
    for i in xrange(len(n.vor_pts)):
        p1 = n.vor_pts[i     % num_pts]
        p2 = n.vor_pts[(i+1) % num_pts]
        p3 = n.vor_pts[(i+2) % num_pts]
        if (p1[0]-p2[0],p1[1]-p2[1]) == (p2[0]-p3[0],p2[1]-p3[1]):
            result.add(p2)
    return result

# given a list of points (in our case, the polygon points for some pixel),
# eliminate all points p such that p and its immediate neighbours
# have an angle of 180 degrees
def find_useless_pts(n):
    global points
    potentially_useless = find_potentially_useless_points(n)
    actually_useful = set()
    for coord_pair in potentially_useless:
        pt = points[coord_pair]
        for other_node in pt.nodes:
            if other_node != n and pt not in find_potentially_useless_points(other_node):
                actually_useful.add(pt.get_xy())
    useless = potentially_useless - actually_useful
    return useless

'''tests'''
# remember, our system is left-handed
# (0, 0) is the topleft pixel
# and NOT the bottom-left pixel
def test_is_to_the_left():
    assert is_to_the_left((-1,1), (0,0), (1,1)) is False
    assert is_to_the_left((0,0), (0,0), (1,1)) is False
    assert is_to_the_left((2,2), (0,0), (1,1)) is False
    assert is_to_the_left((-0.6,-0.4), (0,0), (1,1)) is False

def test_convex_hull():
    pts1 = [(0,0), (0.5,0.25), (0.75,0.25), (1,0), (0.75,0.75), (0.5,0.75), (0,1), (0.25,0.5)]
    cvh1 = {(0, 1), (0.75, 0.75), (1, 0), (0, 0)}

    pt2 = [(0,0), (1,-1), (1,0), (1,1), (1.5, -0.5), (2,0)]
    cvh2 = [(0,0), (1,-1), (1.5,-0.5), (2,0), (1,1)]

    pt3 = [(0,0), (1,1), (1,0), (1,-1), (1.5, 0.5), (2,0)]
    cvh3 = [(0,0), (1,1), (1.5,0.5), (2,0), (1,-1)]

    # assert convex_hull(pt2) == cvh2 # FAILS
    assert convex_hull(pt3) == cvh3

if '--tests' in sys.argv:
    test_is_to_the_left()
    test_convex_hull()

points = {}
# points is a dict mapping (x,y) to the Point present there.
# We could use an array because the Point locations are quantized
# to quarter-pixels, but there are 4wh possible point locations,
# which would mean a very sparse array and a lot of wasted
# memory. So the dict is a better way to store all the Points

# populate the neighbours for each point belonging to node n
# by treating n.vor_pts as a circular array
def populate_neighbours(n):
    global points
    # initialize the list of neighbours (with respect to n) for each point
    for p in n.vor_pts:
        points[p].neighbours[n] = set()
    # base cases
    num_vor_pts = len(n.vor_pts)
    if num_vor_pts == 1:
        return
    if num_vor_pts == 2:
        p1, p2 = points[n.vor_pts[0]], points[n.vor_pts[1]]
        p1.neighbours[n].add(p2)
        p2.neighbours[n].add(p1)
        return
    # circular array
    for i in xrange(len(n.vor_pts)):
        p = points[n.vor_pts[i]]
        p.neighbours[n].add(points[n.vor_pts[(i+1)%num_vor_pts]])
        p.neighbours[n].add(points[n.vor_pts[(i-1)%num_vor_pts]])

# now construct the simplified voronoi diagram
# and in the process, fill up the global Points map
for x in xrange(w):
    for y in xrange(h):
        find_all_voronoi_points(x, y, im)
        n = get_node(x, y, im)
        n.vor_pts = convex_hull(n.vor_pts)
        # populate the points dict
        for xx, yy in n.vor_pts:
            if (xx, yy) in points:
                p = points[(xx, yy)]
                p.nodes.add(n)
            else:
                p = Point(x=xx, y=yy)
                points[(xx, yy)] = p
                p.nodes.add(n)
        populate_neighbours(n)

# remove all useless points
for x in xrange(w):
    for y in xrange(h):
        n = get_node(x, y, im)
        useless_pts = find_useless_pts(n)
        n.vor_pts = filter(lambda p: p not in useless_pts, n.vor_pts)
        # also update the global points dict
        for p in useless_pts:
            # tell p's neighbours to forget p
            for ne in points[p].neighbours[n]:
                ne.neighbours[n].remove(points[p])
            del points[p]

# pt1 and pt2 are two polygon vertices in the simplified voronoi
# diagram this function checks if the reshaped pixels corresponding
# to the two polygons on either side of the edge joining pt1 to pt2
# are different enough for the edge to be classified as visible
def polygons_are_dissimilar(pt1, pt2):
    # get the pixels associated with both points and take the intersection of the two sets
    # this either has size 2 or size 1
    # the second case happens when the two polygon points are on the boundary
    # in this case, the edge is trivially not a visible edge since there is no
    # need to draw b-splines along the boundary
    # note that here, by "visible edge" we mean a single-length visible edge
    # whereas elsewhere, we use it to mean "a sequence of nodes separating 2 regions"
    intersection = pt1.nodes & pt2.nodes
    if len(intersection) == 1:
        return True
    else:
        assert len(intersection) == 2
        node1, node2 = intersection
        return pixels_are_dissimilar(node1.rgb, node2.rgb)

def test_point_positions():
    global points, imagename
    if imagename == 'img/smw_boo.png':
        assert (8.75, 11.75) in points
        assert (0, 0) in points

def test_point_neighbours():
    global points, imagename
    if imagename == 'img/smw_boo.png':
        assert (5.75, 0.75) in points
        # assert { (6,0), (5,1), (6.25,1.25) } == { pt.get_xy() for pt in points[(5.75, 0.75)].neighbours[get_node(5,1,im)] }

# TODO
def test_polygons_are_dissimilar():
    global points, imagename
    if imagename == 'img/smw_boo.png':
        p1 = points[(3.25, 4.25)]
        p2 = points[(2.75, 3.75)]
        assert not polygons_are_dissimilar(p1, p2)

if '--tests' in sys.argv:
    test_point_positions()
    test_point_neighbours()
    test_polygons_are_dissimilar()

# global "list" of visible edge sequences
vedges = set()

# pt is a point at which three visible edges are meeting
# this function merges them as per section 3.3 on page 5
def merge_visible_edges(pt):
    # locate the neighbour of 'pt' in each one of these vedges
    # this can be done in constant time, since we know that pt
    # is an endpoint for each one of these vedges, and therefore
    # it is either at the head or the tail of the lists
    vedge1, vedge2, vedge3 = pt.vedges
    neighb1 = vedge1.points[1] if vedge1.points[0] == pt else vedge1.points[-2]
    neighb2 = vedge2.points[1] if vedge2.points[0] == pt else vedge2.points[-2]
    neighb3 = vedge3.points[1] if vedge3.points[0] == pt else vedge3.points[-2]
    # measure the angles - TODO
    pass

def keep_closest_collinear_neighbours(p, neighbours):
    # filter all neighbours ne such that p has a neighbour ne', ne' has ne as its neighbour
    # and p, ne and ne' lie on a straight line with ne' in between p and ne
    to_remove = set()
    for i in xrange(len(neighbours)):
        for j in xrange(i+1, len(neighbours)):
            if is_straight_line(p, neighbours[i], neighbours[j]):
                # if p is not the middle point, remove
                # the neighbour which is farther away
                if p.x < neighbours[i].x and p.x < neighbours[j].x:
                    if neighbours[i].x < neighbours[j].x:
                        to_remove.add(neighbours[j])
                    else:
                        to_remove.add(neighbours[i])
                elif p.x > neighbours[i].x and p.x > neighbours[j].x:
                    if neighbours[i].x > neighbours[j].x:
                        to_remove.add(neighbours[j])
                    else:
                        to_remove.add(neighbours[i])

    return filter(lambda p: p not in to_remove, neighbours)

# p is a point for which we want to find all
# containing visible edge sequences
def find_all_visible_edges(p):
    # keep only neighbours with which I have a single-length visible edge
    slve_neighbours = filter(lambda x: polygons_are_dissimilar(x, p), p.all_neighbours())
    # keep only my closest neighbours along a line
    slve_neighbours = keep_closest_collinear_neighbours(p, slve_neighbours)
    # remove neighbours which already have a visible edge *sequence* with me
    for ve_object in p.vedges:
        slve_neighbours = filter(lambda ne: ne not in ve_object.points, slve_neighbours)

    # should we explore the visible edge with (p, ne) as a starting edge?
    # yes, if ne has not been explored before. if it has,
    #  then surely it encountered the (ne, p) edge
    visible_edges = [find_visible_edge(p, ne) for ne in slve_neighbours]

    # check if two visible edge sequences are actually reversals of each other
    to_remove = set()
    for i in xrange(len(visible_edges)):
        for j in xrange(len(visible_edges)):
            if i != j:
                v, w = visible_edges[i], visible_edges[j]
                # we found a pair, and neither i nor j is marked for removal
                # first check for cycles
                vv = v[1:-1] if v[0] == v[-1] else v
                ww = w[1:-1] if w[0] == w[-1] else w
                if vv == list(reversed(ww)) and j not in to_remove and i not in to_remove:
                    # add i to to_remove. we could add j too, either way works
                    to_remove.add(i)
    # perform the removal
    visible_edges = [v for i,v in enumerate(visible_edges) if i not in to_remove]
    
    # if we only have two visible edge sequences, they are actually
    # two disjoint parts of one single visible edge sequence. so, we merge them
    if len(visible_edges) == 2 and len(p.vedges) == 0: # partial fix
        visible_edge1, visible_edge2 = visible_edges[0], visible_edges[1]

        # we need to check if either of the two sequences is a cycle
        is_cycle1 = visible_edge1[0] == visible_edge1[-1]
        is_cycle2 = visible_edge2[0] == visible_edge2[-1]

        if not is_cycle1 and not is_cycle2:
            visible_edges = [list(reversed(visible_edge1))[:-1] + visible_edge2]

    result = []
    for v in visible_edges:
        ve_object = VisibleEdge(v)
        result.append(ve_object)
        for pt in v:
            pt.vedges.add(ve_object)

    return result

# returns true if points a b and c are collinear
def is_straight_line(p1, p2, p3):
    a, b, c = p1.get_xy(), p2.get_xy(), p3.get_xy()
    if a[1] == b[1]: return b[1] == c[1]
    if c[1] == b[1]: return b[1] == a[1]
    slope1 = float(a[0]-b[0]) / float(a[1]-b[1])
    slope2 = float(c[0]-b[0]) / float(c[1]-b[1])
    return slope1 == slope2

# (p1, p2) is the first edge of the visible
# edge with p1 as an endpoint. Examples:
# 1 - 2 - 3 yields the list [1,2,3]
# 1 - 2 - 3 - 1 yields the list [1,2,3,1]
def find_visible_edge(p1, p2):
    assert p1 in p2.all_neighbours()
    assert p2 in p1.all_neighbours()

    prev, curr = p1, p2
    encountered = set([p1, p2])
    result = [p1]
    while True:
        slve_neighbours = filter(lambda x: polygons_are_dissimilar(x, curr), curr.all_neighbours())
        slve_neighbours = keep_closest_collinear_neighbours(curr, slve_neighbours)

        if len(slve_neighbours) != 2:
            result.append(curr)
            break

        result.append(curr)

        neighb1, neighb2 = slve_neighbours
        if neighb1 == prev:
            prev, curr = curr, neighb2
        else:
            prev, curr = curr, neighb1

        if curr not in encountered:
            encountered.add(curr)
        else:
            result.append(curr)
            break

    return result

for p in points.values():
    vedges |= set(find_all_visible_edges(p))

def merge_vedges(p, edge1, edge2, m):
    global vedges

    initial = len(vedges)

    e1, e2 = edge1.points, edge2.points

    if e1[0] != p: e1.reverse() # CHECK
    if e2[0] != p: e2.reverse() # THIS!

    is_cycle1 = e1[0] == e1[-1]
    is_cycle2 = e2[0] == e2[-1]
    if is_cycle1 and is_cycle2:
        e = e1[:-1] + e2
    elif is_cycle1 and not is_cycle2:
        e = list(reversed(e2))[:-1] + e1
    else: # CHECK [ABOVE] THIS
        e = list(reversed(e1))[:-1] + e2

    new_edge = VisibleEdge(e)

    vedges.remove(edge1)
    vedges.remove(edge2)

    for pt in new_edge.points:
        if edge1 in pt.vedges:
            pt.vedges.remove(edge1)
        if edge2 in pt.vedges:
            pt.vedges.remove(edge2)
        pt.vedges.add(new_edge)

    vedges.add(new_edge)

    if initial <= len(vedges): # less than not possible, right?
        print p, "merging by", m, "::", initial, ">", len(vedges)
        point_list.append(p)

def angle(o, a, b):
    def d(l, m): return (l.x - m.x)**2 + (l.y - m.y)**2
    P12, P23, P13 = d(o, a), d(a, b), d(o, b)
    angle = math.acos((P12 + P13 - P23) / (2 * math.sqrt(P12 * P13)))
    return math.degrees(angle) # converted from radians

def resolve_juction(p):
    global vedges, count

    assert len(p.vedges) == 3
    v1, v2, v3 = p.vedges

    def corner(p, vedge):
        return True if p == vedge[0] or p == vedge[1] else False

    # if not(corner(p, v1) and corner(p, v2) and corner(p, v3)):
    #     # print "bugfix pending; workaround in play"
    #     point_list.append(p)
    #     return

    ne1 = v1[1] if v1[0] == p else v1[-2]
    ne2 = v2[1] if v2[0] == p else v2[-2]
    ne3 = v3[1] if v3[0] == p else v3[-2]

    # print 'junction', p, ne1, ne2, ne3

    if p == ne1 or p == ne2 or p == ne3:
        return

    e1, e2, e3 = map(lambda ne: is_contour_edge(p, ne), [ne1, ne2, ne3])

    if e1 and e2 and not e3:
        merge_vedges(p, v1, v2, "contour edges")
    elif e2 and e3 and not e1:
        merge_vedges(p, v2, v3, "contour edges")
    elif e3 and e1 and not e2:
        merge_vedges(p, v3, v1, "contour edges")
    else: # connect edges 180 degrees apart
        a1, a2, a3 = angle(p, ne1, ne2), angle(p, ne2, ne3), angle(p, ne3, ne1)
        if a1 > a2 and a1 > a3:
            # point_list.append(ne3)
            merge_vedges(p, v1, v2, "closest angle")
        elif a2 > a3 and a2 > a1:
            # point_list.append(ne1)
            merge_vedges(p, v2, v3, "closest angle")
        elif a3 > a1 and a3 > a2:
            # point_list.append(ne2)
            merge_vedges(p, v3, v1, "closest angle")
        # else: # exclusive conditions?
            # print "#debug: couldn't merge ANY edges\n"

def is_contour_edge(pt1, pt2):
    #
    intersection = pt1.nodes & pt2.nodes
    if len(intersection) == 1:
        return True
    else:
        ## if len(intersection) != 2: return False
        node1, node2 = intersection
        return not shading_edge(node1.rgb, node2.rgb)

for p in points.values():
    if len(p.vedges) > 3:
        # print "unlikely case:", p, len(p.vedges)
        pass
    if len(p.vedges) == 3:
        # point_list.append(p)
        resolve_juction(p)

def test_visible_edges():
    global imagename

    num_vedges = { 'img/smw_boo.png' : 6,
                   'img/invaders_01.png' : 4,
                   'img/invaders_02.png' : 3,
                   'img/invaders_03.png' : 3,
                   'img/invaders_04.png' : 3,
                   'img/smw_help.png' : 8,
                }

    if imagename in num_vedges:
        assert len(vedges) == num_vedges[imagename]

    if imagename == 'img/smw_boo.png':
        v = points[(7,1)].vedges
        assert len(v) == 1
        assert len(v.pop().points) == 67

        v = points[(3.25, 4.25)].vedges
        assert len(v) == 1
        assert len(v.pop().points) == 59

        v = points[(4.25, 5.25)].vedges
        assert len(v) == 1
        assert len(v.pop().points) == 9

        v = points[(9.25, 6.25)].vedges
        assert len(v) == 1
        assert len(v.pop().points) == 23

        v = points[(3.25, 10.25)].vedges
        assert len(v) == 1
        assert len(v.pop().points) == 25

if '--tests' in sys.argv:
    test_visible_edges()

# for v in vedges:
#     v.bspline = bspline_eval(v.points)

from numpy import array, linspace
import matplotlib.pyplot as plt
import scipy.interpolate as si

# p = points[(5,13)]
# point_list = []
# # point_list = [p]
# for v in p.vedges:
#     second = v[1] if p == v[0] else v[-2]
#     end = v[-1] if p == v[0] else v[0]
#     print 'second', second, 'end', end
#     point_list.append(second)
#     point_list.append(end)

# credit - http://stackoverflow.com/questions/24612626/b-spline-interpolation-with-python
DEGREE, SMOOTHNESS = 3, 150
for v in vedges:
    pts = [p.get_xy() for p in v.points]
    degree = DEGREE

    # cycle check
    periodic = False
    if pts[0] == pts[-1]:
        pts.pop()
        periodic = True
        # pts = pts[1:-1]

    if periodic: pts = pts + pts[0 : degree+1]
    else: pts = [pts[0]] + pts + [pts[-1],pts[-1]]

    pts = array(pts)
    n_points = len(pts)
    x, y = pts[:,0], pts[:,1]

    t = range(len(x))
    ipl_t = linspace(1.0, len(pts) - degree, SMOOTHNESS)

    x_tup = si.splrep(t, x, k=degree, per=periodic)
    y_tup = si.splrep(t, y, k=degree, per=periodic)
    x_list = list(x_tup)
    xl = x.tolist()

    y_list = list(y_tup)
    yl = y.tolist()

    if periodic:
        x_list[1] = [0.0] + xl + [0.0, 0.0, 0.0, 0.0]
        y_list[1] = [0.0] + yl + [0.0, 0.0, 0.0, 0.0]

    x_i = si.splev(ipl_t, x_list)
    y_i = si.splev(ipl_t, y_list)

    v.bspline = zip(x_i, y_i)

render_stage = process_command_line_arg('--render')
if render_stage is not None:
    render(render_stage)