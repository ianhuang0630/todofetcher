# Todofetcher
You're taking notes of a lecture, and suddenly an idea or todo item pops into your head. You want to jot it down, but -- dammit -- you have to open up the Todoist or your .txt file to do that. You open it up, but what do you write? You want to recored the most amount of information possible about the thought you're having, or the todo item in a few words -- meanwhile the lecture is progressing, and you've just missed the proof of the last theorem!

You get back home, and you're ready to be productive -- for 2 hours and 30 minutes -- before that date you've got set up. You open your todolist, and it's a long list of things, and a disorganized jungle of checked and unchecked boxes. What tasks should you focus on for the next 2 hours and 30 minutes to get the most done??

## If this sounds like you ...

If you use hierarchies of folders to keep track of your notes, and use text editing tools like vim and emacs, Todofetcher is meant to help you with both of those problems. It:
1. fetches all available new todo items from your available notes into a central todolist file specified in `config.py`. Details about which note it's from will also be included, so that you can always go back to that note and traceback your thoughts. When you check things off in the central todolist file, it will also sync up with the original todo item in the notes.  
2. fetches all undone todolist items from the central todolist file that can fit into a user-provided time interval. It also will start timing you and holding you to your dedicated time per task (specified when you originally wrote down the todolist item.)

Run `python todolist.py` to sync across your notes. 

Run `python todofetcher.py -t [time]` to get a list of todolist items that are feasible within the time that you give it. `[time]` should be in the form `# h # m`, `# h` or `# m`. Note the space.

If you already have a sense of what you want to do, just run: `python todofetcher.py -s [substring of unchecked todo]` or `python todofetcher.py -k [keywords] [of] [todo]`

## If you're using vim...
If you're using vim, then there's a good way to not have to close the file while running these programs are making changes to the file. In your `.vimrc`, make sure the following lines are somewhere in there.

```
set autoread
set updatetime=750
au CursorHold * checktime
```

