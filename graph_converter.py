# -*- coding: utf-8 -*-
"""
Created on Wed May 22 16:30:39 2019

@author: 2624224
"""
import os
import glob
from multiprocessing import Pool
import logging
import pickle
import numpy as np
import sys
sys.path.append('..')
import argparse
import os.path as osp

import shape
import logger
import OCCUtils
import occ_utils

def feature_from_face(face_util):
    normal = occ_utils.as_list(occ_utils.normal_to_face_center(face_util))
    _, pnt = face_util.mid_point()
    pnt = occ_utils.as_list(pnt)
    d = np.dot(normal, pnt)
    return normal + [d]


def graph_from_shape(a_shape):        
    a_graph = {}
    a_graph['y'] = a_shape.face_truth
    a_graph['x'] = [None] * len(a_shape.face_ids)
    a_graph['edge_index'] = [[],[]]
     
    for face in a_shape.face_ids:        
        face_util = OCCUtils.face.Face(face)
        a_graph['x'][a_shape.face_ids[face]] = feature_from_face(face_util)
        for edge in face_util.edges():
            face_adjacent = occ_utils.face_adjacent(a_shape.shape, face, edge)
            a_graph['edge_index'][0].append(a_shape.face_ids[face])
            a_graph['edge_index'][1].append(a_shape.face_ids[face_adjacent])
    return a_graph 


def save_graph(graph, graph_path, shape_name):
    with open(os.path.join(graph_path, shape_name + '.graph'), 'wb') as file:
        pickle.dump(graph, file)

    
def generate_graph(arg):
    '''
    generate points for shapes listed in CATEGORY_NAME_step.txt
    '''
    shape_dir = arg[0]
    graph_path = arg[1]
    shape_name = arg[2]

#    logging.info(shape_name)
    if os.path.exists(os.path.join(graph_path, shape_name + '.graph')):
        return 0
    try:
        a_shape = shape.LabeledShape(shape_dir)
        a_shape.load(shape_name)
    except:
        logging.info(shape_name + ' failed loading')
        return 0
    
    if a_shape.check() == False:
        return 0

    try:
        a_graph = graph_from_shape(a_shape)
    except:
        logging.info(shape_name + 'failed to create graph')
        return 0

    save_graph(a_graph, graph_path, shape_name)
    return 1


parser = argparse.ArgumentParser()
parser.add_argument('--shape_dir', 
                    default=osp.join(osp.dirname(osp.realpath(__file__)), '../data/raw/simple/'), 
                    help="Directory containing the step files")
parser.add_argument('--graph_dir', 
                    default=osp.join(osp.dirname(osp.realpath(__file__)), '../data/processed/simple'), 
                    help="Directory containing the step files")
args = parser.parse_args()

if __name__ == '__main__':
    logger.set_logger('graph_converter.log')    

    if not os.path.exists(args.graph_dir):
        os.mkdir(args.graph_dir)
    
    shape_paths = glob.glob(args.shape_dir + '*.step')
    shape_names = [shape_path.split(os.sep)[-1].split('.')[0] for shape_path in shape_paths]    
    logging.info(str(len(shape_paths)) + ' models to be converted')
    results = Pool().map(generate_graph, [(args.shape_dir, args.graph_dir, shape_name) for shape_name in shape_names])
    logging.info(str(sum(results)) + ' models converted')
