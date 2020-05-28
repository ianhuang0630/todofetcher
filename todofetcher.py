"""
Script for fetching for a todolist item
"""
import sys
from utils import * 
import config
from datetime import datetime, timedelta
from termcolor import colored 
import time
import argparse

def get_priorities(todo2datedur):
    today = datetime.now().date()
    todo2priority= {}
    for todo in todo2datedur:
        diff = today - todo2datedur[todo]['assign_date'].date()
        todo2priority[todo] = diff.days
    
    return todo2priority
     

def find_total_duration(l):
    durations = [element['times']['duration'] for element in l]
    sum_ = timedelta(minutes=0) 
    for d in durations:
        sum_ += d

    return sum_

def find_feasible_todos(duration, t2d):
    
    feasible_todos = [t for t in t2d if t2d[t]['duration']<= duration]
    return feasible_todos             

def pick_by_priority(todos, t2p):
    # find the one with the max priority
    max_prio = -1
    best_todo = None
    for t in todos: 
        if max(t2p[t], 0) > max_prio:
            max_prio = t2p[t]
            best_todo = t
    return best_todo

    
def get_feasible_set(todo2datedur, todo2priority, budget_datetime):
    todo2d = todo2datedur.copy() 
    todo2p = todo2priority.copy()
    
    feasible_list = []
    todo2d_new = {}
    todo2p_new = {}
    # in search of high priority above the threshold
    for key in todo2d: 
        assert key in todo2p 
        priority = todo2p[key]
        if priority > config.PRIORITY_THRESHOLD:
            feasible_list.append({'todo_item':key,
                                'times': todo2d[key],
                                'priority': todo2p[key]} )
        else:
            todo2d_new[key] = todo2d[key]
            todo2p_new[key] = todo2p[key]

    todo2d = todo2d_new
    todo2p = todo2p_new 
    
    total_duration = find_total_duration(feasible_list) 
    if total_duration > budget_datetime:
        print(colored('Found {} todos w/ priorities higher than threshold, total duration {}. Adding these to your list'.format(len(feasible_list), str(total_duration)), 'red'))
        return feasible_list
    
    ## Selecting for remaining time
    remaining_duration = budget_datetime - total_duration
    
    while True:
        next_task_options = find_feasible_todos(remaining_duration, todo2d)
        if len(next_task_options) == 0: 
            break
        next_task = pick_by_priority(next_task_options, todo2p)
        
        next_times = todo2d.pop(next_task)
        feasible_list.append({'todo_item': next_task, 
                            'times': next_times, 
                            'priority': todo2p.pop(next_task)})
        
        total_duration += next_times ['duration'] 
        remaining_duration -= next_times ['duration']
    
    return feasible_list 

class CountDown(object):
    def __init__(self, starting_time):
        self.starting_time = starting_time
        self.current_time = starting_time 
        self.decrement_interval = 600
        self.return_time = timedelta(seconds=0) 
    
    def start(self):
        while self.current_time > self.return_time:
            try:
                # tic = time.time()
                sys.stdout.write('\r{}'.format(colored(str(self.current_time), 'red')))
                sys.stdout.flush()
                time.sleep(1)
                # toc = time.time()
                self.current_time -= timedelta(seconds=1) 

            except KeyboardInterrupt:
                print("""
Time out. 
Options:
1) Add more time [a]
2) Check off item [c]
3) Continue [n]
4) Cancel [x]
                """)
                options = input()
                if options.lower().strip() == 'a':
                    print ("how much more time?")
                    while True:
                        try:
                            time_str = input()
                            extratime = duration2datetime(time_str)                
                            self.current_time += extratime
                            break 
                        except:
                            print('Invalid. Try again.')
                elif options.lower().strip() == 'c':
                    return {'status': 'complete',
                            'remaining_time': self.current_time}
                elif options.lower().strip() == 'n':
                    pass 
                elif options.lower().strip() == 'x':
                    return {'status': 'term'}
        
        return {'status': 'out-of-time'}

class TodoFetcher(object):
    def __init__(self, todolist):
        self.todolist = todolist

    def wait_for_commitment(self):
        print('Ready to be productive? [Y/n]')
        yon=input()
        
        if yon == 'y' or yon == 'Y':
            self.start()
        else:
            print('Exiting.')
    
    def start(self):
        for todo in self.todolist:
            todo_str= todo['todo_item']
            print(colored(todo_str, 'green'))
            cd=CountDown(todo['times']['duration'])
            exit_status = cd.start()
            if exit_status['status'] == 'complete':
                assert check_off_original_todo(todo['todo_item'])
            if exit_status['status'] == 'out-of-time':
                print('You ran out of time!') 
            print(exit_status)
        return todo 

if __name__=="__main__":
    print ('starting todo fetch')
    
    # read the time in from commandline
    if len(sys.argv) < 2:
        raise ValueError('Need to specify some amount of time')
    
    # get the total amount of time alotted for session
    
    option = sys.argv[1]
    
    if option == '-s' or option == '-k':
        todo2date = unchecked_by_date()
        if option == '-s':
            substring = ' '.join(sys.argv[2:])
            # looking for valid todo
            target_todo2date = [element for element in todo2date if substring in element[0].lower()]
        else:
            keywords = sys.argv[2:]
            target_todo2date = [element for element in todo2date if all([kw in element[0].lower() for kw in keywords])]
        
        if len(target_todo2date) < 1:
            if option == '-s':
                raise ValueError('substring does not exist among unchecked items in the todolist')
            elif option == '-k':
                raise ValueError('keyword(s) do not exist among unchecked items in the todolist')
        
        # get the duration
        todo2datedur = {element[0]:{'assign_date': element[1], 'duration':duration2datetime(find_duration(element[0]))} for element in target_todo2date}
        todo2priority = {element[0]: 0 for element in target_todo2date}
        todo2timedur = [{'times': {'duration': todo2datedur[element[0]]['duration']}} for i, element in enumerate(target_todo2date)]
        total_dur = find_total_duration(todo2timedur)
        
        feasible_set = get_feasible_set(todo2datedur, todo2priority, total_dur) 
        
        # these priorities are exponential to the date they are issued to the current date today.
         
        # display the todolist items, and start timing. Await for all items to be checked.
        # users have three options: either cancel, request more time, or check off current item.
        print(colored('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@', 'cyan'))
        for element in feasible_set:
            print(colored(element['todo_item'], 'yellow'))
        
        TF = TodoFetcher(feasible_set) 
        TF.wait_for_commitment()

    elif option == '-t':
        budget_time = sys.argv[2:]
        budget_datetime = durationlist2datetime(budget_time)
        
        todo2date = unchecked_by_date()
        expected_durations = []
        for todo in todo2date:
            duration = find_duration(todo[0])
            if duration is None:
                print('{} does not have an interpretable duration, will be replacing with default for this run.'.format(todo[0]))
                todo_default_time= add_placeholder_duration(todo[0])                        
                print('interpreted as: {}'.format(todo_default_time)) 
                duration = find_duration(todo_default_time)
            expected_durations.append(duration)

        assert len(todo2date) == len(expected_durations)
        expected_durations = [duration2datetime(dur) for dur in expected_durations]
        
        todo2datedur = {}
        for i in range(len(expected_durations)):
            todo2datedur[todo2date[i][0]] = {'assign_date': todo2date[i][1],
                                                'duration': expected_durations[i]}

        # iterate through list of items, giving them different priorities.
        todo2priority = get_priorities(todo2datedur)
        feasible_set = get_feasible_set(todo2datedur, todo2priority, budget_datetime) 
        
        # these priorities are exponential to the date they are issued to the current date today.
         
        # display the todolist items, and start timing. Await for all items to be checked.
        # users have three options: either cancel, request more time, or check off current item.
        print(colored('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@', 'cyan'))
        for element in feasible_set:
            print(colored(element['todo_item'], 'yellow'))
        
        TF = TodoFetcher(feasible_set) 
        TF.wait_for_commitment()
    else:
        raise ValueError('Invalid flag.')
