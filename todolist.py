"""
Script for syncing up notebook notes
"""
import os
import pickle
from datetime import datetime

TODOLIST_NAME = 'todo.md'
NOTES_DIRS = ['test_notes']
VALID_EXT = ['.md']
CHECKLIST_CHECKED_MARKERS = ['* [x]'] 
CHECKLIST_UNCHECKED_MARKERS = ['* [ ]'] 
HEX_START = 0
HEX_BITS = 8

def ends_in_ext(fname, ext):
    return fname[-len(ext):] == ext

def ends_in_exts(fname, exts):
    assert type(exts) is list
    for ext in exts:
        if ends_in_ext(fname, ext):
            return True
    return False

def has_checklist_marker(line, checked):
    assert type(line) is str
    # returns the index where the marker is found and the index corresponding 
    # to the marker type
    assert type(CHECKLIST_UNCHECKED_MARKERS) is list
    assert type(CHECKLIST_CHECKED_MARKERS) is list
    if checked:
        markers_list = CHECKLIST_CHECKED_MARKERS
    else:
        markers_list = CHECKLIST_UNCHECKED_MARKERS
    for mk_idx, marker in enumerate(markers_list):
        idx = line.find(marker)
        if idx != -1:
            return idx, mk_idx 
    return None, None

def get_todos(fpath, checked):
    assert type(fpath) is str
    assert os.path.exists(fpath)
    todos = []
    todo_nb = []
    with open(fpath, 'r') as f:
        lines=f.readlines()
        for l_nb, line in enumerate(lines):
            idx, mk_idx = has_checklist_marker(line, checked)
            if idx is not None and mk_idx is not None:
                todos.append( line[idx:].strip() )
                todo_nb.append(l_nb)

    return todos, todo_nb

def find_hex(todo):
    assert type(todo) is str
    hex_idx = todo.find('{0x')
    if hex_idx == -1:
        return None
    hex_str = todo[hex_idx+len('{0x') : hex_idx+len('{0x')+HEX_BITS]
    try:
        int(hex_str, 16)
    except ValueError: 
        return None
    
    return {'where': hex_idx, 'hex': hex_str} 

def generate_hex():
    global HEX_START
    new_hex = '0x'+'%0{}X'.format(HEX_BITS) % HEX_START
    HEX_START += 1
    return new_hex

def assign_hex(todo, new_hex):
    # assuming that the todo doesn't already have a hex assigned to it.
    # if it does, then overwite it
    old_hex = find_hex(todo)
    assert type(todo) is str and type(new_hex) is str
    if old_hex == None:
        if todo[-1] != ' ':
            todo += ' '
        todo += '{' + new_hex + ')'
    else:
        todo[old_hex['where'] + len('{') : old_hex['where'] + len('{')+HEX_BITS] = new_hex
    
    return todo

def read_duration(substring):
    assert type(substring) is str
    fragments = substring.split()
    found = [ (idx, chunk) for idx, chunk in enumerate(fragments) if chunk.isdigit()]
    if len(found) == 0:
        return None
    

    if len(found)>0 and found[0][0] + 1 < len(fragments) and fragments[found[0][0]+1] == 'm': 
        return found[0][1] + ' m'

    if len(found)>1 and found[1][0] + 1 < len(fragments) and fragments[found[0][0]+1] == 'h':
        # add hour
        if len(found)>1 and found[1][0] + 1 < len(fragments) and fragments[found[1][0]+1] == 'm':
            return found[0][1] + ' h ' + found[1][1] + ' m'
        else:
            return found[0][1] + ' h'
    else:
        return None

def find_duration(todo):
    last_comma_idx = todo[::-1].find(',')
    if last_comma_idx == -1:
        return None
    substring = todo[-(last_comma_idx + 1):]
    duration = read_duration(substring)
    if duration == None:
        print('WARNING: duration missing for {}'.format(todo))
    
    return duration

def add_placeholder_duration(todo):
    
    last_comma_idx = todo[::-1].find(',')
    if last_comma_idx == -1:
        todo += ', 30 m'
    else:
        todo = todo[: -(last_comma_idx + 1)] + ' 30 m' + todo[-(last_comma_idx + 1):] 
    return todo 

def get_new_unchecked_todos(fpath):
    todos, todo_lnb = get_todos(fpath, False)
    
    # check there isn't a hash already given. if so, drop it
    new_todos = []
    new_todo_lnb = []
    for idx, todo in enumerate(todos):
        if find_hex(todo) is None: # means that it's new
            new_todos.append(todo)
            new_todo_lnb.append(todo_lnb[idx])

    new_hashes = [generate_hex() for todo in new_todos]
    # for each todo, we should check that there's a time duration indicated
    new_todos_wtime = []
    for todo in new_todos:
        duration = find_duration(todo)
        if duration is None:
            print('WARNING: adding default duration of 30 m for {}'.format(todo))
            todo = add_placeholder_duration(todo)
            new_todos_wtime.append(todo)
        else:
            new_todos_wtime.append(todo)    
    assert len(new_hashes) == len(new_todos_wtime)
    return list(zip(new_todos_wtime, new_hashes, new_todo_lnb))

def get_checked_hashes(fpath):
    todos, _ = get_todos(fpath, True)
    checked_hashes = []
    for todo in todos:
        checked_hex = find_hex(todo)
        if checked_hex is not None: # ignoring adhoc todolists without hashes
            hex_string = checked_hex['hex']
            checked_hashes.append(hex_string)
    return checked_hashes


def find_line_with_hash(lines, hex_id):
    for line_id, line in enumerate(lines):
        if hex_id in line: 
            return (line_id, line)

    return None

def check_off_line(line):
    for idx, element in enumerate(CHECKLIST_UNCHECKED_MARKERS):
        checkbox_idx = line.find(element)
        if checkbox_idx != -1:
            return line [:checkbox_idx] + CHECKLIST_CHECKED_MARKERS[idx] \
                    + line[checkbox_idx + len(CHECKLIST_UNCHECKED_MARKERS[idx]) : ]
    
    for idx, element in enumerate(CHECKLIST_CHECKED_MARKERS):
        checkbox_idx = line.find(element)
        if checkbox_idx != -1:
            return line # this line was already checked
    
    return None

def check_off_original_notes(fpath, hex_ids):
    assert type(hex_ids) is list
    # opens up the file, and then checks off the box
    try: 
        with open(fpath, 'r') as f:
            lines = f.readlines()
            # find the line with the hex
            for hex_id in hex_ids:
                line_tup = find_line_with_hash(lines, hex_id)
                assert line_tup is not None, "database needs to be updated"
                line_id = line_tup[0]
                line = check_off_line(line_tup[1])
                lines[line_id] = line
    except FileNotFoundError:
        print('{} not found'. format(fpath))
        return False

    try:
        with open(fpath, 'w') as f:
            f.writelines(lines) 
        return True
    except:
        return False

def get_date_string(): 
    date = datetime.now().date()
    return str(date.month)+'/'+ str(date.day)+'/'+str(date.year)[-2:]

def find_datestring_in_lines(lines, ds):
    for l_nb, line in enumerate(lines):
        if ''.join(line.strip().split()) == ds:
            return l_nb
    return None 

def find_todoheader_in_lines(lines):
    return find_datestring_in_lines(lines, '#TODO')

def todoline_formatter(note2newtodos_w_hashes):
    write_todos = []
    if len(note2newtodos_w_hashes):
        for note in note2newtodos_w_hashes:
            for todo_hex in note2newtodos_w_hashes[note]:
                write_todos.append ("%s {%s} (in `%s`)"%(todo_hex[0], todo_hex[1], note))
        write_todos = [element+'\n' for element in write_todos]
    
    return write_todos 
 
def write_to_todo(note2newtodos_w_hashes):
    assert type(note2newtodos_w_hashes) is dict
    ds =get_date_string()
    # loading current todo
    with open(TODOLIST_NAME, 'r') as f:
        lines = f.readlines()
        d_nb = find_datestring_in_lines(lines, ds)
    
    # formatting new todos
    newlines = todoline_formatter(note2newtodos_w_hashes)
    if d_nb is None:
        t_nb = find_todoheader_in_lines(lines)
        newlines = [ds+'\n'] + newlines + ['\n']
        new_todolist = lines[:t_nb+1] + newlines + lines[t_nb+1:]
    else:
        new_todolist = lines[:d_nb+1] + newlines + lines[d_nb+1:] 
     
    # writing current todo 
    with open(TODOLIST_NAME, 'w') as f:
        f.writelines(new_todolist)

def write_hashes_on_new_todos(note2newtodos_w_hashes):
    for note in note2newtodos_w_hashes:
        if len(note2newtodos_w_hashes[note]): # open the file only if you have new todo's from here
            todo_hashes = note2newtodos_w_hashes[note]
            # todo_hashes is a list of 3-tuples, where the 3rd element is the line number where the todolist item is
            with open(note, 'r') as f:
                lines = f.readlines()
                for tup in todo_hashes:
                    # appending hex
                    lines[tup[2]] = lines[tup[2]].strip() + ' {%s}\n'%tup[1] 
            with open(note, 'w') as f:
                f.writelines(lines)

def get_modification_date(filepath):
    t = os.path.getmtime(filepath)
    return datetime.fromtimestamp(t)

def has_new_modification(filepath, path2modtime):
    if filepath not in path2modtime:
        return True
    else:
        mdate = get_modification_date(filepath)
        assert type(path2modtime[filepath]) is datetime
        return mdate > path2modtime[filepath]

if __name__ == '__main__':

    if not os.path.exists('.data/'):
        os.makedirs('.data/')
    if os.path.exists('.data/mem.pkl'):
        with open(os.path.join('.data/', 'mem.pkl'), 'rb')  as f:
            params = pickle.load(f)
        HEX_START = params['HEX_START']
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
    assert type(NOTES_DIRS) is list
    assert type(VALID_EXT) is list
    all_notes = []
    for d in NOTES_DIRS: 
        files = os.listdir(d)
        files_path = [os.path.join(d, fname) for fname in \
                files if ends_in_exts(fname, VALID_EXT)]
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
    hashes = get_checked_hashes(TODOLIST_NAME)
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
        pickle.dump({'HEX_START': HEX_START}, f)
    # 4. update modification times
    with open(os.path.join('.data/', 'path2modtime.pkl'), 'wb') as f:
        pickle.dump(path2modtime, f)

