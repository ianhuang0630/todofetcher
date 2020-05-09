"""
Script for syncing up notebook notes
"""
import os
import pickle
from datetime import datetime
from utils import *
import config 


if __name__ == '__main__':

    if not os.path.exists('.data/'):
        os.makedirs('.data/')
    if os.path.exists('.data/mem.pkl'):
        with open(os.path.join('.data/', 'mem.pkl'), 'rb')  as f:
            params = pickle.load(f)
        config.HEX_START = params['HEX_START']
    else:
        params = {} 
    
    if os.path.exists('.data/hash2completion.pkl'):
        with open(os.path.join('.data/', 'hash2completion.pkl'), 'rb') as f:
            hash2completion = pickle.load(f)
    else:
        hash2completion = {} 

    if os.path.exists('.data/hash2path.pkl'):
        with open(os.path.join('.data/', 'hash2path.pkl'), 'rb') as f:
            hash2path = pickle.load(f) # may need special script to regenerate if the paths of documents are changed
    else:
        hash2path = {}
   
    if os.path.exists('.data/path2modtime.pkl'):
        with open(os.path.join('.data/', 'path2modtime.pkl'), 'rb') as f:
            path2modtime = pickle.load(f)
    else:
        path2modtime = {}
    
    # iterate through the whole list of notes
    assert type(config.NOTES_DIRS) is list
    assert type(config.VALID_EXT) is list
    all_notes = []
    for d in config.NOTES_DIRS: 
        files = os.listdir(d)
        files_path = [os.path.join(d, fname) for fname in \
                files if ends_in_exts(fname, config.VALID_EXT)]
        # check if it's got recent modifications
        for filepath in files_path:
            if has_new_modification(filepath, path2modtime):
                all_notes.append(filepath)
    
    # iterate through all of the files, get back the checklist items
    note2newtodos_w_hashes = {}
    for note in all_notes:
        print('examining {}'.format(note))
        todos_w_hashes = get_new_unchecked_todos(note) 
        note2newtodos_w_hashes[note] = todos_w_hashes
    
    # #########################################################################
    # loading the todo.md -> first thing to do --> cross off the items in the original notes
    # get the checked hashes
    hashes = get_checked_hashes(config.TODOLIST_NAME)
    path2newcheckhash = {}
    newcheckhash = []
    # find only the new hashes that have recently been checked off 
    for hash_ in hashes: 
        if hash2completion['0x'+hash_] is False: # hash not currently checked of
            newcheckhash.append(hash_)
            filepath = hash2path['0x'+hash_]
            if filepath not in path2newcheckhash:
                path2newcheckhash[filepath] = [hash_]
            else:
                path2newcheckhash[filepath].append(hash_)
    # for each file, find the hashes and check them off
    mark_as_newly_completed = []
    newly_completed_fpaths = []
    for fpath in path2newcheckhash:
        assert type(path2newcheckhash[fpath]) is list
        if check_off_original_notes(fpath, path2newcheckhash[fpath]):
            mark_as_newly_completed.extend(path2newcheckhash[fpath]) # we will only update hash2complete if the file can be found
            newly_completed_fpaths.append(fpath)
    if len(mark_as_newly_completed) != len(newcheckhash):
        print('There are some notes that cannot be discovered. either find and \
                reposition them in the correct paths or remake the path database')
    
    # ######################################################################### 
    # writing to todo.md
    # adding new todo's into the todo file
    write_to_todo(note2newtodos_w_hashes) 
    write_hashes_on_new_todos(note2newtodos_w_hashes)
    # ######################################################################### 
    
    # before exiting:
    # 1. update hash2completion for hex values in mark_as_newly_completed, and add new hex values from recent hashes
    for hash_ in mark_as_newly_completed:
        hash2completion['0x'+hash_] = True
    # 2. update hash2path with the new todo items in note2newtodos_w_hashes 
    for note in note2newtodos_w_hashes:
        for tup in note2newtodos_w_hashes[note]:
            hash2path[tup[1]] = note 
            hash2completion[tup[1]] = False
    
    for filepath in list(set(all_notes + newly_completed_fpaths)):
        path2modtime[filepath] = get_modification_date(filepath)

    with open(os.path.join('.data/', 'hash2completion.pkl'), 'wb') as f:
        print('updated hash2completion')
        pickle.dump(hash2completion,f)
    with open(os.path.join('.data/', 'hash2path.pkl'), 'wb') as f:
        print('updated hash2path')
        pickle.dump(hash2path, f)
    # 3. update HEX_START in mem.pkl
    with open(os.path.join('.data/', 'mem.pkl'), 'wb') as f:
        pickle.dump({'HEX_START': config.HEX_START}, f)
    # 4. update modification times
    with open(os.path.join('.data/', 'path2modtime.pkl'), 'wb') as f:
        pickle.dump(path2modtime, f)

