"""
utilities functions 
"""
import os
import pickle
from datetime import datetime, timedelta
import config

def ends_in_ext(fname, ext):
    """
    Checks if fname ends in ext
    """
    return fname[-len(ext):] == ext

def ends_in_exts(fname, exts):
    """
    Checks if fname ends in any of the list of exts
    """
    assert type(exts) is list
    for ext in exts:
        if ends_in_ext(fname, ext):
            return True
    return False

def has_checklist_marker(line, checked):
    """
    checks if a line (string) has a checked or unchecked marker (depending on 
    whether `checked`==True), and returns the index of the marker, as well as 
    the index of the type of marker found.
    """
    assert type(line) is str
    # returns the index where the marker is found and the index corresponding 
    # to the marker type
    assert type(config.CHECKLIST_UNCHECKED_MARKERS) is list
    assert type(config.CHECKLIST_CHECKED_MARKERS) is list
    if checked:
        markers_list = config.CHECKLIST_CHECKED_MARKERS
    else:
        markers_list = config.CHECKLIST_UNCHECKED_MARKERS
    for mk_idx, marker in enumerate(markers_list):
        idx = line.find(marker)
        if idx != -1:
            return idx, mk_idx 
    return None, None

def mmddyy2datetime(mmddyy):
    """
    mmddyy string to datetime object.
    """
    clean_mmddyy = '/'.join([element.strip() for element in mmddyy.split('/')])
    datetime_mmddyy = datetime.strptime(clean_mmddyy, '%m/%d/%y')
    return datetime_mmddyy


def durationlist2datetime(duration_split):
    """
    duration string split (by spaces) list to datetime object.
    """
    assert len(duration_split)%2 == 0
    digits = []
    if len(duration_split) == 4:
        # case # h # m
        digits = [int(duration_split[0]), int(duration_split[2])] 
    elif len(duration_split) == 2:
        if duration_split[1] == 'm':
            digits = [0, int(duration_split[0])]
        elif duration_split[1] == 'h':
            digits = [int(duration_split[0]), 0]
        else:
            raise ValueError('duration string should be in the form # m, # h, or # h # m')
    assert len(digits) != 0
    duration_datetime = timedelta(hours = digits[0], minutes=digits[1])# datetime.strptime('::'.join(digits),'%H::%M')
    return duration_datetime 

def duration2datetime(duration_str):
    """
    Duration string to datetime object.
    """ 
    duration_split = duration_str.split()
    return durationlist2datetime(duration_split) 
    
def unchecked_by_date():
    """
    Returns a list of tuples of the form (todo_string, datetime_assigned)
    """
    with open(config.TODOLIST_NAME, 'r') as f:
        lines = f.readlines()
        dates_lnb= find_all_datetimes_mmddyy_in_lines(lines) 
    
    todos, todo_nb = get_todos(config.TODOLIST_NAME, checked=False)
    todos_lnb = list(zip(todos, todo_nb))
    # open up the todolist file 
    master_list = dates_lnb + todos_lnb
    master_list = sorted(master_list, key = lambda x: x[1])
    
    # [(todo item, date)]
    current_date = None
    todo2date = []
    for element in master_list:
        if type(element[0]) is datetime:
            current_date = element[0] 
        elif type(element[0]) is str:
            assert current_date is not None, "we have a rogue todolist item without a date"
            todo2date.append((element[0], current_date))
    return todo2date


def get_todos(fpath, checked):
    """
    get a list of todo's from fpath that are either checked/unchecked depending
    on wehther `checked`==True
    """
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
    """
    given a single todo item as a string, find the hex_string and its index in the
    string. If none found, return None.
    """
    assert type(todo) is str
    hex_idx = todo.find('{0x')
    if hex_idx == -1:
        return None
    hex_str = todo[hex_idx+len('{0x') : hex_idx+len('{0x')+config.HEX_BITS]
    try:
        int(hex_str, 16)
    except ValueError: 
        return None
    
    return {'where': hex_idx, 'hex': hex_str} 

def generate_hex():
    """
    increments the global hex id, and returns it.
    """
    # global config.HEX_START
    new_hex = '0x'+'%0{}X'.format(config.HEX_BITS) % config.HEX_START
    config.HEX_START += 1
    return new_hex

def assign_hex(todo, new_hex):
    """
    Generates/replaces the todo hex, and appends it to the end of the string,
    then returns that todo.
    """
    # assuming that the todo doesn't already have a hex assigned to it.
    # if it does, then overwite it
    old_hex = find_hex(todo)
    assert type(todo) is str and type(new_hex) is str
    if old_hex == None:
        if todo[-1] != ' ':
            todo += ' '
        todo += '{' + new_hex + ')'
    else:
        todo[old_hex['where'] + len('{') : old_hex['where'] + len('{')+config.HEX_BITS] = new_hex
    
    return todo

def read_duration(substring):
    """
    the substring will be the last part of the string separated by a comma. 
    read_duration will return the time duration in the substring. If not found,
    will return none.
    """
    assert type(substring) is str
    fragments = substring.split()
    found = [ (idx, chunk) for idx, chunk in enumerate(fragments) if chunk.isdigit()]
    if len(found) == 0:
        return None
    
    # testing for the strong condition first
    if len(found)>1 and found[1][0] + 1 < len(fragments) and fragments[found[0][0]+1] == 'h':
        # add hour
        if fragments[found[1][0]+1] == 'm':
            return found[0][1] + ' h ' + found[1][1] + ' m'
        else: # if the other field is filled with some sort of nonsense
            return found[0][1] + ' h'
 
    if len(found)>0 and found[0][0] + 1 < len(fragments):
        if fragments[found[0][0]+1] == 'm': 
            return found[0][1] + ' m'
        if fragments[found[0][0]+1] == 'h':
            return found[0][1] + ' h'
    else:
        return None

def find_duration(todo):
    """
    Returns the duration as "# h # m" or "# m" or "# h" for a single todo. If no
    duration found, then the default duration is given.
    """
    last_comma_idx = todo[::-1].find(',')
    if last_comma_idx == -1:
        return None
    substring = todo[-(last_comma_idx + 1):]
    duration = read_duration(substring)
    if duration == None:
        print('WARNING: duration missing for {}'.format(todo))
    
    return duration

def add_placeholder_duration(todo):
    """
    Attaching default duration to the end of the todo list item, and returning it.
    """ 
    if todo.strip()[-1] == ',':
        todo += ' 30 m'
    else:
        todo += ', 30 m'
    
    return todo
    # last_comma_idx = todo[::-1].find(',')
    # if last_comma_idx == -1:
    #     todo += ', 30 m'
    # else:
    #     # if there's nothing after the comma 
    #     # else, do the followin
    #     import ipdb; ipdb.set_trace()

    #     todo = todo[: -(last_comma_idx + 1)] + ' 30 m' + todo[-(last_comma_idx + 1):] 
    # return todo 

def get_new_unchecked_todos(fpath):
    """
    From a file (fpath), return list of tuples for todos, their hashes, 
    and their line numbers in the original text files (though those are subject 
    to change)
    """
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
    """
    for all checked todos, return the set of all hex hashes
    """
    todos, _ = get_todos(fpath, True)
    checked_hashes = []
    for todo in todos:
        checked_hex = find_hex(todo)
        if checked_hex is not None: # ignoring adhoc todolists without hashes
            hex_string = checked_hex['hex']
            checked_hashes.append(hex_string)
    return checked_hashes


def find_line_with_hash(lines, hex_id):
    """
    given a hex id, return the line number and the line that contains that id.
    """
    for line_id, line in enumerate(lines):
        if hex_id in line: 
            return (line_id, line)

    return None

def check_off_line(line):
    """
    Return a version of the line where the box is checked off.
    """
    for idx, element in enumerate(config.CHECKLIST_UNCHECKED_MARKERS):
        checkbox_idx = line.find(element)
        if checkbox_idx != -1:
            return line [:checkbox_idx] + config.CHECKLIST_CHECKED_MARKERS[idx] \
                    + line[checkbox_idx + len(config.CHECKLIST_UNCHECKED_MARKERS[idx]) : ]
    
    for idx, element in enumerate(config.CHECKLIST_CHECKED_MARKERS):
        checkbox_idx = line.find(element)
        if checkbox_idx != -1:
            return line # this line was already checked
    
    return None

def check_off_original_notes(fpath, hex_ids):
    """
    within a single note file, check off ever box corresponding to a list of 
    hex_ids. Return true upon success, false otherwise.
    """
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
    """
    Return the current date as a string mm/dd/yy
    """
    date = datetime.now().date()
    return str(date.month)+'/'+ str(date.day)+'/'+str(date.year)[-2:]

def find_datestring_in_lines(lines, ds):
    """
    return the line within a list of lines that contains the date string ds.
    Returning a line number where it is first found.
    """
    for l_nb, line in enumerate(lines):
        if ''.join(line.strip().split()) == ds:
            return l_nb
    return None 

def find_all_datetimes_mmddyy_in_lines(lines): 
    datetimes_lnb =[]
    for line_idx, line in enumerate(lines):
        try:
            datetime_mmddyy = mmddyy2datetime(line)
            datetimes_lnb.append((datetime_mmddyy, line_idx))
        except ValueError:
            continue
    return datetimes_lnb

def find_todoheader_in_lines(lines):
    """
    Finding the line_number 
    """
    return find_datestring_in_lines(lines, '#TODO')

def todoline_formatter(note2newtodos_w_hashes):
    """
    Given a list of new_todos discovered across notes, return a set of formatted todo items. 
    """
    write_todos = []
    if len(note2newtodos_w_hashes):
        for note in note2newtodos_w_hashes:
            for todo_hex in note2newtodos_w_hashes[note]:
                write_todos.append ("%s {%s} (in `%s`)"%(todo_hex[0], todo_hex[1], note))
        write_todos = [element+'\n' for element in write_todos]
    
    return write_todos 
 
def write_to_todo(note2newtodos_w_hashes):
    """
    writing to the todolist for a list of new todolist items.
    """
    assert type(note2newtodos_w_hashes) is dict
    ds =get_date_string()
    # loading current todo
    with open(config.TODOLIST_NAME, 'r') as f:
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
    with open(config.TODOLIST_NAME, 'w') as f:
        f.writelines(new_todolist)

def write_hashes_on_new_todos(note2newtodos_w_hashes):
    """
    for every single note containing a new todo item, insert the hex id at the
    end of the line containing the new todo.
    """
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
    """
    returning the modification date of a file as a datetime object
    """
    t = os.path.getmtime(filepath)
    return datetime.fromtimestamp(t)

def has_new_modification(filepath, path2modtime):
    """
    returns true when the file in filepath has just been changed.
    """
    if filepath not in path2modtime:
        return True
    else:
        mdate = get_modification_date(filepath)
        assert type(path2modtime[filepath]) is datetime
        return mdate > path2modtime[filepath]


